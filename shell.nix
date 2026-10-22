let
  sources = import ./npins;
in
  {pkgs ? import sources.nixpkgs {}}:
    pkgs.mkShell {
      packages = with pkgs; [
        python314
        python314Packages.requests
        python314Packages.setuptools

        git
        alejandra
      ];
    }
