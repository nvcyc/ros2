#!/usr/bin/env python3
"""Wrapper script for colcon build and test operations."""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def find_repo_root():
    """Find the repository root by looking for .git or pixi.toml.

    Returns:
        Path to repository root, or None if not found
    """
    current = Path(__file__).parent.absolute()

    # Walk up the directory tree
    for parent in [current] + list(current.parents):
        # Check for .git directory first
        if (parent / '.git').exists():
            return parent
        # Then check for pixi.toml
        if (parent / 'pixi.toml').exists():
            return parent

    return None


def load_env_file(repo_root):
    """Load environment variables from .env file if it exists.

    Args:
        repo_root: Path to the repository root directory
    """
    env_file = repo_root / '.env'
    if not env_file.exists():
        return

    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            # Parse KEY=VALUE format
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                os.environ[key] = value


def colcon_command(command, packages, parallel_workers, tests_to_run=None):
    """Construct a colcon invocation without going through a shell."""
    if command == 'build':
        cmd = ['colcon', 'build', '--symlink-install',
               '--ament-cmake-args', '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON']
        selection = '--packages-up-to'
    else:
        cmd = ['colcon', 'test', '--return-code-on-test-failure',
               '--event-handlers', 'console_cohesion+']
        selection = '--packages-up-to' if command == 'test-up-to' else '--packages-select'
    if packages:
        cmd.extend([selection, *packages])
    if parallel_workers:
        cmd.extend(['--parallel-workers', parallel_workers])
    if tests_to_run:
        cmd.extend(['--ctest-args', '-R', tests_to_run])
    return cmd


def main():
    """Build or test any number of packages; no package names means all."""
    repo_root = find_repo_root()
    if repo_root:
        load_env_file(repo_root)

    parser = argparse.ArgumentParser(description='Wrapper for colcon operations')
    parser.add_argument('command', choices=['build', 'test', 'test-up-to', 'compile-commands'])
    parser.add_argument('packages', nargs='*', help='Package names (empty means all)')
    parser.add_argument('--tests-to-run', help='CTest name regex (test commands only)')
    parser.add_argument('--build-first', action='store_true',
                        help='Build selected packages and dependencies before testing')
    args = parser.parse_intermixed_args()
    testing = args.command in ('test', 'test-up-to')
    if not testing and (args.tests_to_run is not None or args.build_first):
        parser.error('--tests-to-run and --build-first require a test command')

    parallel_workers = os.environ.get('PIXI_PARALLEL_WORKERS', '')
    if parallel_workers:
        os.environ['CMAKE_BUILD_PARALLEL_LEVEL'] = parallel_workers
        os.environ['MAKEFLAGS'] = f'-j{parallel_workers}'

    try:
        if args.build_first or args.command == 'compile-commands':
            result = subprocess.run(
                colcon_command('build', args.packages, parallel_workers), check=False)
            if result.returncode:
                return result.returncode

        if args.command == 'compile-commands':
            with open('compile_commands.json', 'w') as output:
                return subprocess.run(
                    ['compdb', '-p', 'build', 'list'], stdout=output, check=False).returncode

        result = subprocess.run(
            colcon_command(args.command, args.packages, parallel_workers, args.tests_to_run),
            check=False)
        if testing:
            # Show results even after failures. Preserve the test invocation's status;
            # the workspace summary can also contain older results from other packages.
            subprocess.run(['colcon', 'test-result', '--verbose'], check=False)
        return result.returncode
    except OSError as exc:
        print(f"Error executing colcon {args.command}: {exc}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
