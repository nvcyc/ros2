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


def main():
    """Main entry point for the colcon wrapper."""
    # Load environment variables from .env file if it exists
    repo_root = find_repo_root()
    if repo_root:
        load_env_file(repo_root)

    parser = argparse.ArgumentParser(description='Wrapper for colcon operations')
    parser.add_argument('command', choices=['build', 'test', 'test-up-to'],
                        help='Colcon command to run')
    parser.add_argument('packages', nargs='*',
                        help='Package name(s) to build or test (empty means all)')
    parser.add_argument('--tests-to-run', type=str,
                        help='Regex pattern to select specific tests within packages (for test commands)')

    args = parser.parse_args()

    # Map wrapper commands to colcon commands and package selection modes
    command_config = {
        'build': {
            'colcon_cmd': 'build',
            'package_arg': 'packages-up-to',
            'extra_args': ['--symlink-install',
                          '--ament-cmake-args', '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON']
        },
        'test': {
            'colcon_cmd': 'test',
            'package_arg': 'packages-select',
            'extra_args': ['--event-handlers', 'console_cohesion+']
        },
        'test-up-to': {
            'colcon_cmd': 'test',
            'package_arg': 'packages-up-to',
            'extra_args': ['--event-handlers', 'console_cohesion+']
        }
    }

    config = command_config[args.command]

    # Setup parallel workers environment variables
    parallel_workers = os.environ.get('PIXI_PARALLEL_WORKERS', '')
    if parallel_workers:
        os.environ['CMAKE_BUILD_PARALLEL_LEVEL'] = parallel_workers
        os.environ['MAKEFLAGS'] = f'-j{parallel_workers}'

    # Build the colcon command
    cmd = ['colcon', config['colcon_cmd']]

    # Add extra arguments (build options or test event handlers)
    cmd.extend(config['extra_args'])

    # Add package selection if packages specified
    if args.packages:
        cmd.extend([f"--{config['package_arg']}"] + args.packages)

    # Add test selection if specified (for test commands only)
    if args.tests_to_run and args.command in ['test', 'test-up-to']:
        cmd.extend(['--ctest-args', '-R', args.tests_to_run])

    # Add parallel workers to colcon
    if parallel_workers:
        cmd.extend(['--parallel-workers', parallel_workers])

    # Execute the command
    try:
        result = subprocess.run(cmd, check=False)
        sys.exit(result.returncode)
    except Exception as e:
        print(f"Error executing colcon {args.command}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
