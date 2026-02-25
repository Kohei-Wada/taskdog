#!/usr/bin/env python3
"""Bump version across all packages in the monorepo.

Usage:
    python scripts/bump_version.py --current       # Show current version
    python scripts/bump_version.py 0.8.0 --dry-run # Preview changes
    python scripts/bump_version.py 0.8.0           # Update all versions
"""

import argparse
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent

VERSION_PATTERN = re.compile(r'^version\s*=\s*"(\d+\.\d+\.\d+)"', re.MULTILINE)
DEPENDENCY_PATTERN = re.compile(
    r"(taskdog-(?:core|client|server|ui|mcp))==(\d+\.\d+\.\d+)"
)
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


def discover_pyproject_files() -> list[Path]:
    """Dynamically discover all pyproject.toml files in the monorepo."""
    files = [ROOT_DIR / "pyproject.toml"]
    packages_dir = ROOT_DIR / "packages"
    if packages_dir.exists():
        for pkg_dir in sorted(packages_dir.iterdir()):
            pyproject = pkg_dir / "pyproject.toml"
            if pyproject.exists():
                files.append(pyproject)
    return files


def get_current_version() -> str:
    """Get current version from root pyproject.toml."""
    root_pyproject = ROOT_DIR / "pyproject.toml"
    with open(root_pyproject, "rb") as f:
        data = tomllib.load(f)
    return data["project"]["version"]


def validate_version(version: str) -> bool:
    """Validate semantic version format (X.Y.Z)."""
    return SEMVER_PATTERN.match(version) is not None


def update_pyproject_file(filepath: Path, new_version: str, dry_run: bool) -> list[str]:
    """Update version in a single pyproject.toml file.

    Returns list of changes made.
    """
    changes = []
    content = filepath.read_text()
    original_content = content

    # Update version = "X.Y.Z"
    def replace_version(match: re.Match[str]) -> str:
        old_version = match.group(1)
        if old_version != new_version:
            changes.append(f"  version: {old_version} -> {new_version}")
        return f'version = "{new_version}"'

    content = VERSION_PATTERN.sub(replace_version, content)

    # Update taskdog-*==X.Y.Z dependencies
    def replace_dependency(match: re.Match[str]) -> str:
        pkg_name = match.group(1)
        old_version = match.group(2)
        if old_version != new_version:
            changes.append(f"  {pkg_name}: {old_version} -> {new_version}")
        return f"{pkg_name}=={new_version}"

    content = DEPENDENCY_PATTERN.sub(replace_dependency, content)

    if content != original_content and not dry_run:
        filepath.write_text(content)

    return changes


def verify_no_old_versions(old_version: str) -> list[str]:
    """Verify no old version references remain after update.

    Returns list of files with remaining old version references.
    """
    problems = []

    for filepath in discover_pyproject_files():
        content = filepath.read_text()
        relative_path = filepath.relative_to(ROOT_DIR)

        # Check for old version in version field
        if f'version = "{old_version}"' in content:
            problems.append(f'{relative_path}: version = "{old_version}" still present')

        # Check for old version in dependencies
        old_dep_matches = re.findall(rf"taskdog-\w+=={re.escape(old_version)}", content)
        for match in old_dep_matches:
            problems.append(f"{relative_path}: {match} still present")

    return problems


def bump_version(new_version: str, dry_run: bool) -> int:
    """Bump version across all packages."""
    if not validate_version(new_version):
        print(f"Error: Invalid version format '{new_version}'. Expected X.Y.Z")
        return 1

    current = get_current_version()
    print(f"Current version: {current}")
    print(f"New version: {new_version}")
    print()

    pyproject_files = discover_pyproject_files()

    print(f"Found {len(pyproject_files)} pyproject.toml files:")
    for f in pyproject_files:
        print(f"  - {f.relative_to(ROOT_DIR)}")
    print()

    if dry_run:
        print("[DRY RUN] Changes that would be made:")
    else:
        print("Updating versions...")
    print()

    total_changes = 0

    for filepath in pyproject_files:
        relative_path = filepath.relative_to(ROOT_DIR)
        changes = update_pyproject_file(filepath, new_version, dry_run)

        if changes:
            print(f"{relative_path}:")
            for change in changes:
                print(change)
            print()
            total_changes += len(changes)

    if total_changes == 0:
        print("No changes needed - already at target version.")
    elif dry_run:
        print(f"Would update {total_changes} version references.")
    else:
        print(f"Updated {total_changes} version references.")

        # Verify no old versions remain
        if current != new_version:
            print()
            print("Verifying update...")
            problems = verify_no_old_versions(current)
            if problems:
                print("ERROR: Old version references still found:")
                for problem in problems:
                    print(f"  - {problem}")
                return 1
            print("Verification passed - no old version references found.")

        # Sync uv.lock with updated pyproject.toml versions
        print()
        print("Syncing uv.lock...")
        result = subprocess.run(
            ["uv", "lock"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"ERROR: uv lock failed:\n{result.stderr}")
            return 1
        print("uv.lock updated.")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bump version across all packages in the monorepo"
    )
    parser.add_argument(
        "version",
        nargs="?",
        help="New version (e.g., 0.8.0)",
    )
    parser.add_argument(
        "--current",
        action="store_true",
        help="Show current version and exit",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes",
    )

    args = parser.parse_args()

    if args.current:
        print(get_current_version())
        return 0

    if not args.version:
        parser.error("version is required (or use --current to show current version)")

    return bump_version(args.version, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
