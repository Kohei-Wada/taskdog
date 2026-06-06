# AUR package (`taskdog`)

A `PKGBUILD` for installing taskdog on Arch Linux via `pacman`/`yay`
(`yay -S taskdog`), as an alternative to `make install` (which uses
`uv tool install` into `~/.local`).

## What it does

- Builds a relocatable, self-contained virtualenv on the system Python and
  ships it under `/usr/lib/taskdog`.
- Exposes the three entry points in `/usr/bin`: `taskdog`, `taskdog-server`,
  `taskdog-mcp`.
- Installs the systemd **user** service to `/usr/lib/systemd/user/`
  (enable per-user with `systemctl --user enable --now taskdog-server`).
- Precompiles bytecode (`compileall --invalidation-mode unchecked-hash`) so the
  read-only `/usr` install never recompiles at runtime.

This is the **venv-bundled** approach: taskdog's five packages are built from
the release tarball, third-party deps come from PyPI at build time, and
everything is vendored into the package. It is non-idiomatic for the AUR
(the official-repo route would package each `python-*` dependency natively),
but self-contained and low-maintenance — the same approach taken by
`aider-chat-venv` and `paperless-ngx-venv`.

## Build & install

```bash
cd contrib/aur
makepkg -si          # build and install
```

Data lives per-user in `$XDG_DATA_HOME/taskdog/` (default
`~/.local/share/taskdog/`); the package never touches it.

## Updating (automated)

The package is published on the AUR and refreshed automatically: the `Release`
workflow (`.github/workflows/release.yml`) has a `publish-aur` job that, on every
`v*` tag, rewrites `pkgver`/`sha256sums` from the tagged release tarball,
regenerates `.SRCINFO`, and pushes to `ssh://aur@aur.archlinux.org/taskdog.git`.

This in-repo `PKGBUILD` is the source the CI pushes from; the `pkgver`/`sha256sums`
values here are a snapshot and are overwritten by CI from the tag, so they do not
need to be kept current by hand.

To update by hand instead, bump `pkgver`, run `makepkg -g` to refresh
`sha256sums`, then `makepkg -si`.

## Caveats

- `arch=('x86_64')` because the bundled wheels (e.g. `pydantic-core`) are
  platform-specific.
- The venv is built against the system Python, so a major Python upgrade
  (e.g. 3.14 → 3.15) requires a rebuild.
- Build downloads third-party deps from PyPI, which is outside `makepkg`'s
  source control — fine for personal/AUR use, not for the official repos.

## CI setup (one-time)

The `publish-aur` job needs an SSH key authorized to push to the AUR package:

1. Create an AUR account and add its SSH **public** key (My Account → SSH Public
   Key). Use a dedicated key, not a personal one.
2. Register the matching **private** key as the GitHub Actions secret
   `AUR_SSH_PRIVATE_KEY` (`gh secret set AUR_SSH_PRIVATE_KEY < ~/.ssh/aur`).
3. The AUR package must already exist — CI only updates it. The initial import
   (push of `PKGBUILD` + `.SRCINFO` to a fresh `taskdog.git`) is a manual step
   done once by the maintainer.
