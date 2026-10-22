{
  pkgs,
  lib,
  npins,
  nix,
  nixos-rebuild-ng,
  git,
  alejandra,
  setuptools ? pkgs.python3Packages.setuptools,
  requests ? pkgs.python3Packages.requests,
}:
pkgs.python3Packages.buildPythonApplication {
  pname = "nixupdate";
  version = "1.0.0";
  pyproject = true;

  build-system = [
    setuptools
  ];

  propagatedBuildInputs = [
    requests
  ];

  src = ./.;

  postPatch = ''
    substituteInPlace src/nixupdate/__init__.py src/nixupdate/phases.py \
      --replace-fail \"alejandra\" \"${lib.getExe alejandra}\" \
      --replace-fail \"git\" \"${lib.getExe git}\" \
      --replace-fail \"nix-env\" \"${lib.getExe' nix "nix-env"}\" \
      --replace-fail \"nixos-rebuild\" \"${lib.getExe nixos-rebuild-ng}\" \
      --replace-fail \"npins\" \"${lib.getExe npins}\"
  '';
}
