let
  sources = import ./npins;
in
  {
    system ? builtins.currentSystem,
    pkgs ? import sources.nixpkgs {inherit system;},
  }: rec {
    packages.${system} = rec {
      default = nixupdate;
      nixupdate = pkgs.callPackage ./package.nix {};
    };

    overlays.default = final: prev: {
      nixupdate = packages.${system}.nixupdate;
    };

    devShells.${system}.default = import ./shell.nix {inherit pkgs;};
  }
