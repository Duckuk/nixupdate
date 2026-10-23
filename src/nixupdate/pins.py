import json
import re
import requests

from nixupdate.color_codes import *

def load_pins() -> dict[str, dict]:
    try:
        with open("npins/sources.json", buffering=128*1024) as f:
            return json.load(f)["pins"]
    except Exception as e:
        print(f"{RED}Error: Failed to load npins sources.json: {e}{RESET}")
        exit(1)


def check_pin(name: str, pin: dict, quick_channel: bool = False) -> tuple[str, str, str] | None:
    """
    Returns a tuple in the format (name, old_revision, new_revision) if the given pin has an update available, otherwise returns None
    Supports GitHub and Channel types
    (pin_name, old_revision, remote_revision)
    """

    PLACEHOLDER = (name, "nil", "nil")

    if pin.get("frozen") is True:
        return None
    
    pin_type: str | None = pin.get("type")
    if pin_type is None:
        print(f"{YELLOW}Warning: pin '{name}' does not have a type, skipping.{RESET}")
        return None
    
    pin_repo = pin.get("repository", {})

    if pin_type == "Git" and pin_repo.get("type") == "GitHub":
        owner, repo, branch = pin_repo["owner"], pin_repo["repo"], pin["branch"]

        req = requests.get(f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}")

        if req.headers.get("x-ratelimit-remaining") == "0":
            print(f"{YELLOW}Warning: github rate limit reached, cannot check for updates.")
            return None
        
        old_revision: str = pin["revision"]
        new_revision: str = req.json()["commit"]["sha"]

        if new_revision != old_revision:
            return (name, old_revision, new_revision)
    
    elif pin_type == "Channel" and quick_channel is False:
        channel: str = pin["name"]

        git_commit_in_releases_page = re.compile(r"Git commit\s*<tt>(\w+)</tt>")

        old_url = pin["url"][:pin["url"].rfind('/')]
        # pyrefly: ignore[unsupported-operation]
        old_revision = re.search(
            git_commit_in_releases_page,
            requests.get(old_url).text
            )[1]
        # pyrefly: ignore[unsupported-operation]
        new_revision = re.search(
            git_commit_in_releases_page,
            requests.get(f"https://channels.nixos.org/{channel}").text
            )[1]

        if new_revision != old_revision:
            return (name, old_revision, new_revision)
    
    elif pin_type == "Channel" and quick_channel is True:
        channel: str = pin["name"]

        git_commit_in_releases_page = re.compile(r"Git commit\s*<tt>(\w+)</tt>")

        old_url = pin["url"][:pin["url"].rfind('/')]
        new_url = requests.get(f"https://channels.nixos.org/{channel}", allow_redirects=False).headers["location"]

        if new_url != old_url:
            return PLACEHOLDER
    
    else:
        print(f"{YELLOW}Warning: Unsupported pin '{name}' of type '{pin_type}'.{RESET}")

    return None


def update_check() -> list[tuple[str, str, str]]:
    """
    Returns a list of pins that need updates
    Supports whatever types check_pin does
    (pin_name, old_revision, remote_revision)
    """

    pins = load_pins()

    return [
        r
        for name, pin in pins.items()
        if isinstance(pin, dict)
        for r in [check_pin(name, pin)]
        if r is not None
    ]

def quick_update_check() -> bool:
    """
    Returns true if there's any pin that need updates
    Supports whatever types check_pin does
    """
    pins = load_pins()
    
    return any(
        isinstance(pin, dict) and check_pin(name, pin, True) is not None
        for name, pin in pins.items()
    )
