from pathlib import Path
from subprocess import run
import argparse
import atexit
import os
import shutil
import importlib.metadata

from nixupdate.color_codes import *
import nixupdate.phases as phases

stash_commit: str | None = None

def exit_handler() -> None:
    if stash_commit is not None:
        try:
            run(["git", "checkout", "--quiet", "."]).check_returncode()
            run(["git", "clean", "--quiet", "--force", "-d"]).check_returncode()
            run(["git", "stash", "apply", "--quiet", stash_commit]).check_returncode()
            print("Restored repo original state.")
        except Exception as e:
            print(f"{RED}Error: Failed to restore repo original state: {e}{RESET}")
            print(f"Your changes are stored in commit object '{YELLOW}{stash_commit}{RESET}'. Use something like `{YELLOW}git stash apply {stash_commit}{RESET}` to get your changes back.")


def sanity_check(args) -> None:
    if args.commit_message == "":
        print(f"{RED}Error: Commit message cannot be empty!{RESET}")
        exit(1)

    if not args.target.is_file():
        print(f"{RED}Error: '{args.target}' is not a file!{RESET}")
        exit(1)
    
    if run(["git", "rev-parse", "--is-inside-work-tree"], capture_output=True, cwd=args.target.parent).stdout.decode() == "false":
        print(f"{RED}Error: '{args.target.parent}' is not a valid git repository!{RESET}")
        exit(1)

def check_dependencies():
    deps = [
        "alejandra",
        "git",
        "nix-env",
        "nixos-rebuild",
        "npins",
        "sudo",
    ]

    missing_deps = [
        dep
        for dep in deps
        if shutil.which(dep) is None
    ]
    if missing_deps != []:
        print(f"{RED}Error: Missing runtime dependencies{RESET}")
        for dep in missing_deps:
            print(f"  {YELLOW}{dep}{RESET}")
        print(f"Please make sure these programs are in your PATH.")
        exit(1)


def main():
    global stash_commit

    parser = argparse.ArgumentParser(
        prog="nixupdate",
        description="Updates the NixOS system configuration using a system.nix.",
    )
    parser.add_argument("-V", "--version", action="store_true", help="Print version.")
    parser.add_argument("-n", "--no-update", action="store_true", help="Skip updating to newer nixpkgs.")
    parser.add_argument("-f", "--force", action="store_true", help="Build configuration even if there are no changes.")
    parser.add_argument("-b", "--boot", action="store_true", help="Switch configuration on next boot instead of immediately.")
    parser.add_argument("-t", "--target", default="/etc/nixos/system.nix", help="The `system.nix` configuration to build. Defaults to `/etc/nixos/system.nix`.")
    parser.add_argument("-c", "--commit-message", help="Make git commit with this message instead of generation info.")
    args = parser.parse_args()
    args.target = Path(args.target).resolve()

    if args.version:
        print(f"nixupdate {importlib.metadata.version("nixupdate")}")
        exit(0)

    check_dependencies()

    sanity_check(args)

    root_dir = run(["git", "rev-parse", "--show-toplevel"], capture_output=True, cwd=args.target.parent).stdout.decode().strip()
    os.chdir(Path(root_dir).resolve())

    #
    # Run diff phase
    #
    has_changed = phases.diff_phase()

    #
    # Save changes made by user in case we need to exit early
    #
    if has_changed:
        p = run(["git", "stash", "create"], capture_output=True)
        p.check_returncode()
        stash_commit = p.stdout.decode().strip()
    
    #
    # Register the exit handler so we can reverse any changes we make
    #
    atexit.register(exit_handler)

    #
    # Check for nixpkgs update
    #
    updates = phases.update_check_phase(args, has_changed)

    #
    # Apply updates if found
    #
    if updates:
        phases.update_phase(updates)

    #
    # Run alejandra to format code
    #
    phases.format_phase()
    
    #
    # Build the configuration
    #
    phases.build_phase(args)

    atexit.unregister(exit_handler)

    #
    # Push changes to git
    #
    phases.git_phase(args)

    #
    # Remove old generations
    #
    phases.clean_generations_phase()

    print(f"{GREEN}All done!{RESET}")

    return 0

if __name__ == "__main__":
    main()