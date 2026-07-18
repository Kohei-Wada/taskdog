{
  description = "Taskdog - individual task management (CLI/TUI + REST API), packaged with uv2nix";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      uv2nix,
      pyproject-nix,
      pyproject-build-systems,
      ...
    }:
    let
      inherit (nixpkgs) lib;

      # Load the uv workspace from the repo root (reads pyproject.toml + uv.lock).
      workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };

      # Overlay translating the uv.lock into a pyproject.nix package set.
      # Prefer wheels — fewer packages need to be compiled from source.
      overlay = workspace.mkPyprojectOverlay {
        sourcePreference = "wheel";
      };

      # Project-specific overrides. Empty for now; add entries here if a
      # dependency fails to build (e.g. missing native build inputs).
      pyprojectOverrides = _final: _prev: { };

      # Supported systems.
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "aarch64-darwin"
        "x86_64-darwin"
      ];
      forAllSystems = lib.genAttrs systems;

      pkgsFor = system: nixpkgs.legacyPackages.${system};

      # Match the project's pinned interpreter (.python-version = 3.13).
      pythonFor = system: (pkgsFor system).python313;

      # Fully-resolved python package set for a given system.
      pythonSetFor =
        system:
        let
          pkgs = pkgsFor system;
          python = pythonFor system;
        in
        (pkgs.callPackage pyproject-nix.build.packages {
          inherit python;
        }).overrideScope
          (
            lib.composeManyExtensions [
              pyproject-build-systems.overlays.default
              overlay
              pyprojectOverrides
            ]
          );

      # A virtualenv containing every workspace package + its runtime deps.
      # Tagged with meta so `nix profile install` and `nix run` behave nicely.
      venvFor =
        system:
        ((pythonSetFor system).mkVirtualEnv "taskdog-env" workspace.deps.default).overrideAttrs
          (old: {
            meta = (old.meta or { }) // {
              description = "Taskdog - individual task management (CLI/TUI + REST API)";
              homepage = "https://github.com/Kohei-Wada/taskdog";
              license = lib.licenses.mit;
              mainProgram = "taskdog";
              platforms = systems;
            };
          });
    in
    {
      # `nix build` / `nix build .#taskdog` -> a venv exposing the CLI, server, MCP.
      # Install with: nix profile install github:Kohei-Wada/taskdog
      packages = forAllSystems (
        system:
        let
          venv = venvFor system;
        in
        {
          default = venv;
          taskdog = venv;
        }
      );

      # `nix run .#taskdog` (CLI/TUI), `.#taskdog-server`, `.#taskdog-mcp`.
      apps = forAllSystems (
        system:
        let
          venv = venvFor system;
        in
        {
          default = self.apps.${system}.taskdog;
          taskdog = {
            type = "app";
            program = "${venv}/bin/taskdog";
          };
          taskdog-server = {
            type = "app";
            program = "${venv}/bin/taskdog-server";
          };
          taskdog-mcp = {
            type = "app";
            program = "${venv}/bin/taskdog-mcp";
          };
        }
      );

      # Dev shells.
      devShells = forAllSystems (
        system:
        let
          pkgs = pkgsFor system;
          python = pythonFor system;
        in
        {
          # Impure shell: uses uv directly to manage the .venv (editable installs,
          # matches the Makefile workflow). Run `uv sync` inside, then `make test`.
          default = pkgs.mkShell {
            packages = [
              python
              pkgs.uv
            ];
            env = {
              # Force uv to use the nixpkgs interpreter, never download one.
              UV_PYTHON_DOWNLOADS = "never";
              UV_PYTHON = python.interpreter;
            };
            shellHook = ''
              unset PYTHONPATH
            '';
          };

          # Pure shell: the fully Nix-built venv on PATH, no uv/network needed.
          pure = pkgs.mkShell {
            packages = [ (venvFor system) ];
          };
        }
      );
    };
}
