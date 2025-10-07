{
  description = "fastapi-libvirt dev shell";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        py = pkgs.python312;
      in {
        devShells.default = pkgs.mkShell {
          packages = [
            (py.withPackages (ps: [ ps.libvirt ps.python-dotenv ps.tabulate ps.uvicorn ps.fastapi ps.requests]))
            pkgs.libvirt
          ];
        };
      });
}
