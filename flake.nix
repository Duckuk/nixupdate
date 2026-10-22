{
  description = "Helper for updating NixOS configurations.";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs = {
    nixpkgs,
    flake-utils,
    ...
  }:
    flake-utils.lib.eachDefaultSystemPassThrough
    (system: (import ./default.nix {
      inherit system;
      pkgs = import nixpkgs {inherit system;};
    }));
}
