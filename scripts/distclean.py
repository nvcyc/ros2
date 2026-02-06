#!/usr/bin/env python3
"""Script to clean all build artifacts and source code, checking for unpushed changes."""

import shutil
import subprocess
import sys
from pathlib import Path


def check_git_unpushed(repo_path):
    """Check if a git repository has unpushed changes."""
    try:
        # Check if directory is a git repo
        result = subprocess.run(
            ['git', '-C', str(repo_path), 'rev-parse', '--git-dir'],
            capture_output=True,
            check=False
        )
        if result.returncode != 0:
            return False, "Not a git repository"

        # Check for uncommitted changes
        result = subprocess.run(
            ['git', '-C', str(repo_path), 'status', '--porcelain'],
            capture_output=True,
            text=True,
            check=True
        )
        if result.stdout.strip():
            return True, "Has uncommitted changes"

        # Check for unpushed commits
        result = subprocess.run(
            ['git', '-C', str(repo_path), 'log', '@{u}..', '--oneline'],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0 and result.stdout.strip():
            return True, "Has unpushed commits"

        return False, "Clean"
    except Exception as e:
        return None, f"Error checking: {e}"


def main():
    """Main entry point for distclean."""
    src_dir = Path('src')

    if not src_dir.exists():
        print("No src directory found, nothing to clean")
        return 0

    # Check all subdirectories for unpushed changes
    repos_with_changes = []

    for item in src_dir.iterdir():
        if not item.is_dir():
            continue

        # Check subdirectories (e.g., src/ros2/rcl)
        for subdir in item.rglob('*'):
            if not subdir.is_dir():
                continue

            git_dir = subdir / '.git'
            if git_dir.exists():
                has_changes, reason = check_git_unpushed(subdir)
                if has_changes:
                    repos_with_changes.append((subdir, reason))

    # If any repos have unpushed changes, refuse to proceed
    if repos_with_changes:
        print("ERROR: The following repositories have unpushed changes:", file=sys.stderr)
        for repo, reason in repos_with_changes:
            print(f"  {repo}: {reason}", file=sys.stderr)
        print("\nPlease push or stash changes before running distclean", file=sys.stderr)
        return 1

    # Run clean first
    print("Running clean task...")
    result = subprocess.run(['pixi', 'run', 'clean'], check=False)
    if result.returncode != 0:
        print("ERROR: clean task failed", file=sys.stderr)
        return result.returncode

    # Remove subfolders in src directory (keep src/.gitkeep)
    print("Removing subfolders in src directory...")
    for item in src_dir.iterdir():
        if item.is_dir():
            print(f"  Removing {item}")
            try:
                shutil.rmtree(item)
            except Exception as e:
                print(f"ERROR: Failed to remove {item}: {e}", file=sys.stderr)
                return 1

    print("Distclean completed successfully")
    return 0


if __name__ == '__main__':
    sys.exit(main())
