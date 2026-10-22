A helper tool for updating NixOS configurations. Not to be confused with [nix-update](https://github.com/Mic92/nix-update).

# Features

- Quick update checking
- Formats with Alejandra
- Builds NixOS configuration
- Commits changes to git for every generation built
- Cleans out old generations to save disk space

# Runtime dependencies

- [alejandra](https://alejandra.kamadorueda.com) >= 4.0.0
- [git](https://git-scm.com/) >= 2.55.0
- [npins](https://github.com/andir/npins) >= 0.5.1

# Usage

Run using the provided flake:

```bash
nix run github:Duckuk/nixupdate
```

# Arguments

```
-h, --help
    show help message and exit

-V, --version
    Print version and exit.

-n, --no-update
    Skip updating pins.

-f, --force
    Build configuration even if there are no changes.

-b, --boot
    Switch configuration on next boot instead of immediately.

-t, --target TARGET
    The `system.nix` configuration to build. Defaults to `/etc/nixos/system.nix`.

-c, --commit-message COMMIT_MESSAGE
    Make git commit with this message instead of generation info.
```

# Build

Nix is the only supported build system currently:

```bash
nix build github:Duckuk/nixupdate
./result/bin/nixupdate
```
