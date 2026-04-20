"""Main CLI for emake."""

import argparse
import sys

from emake import __version__

from .build import build_all, build_sdist, build_wheel, clean
from .config import get_project_config
from .lint import run_lint
from .test import run_tests
from .venv import get_venv
from .wheel import test_manylinux_wheel


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="emake",
        description="A Python module to replace Makefile workflows.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def add_requirements_parser(subparsers) -> argparse.ArgumentParser:
    """Add the requirements subcommand."""
    parser = subparsers.add_parser(
        "requirements",
        help="Create .venv and install dependencies",
    )
    parser.add_argument(
        "extras",
        nargs="*",
        help="Optional dependency groups to install (e.g., web test dev)",
    )
    return parser


def add_test_parser(subparsers) -> argparse.ArgumentParser:
    """Add the test subcommand."""
    parser = subparsers.add_parser(
        "test",
        help="Run tests (default: all tests in tests/)",
    )
    parser.add_argument(
        "--wheel",
        action="store_true",
        help="Test using Docker with a built wheel instead of local code",
    )
    parser.add_argument(
        "--arch",
        default="x86_64",
        help="Target architecture for wheel testing (default: x86_64)",
    )
    parser.add_argument(
        "--libc",
        default="glibc",
        choices=["glibc", "musl"],
        help="Target libc for wheel testing (default: glibc)",
    )
    parser.add_argument(
        "--python",
        default="3.11",
        help="Python version for wheel testing (default: 3.11)",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default="tests/",
        help="Path to test file or directory (default: tests/)",
    )
    return parser


def add_wheel_parser(subparsers) -> argparse.ArgumentParser:
    """Add the wheel subcommand."""
    parser = subparsers.add_parser(
        "wheel",
        help="Build wheel",
    )
    parser.add_argument(
        "--native",
        action="store_true",
        help="Build platform-specific wheel instead of pure Python wheel",
    )
    parser.add_argument(
        "--arch",
        default="x86_64",
        help="Target architecture for manylinux build (default: x86_64)",
    )
    parser.add_argument(
        "--libc",
        default="glibc",
        choices=["glibc", "musl"],
        help="Target libc for manylinux build (default: glibc)",
    )
    parser.add_argument(
        "--python",
        default="3.11",
        help="Python version for manylinux build (default: 3.11)",
    )
    return parser


def add_sdist_parser(subparsers) -> argparse.ArgumentParser:
    """Add the sdist subcommand."""
    return subparsers.add_parser(
        "sdist",
        help="Build source distribution",
    )


def add_build_parser(subparsers) -> argparse.ArgumentParser:
    """Add the build subcommand."""
    return subparsers.add_parser(
        "build",
        help="Build wheel and source distribution",
    )


def add_clean_parser(subparsers) -> argparse.ArgumentParser:
    """Add the clean subcommand."""
    return subparsers.add_parser(
        "clean",
        help="Remove build artifacts",
    )


def add_lint_parser(subparsers) -> argparse.ArgumentParser:
    """Add the lint subcommand."""
    parser = subparsers.add_parser(
        "lint",
        help="Run linting",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically fix issues where supported",
    )
    return parser


def validate_extras(config, extras: list[str]) -> list[str]:
    """Validate that extras are defined in pyproject.toml.

    Args:
        config: ProjectConfig instance.
        extras: List of extra names provided by user.

    Returns:
        List of validated extra names.

    Raises:
        ValueError: If an extra is not defined in pyproject.toml.
    """
    available = set(config.extras.keys())
    for extra in extras:
        if extra not in available:
            raise ValueError(
                f"Unknown extra '{extra}'. Available: {', '.join(sorted(available))}"
            )
    return extras


def cmd_requirements(args) -> int:
    """Handle the requirements command."""
    config = get_project_config()
    extras = validate_extras(config, args.extras) if args.extras else []

    venv = get_venv()
    venv.install(extras)
    return 0


def cmd_test(args) -> int:
    """Handle the test command."""
    if args.wheel:
        test_manylinux_wheel(None, arch=args.arch, libc=args.libc, python=args.python)
        return 0

    venv = get_venv()
    venv.ensure_test_tools()
    return run_tests(venv, args.path)


def cmd_wheel(args) -> int:
    """Handle the wheel command."""
    if args.native:
        # For native, we just need build tools but run in docker
        venv = get_venv()
        venv.ensure_build_tools()
    else:
        venv = get_venv()
        venv.ensure_build_tools()
    build_wheel(
        venv,
        native=args.native,
        arch=args.arch,
        libc=args.libc,
        python=args.python,
    )
    return 0


def cmd_sdist(args) -> int:
    """Handle the sdist command."""
    venv = get_venv()
    venv.ensure_build_tools()
    build_sdist(venv)
    return 0


def cmd_build(args) -> int:
    """Handle the build command."""
    venv = get_venv()
    venv.ensure_build_tools()
    build_all(venv)
    return 0


def cmd_clean(args) -> int:
    """Handle the clean command."""
    clean()
    return 0


def cmd_lint(args) -> int:
    """Handle the lint command."""
    venv = get_venv()
    venv.ensure_lint_tools()
    return run_lint(venv, fix=args.fix)


def main(argv: list[str] | None = None) -> int:
    """Main entry point for emake."""
    parser = create_parser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_requirements_parser(subparsers)
    add_test_parser(subparsers)
    add_wheel_parser(subparsers)
    add_sdist_parser(subparsers)
    add_build_parser(subparsers)
    add_clean_parser(subparsers)
    add_lint_parser(subparsers)

    args = parser.parse_args(argv)

    # Dispatch to command handler
    commands = {
        "requirements": cmd_requirements,
        "test": cmd_test,
        "wheel": cmd_wheel,
        "sdist": cmd_sdist,
        "build": cmd_build,
        "clean": cmd_clean,
        "lint": cmd_lint,
    }

    try:
        return commands[args.command](args)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
