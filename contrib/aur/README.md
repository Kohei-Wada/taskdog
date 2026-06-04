# AUR package (`taskdog-venv`)

A `PKGBUILD` for installing taskdog on Arch Linux via `pacman`/`yay`, as an
alternative to `make install` (which uses `uv tool install` into `~/.local`).

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
everything is vendored into the package. The `-venv` suffix and
`provides`/`conflicts=('taskdog')` follow the AUR convention used by packages
like `aider-chat-venv` and `paperless-ngx-venv`, reserving the plain `taskdog`
name for a future native (`python-*` dependency) package.

## Build & install

```bash
cd contrib/aur
makepkg -si          # build and install
```

Data lives per-user in `$XDG_DATA_HOME/taskdog/` (default
`~/.local/share/taskdog/`); the package never touches it.

## Updating

Bump `pkgver` (and run `makepkg -g` to refresh `sha256sums`), then
`makepkg -si` again.

## Caveats

- `arch=('x86_64')` because the bundled wheels (e.g. `pydantic-core`) are
  platform-specific.
- The venv is built against the system Python, so a major Python upgrade
  (e.g. 3.14 → 3.15) requires a rebuild.
- Build downloads third-party deps from PyPI, which is outside `makepkg`'s
  source control — fine for personal/AUR use, not for the official repos.

## Not published to the AUR yet

This `PKGBUILD` is kept in-repo for local builds. Publishing it as `taskdog-venv`
on aur.archlinux.org (so `yay -S taskdog-venv` works for everyone) requires an
AUR account + SSH key and is a separate manual step.
