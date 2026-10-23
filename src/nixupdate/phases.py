from nixupdate.pins import PinUpdate
import argparse
import re
from subprocess import run

from nixupdate.color_codes import *
import nixupdate.pins as pins

def _confirm_choice(prompt: str) -> bool:
    reply = input(prompt).lower()
    return reply == "y" or reply == "yes"

def diff_phase() -> bool:
    """
    Check for changes and seek user review if present
    Returns true if changes are present
    Exits early if user aborts
    """
    print(f"{YELLOW}Checking git diff...{RESET}")
    if run(["git", "diff", "--quiet", "HEAD", "--", "."]).returncode != 0:
        run(["git", "diff", "-U0", "HEAD", "--", ".", ":(exclude)npins"])

        if not _confirm_choice("If these changes look good, please confirm you want to proceed (y/n) "):
            print(f"{YELLOW}User aborted. Exiting...{RESET}")
            exit(0)
        print()
        return True
    else:
        print(f"{YELLOW}No changes found.{RESET}")
        print()
        return False

def update_check_phase(args: argparse.Namespace, diff_phase_result: bool) -> list[PinUpdate] | bool | None:
    """
    Checks npins pins for updates
    Returns list of pins that require updates if diff_phase_result is False, otherwise returns a boolean
    Returns None if args.no_update or args.force are True
    Exits early if no updates are found and diff_phase_result is False
    """
    print(f"{YELLOW}Checking for updates...{RESET}")

    if diff_phase_result is False and args.no_update and args.force is False:
        print(f"{YELLOW}No changes and updates skipped. Exiting...{RESET}")
        exit(0)
    
    if args.no_update:
        print("--no-update specified, skipping updates.")
        print()
        return None

    if args.force:
        print("--force specified, skipping update check.")
        print()
        return True
    
    #
    # Do thorough update check if no changes and present it for user review so they can decide whether to update or not
    #
    if diff_phase_result is False:
        pins_with_updates = pins.update_check()
        if pins_with_updates == []:
            print(f"{YELLOW}No changes and no updates available. Exiting...{RESET}")
            exit(0)
        
        print(f"No changes, but there may be pins that require updates:")
        for pin_update in pins_with_updates:
            print(f"{YELLOW}{pin_update.name}{RESET}")

            if pin_update.pin_type == "GitRelease":
                print(f"  old version: {RED}{pin_update.old}{RESET}")
                print(f"  new version: {GREEN}{pin_update.new}{RESET}")
            else:
                print(f"  old revision: {RED}{pin_update.old}{RESET}")
                print(f"  new revision: {GREEN}{pin_update.new}{RESET}")
        
        if not _confirm_choice("Please confirm you would like to proceed (y/n) "):
            print(f"{YELLOW}User aborted. Exiting...{RESET}")
            exit(0)
        
        return pins_with_updates
    
    #
    # Do quicker update check because the details are probably less relevant if the user has their own changes prepared
    #
    else:
        pins_require_updates = pins.quick_update_check()
        
        if pins_require_updates:
            print(f"{GREEN}Update(s) found!{RESET}")
            print()
            return True
        else:
            print(f"{YELLOW}No update(s) found.{RESET}")
            print()
            return False

def update_phase(updates: list[PinUpdate] | bool):
    """
    Runs npins update
    Exits early if npins fails
    """
    print(f"{YELLOW}Updating npins...{RESET}")
    if isinstance(updates, bool): 
        run(["npins", "update"]).check_returncode()
    else:
        pin_names = [e.name for e in updates]
        run(["npins", "update"] + pin_names).check_returncode()
    print(f"{GREEN}Finished updating npins!{RESET}")
    print()

def format_phase():
    """
    Runs alejandra to fomat nix code
    Exits early if alejandra fails
    """
    print(f"{YELLOW}Formatting...{RESET}")

    run(["alejandra", "."]).check_returncode()

    print(f"{GREEN}Finished formatting!{RESET}")
    print()

def build_phase(args: argparse.Namespace):
    """
    Builds the NixOS configuration
    Exits early if the build fails
    """
    print(f"{YELLOW}Building configuration...{RESET}")

    mode = "boot" if args.boot else "switch"
    if run(["sudo", "nixos-rebuild", mode, "--file", args.target]).returncode != 0:
        print(f"{RED}Failed to build configuration!{RESET}")
        exit(1)
    
    print(f"{GREEN}Finished building configuration!{RESET}")
    print()

def git_phase(args: argparse.Namespace):
    """
    Commits changes to git repo
    Exits early if git fails or secret files were accidentally committed
    """
    print(f"{YELLOW}Pushing changes to git...{RESET}")

    if run(["git", "status", "--porcelain"], capture_output=True).stdout.decode() == "":
        print(f"{YELLOW}No changes detected, skipping git commit.{RESET}")
        print()
        return
    
    run(["git", "add", "-A"]).check_returncode()

    if args.commit_message:
        commit_message = args.commit_message
    else:
        try:
            # pyrefly: ignore[missing-attribute]
            commit_message = re.search(r"^.*True$", run(["nixos-rebuild", "list-generations"], capture_output=True).stdout.decode(), re.MULTILINE).group()
            commit_message = re.sub(r" +", " ", commit_message)
        except Exception as e:
            print(f"{RED}Error: Failed to generate commit message from generation: {e}{RESET}")
            exit(1)
    
    #
    # Check that no secrets were committed
    #
    git_status_output = run(["git", "status", "--porcelain"], capture_output=True)
    if ".secret" in git_status_output.stdout.decode() or ".secret" in git_status_output.stderr.decode():
        print(f"{RED}Secret files staged, aborting git push!{RESET}")
        exit(1)

    run(["git", "commit", "-vvvv", "-m", commit_message]).check_returncode()
    run(["git", "push"]).check_returncode()

    print(f"{GREEN}Finished pushing changes!{RESET}")
    print()

def clean_generations_phase():
    """
    Cleans old NixOS generations
    Exits early if nix-env fails
    """
    print(f"{YELLOW}Removing old generations...{RESET}")

    run(["sudo", "nix-env", "--profile", "/nix/var/nix/profiles/system", "--delete-generations", "+5"]).check_returncode()

    print(f"{GREEN}Finished removing old generations!{RESET}")
    print()