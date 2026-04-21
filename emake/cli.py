"""Main CLI for emake."""

import argparse
import os
import sys

from . import __version__
from .build import (
    build_sdist,
    clean,
)
from .config import (
    ProjectConfig,
    get_project_config,
)
from .lint import run_lint
from .test import run_tests
from .venv import get_venv
from .wheel import (
    build_manylinux_wheel,
    check_docker,
    test_manylinux_wheel,
)


def validate_extras(config: ProjectConfig, extras: list[str]) -> list[str]:
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


def cmd_requirements(args: argparse.Namespace) -> int:
    """Handle the requirements command."""
    config = get_project_config()
    extras = validate_extras(config, args.extras) if args.extras else []  # pyright: ignore[reportAny]
    venv = get_venv()
    venv.install(extras)
    return 0


def cmd_test(args: argparse.Namespace) -> int:
    """Handle the test command."""
    if args.wheel:  # pyright: ignore[reportAny]
        test_manylinux_wheel(
            None,
            arch=args.arch,  # pyright: ignore[reportAny]
            libc=args.libc,  # pyright: ignore[reportAny]
            python=args.python,  # pyright: ignore[reportAny]
        )
        return 0

    venv = get_venv()
    venv.ensure_test_tools()
    return run_tests(venv, args.path)  # pyright: ignore[reportAny]


def cmd_build(args: argparse.Namespace) -> int:
    """Handle the build command."""
    venv = get_venv()
    venv.ensure_build_tools()
    if args.sdist:  # pyright: ignore[reportAny]
        build_sdist(venv)

    if args.wheel:  # pyright: ignore[reportAny]
        build_manylinux_wheel(
            False,
            arch=args.arch,  # pyright: ignore[reportAny]
            libc=args.libc,  # pyright: ignore[reportAny]
            python=args.python,  # pyright: ignore[reportAny]
        )

    if args.native_wheel:  # pyright: ignore[reportAny]
        build_manylinux_wheel(
            True,
            arch=args.arch,  # pyright: ignore[reportAny]
            libc=args.libc,  # pyright: ignore[reportAny]
            python=args.python,  # pyright: ignore[reportAny]
        )

    return 0


def cmd_clean(_args: argparse.Namespace) -> int:
    """Handle the clean command."""
    clean()
    return 0


def cmd_lint(args: argparse.Namespace) -> int:
    """Handle the lint command."""
    return run_lint(get_venv(), fix=args.fix)  # pyright: ignore[reportAny]


def cmd_status(_args: argparse.Namespace) -> int:
    """Handle the status command."""
    config = get_project_config()
    venv = get_venv()
    print(f"Project: {config.name}-{config.version}")
    print(f"Docker: {'installed' if check_docker() else 'missing'}")
    print(f"Venv: {'installed' if venv.exists else 'missing'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Main entry point for emake."""
    parser = argparse.ArgumentParser(
        prog="emake",
        description="A Python module to replace Makefile workflows.",
    )
    _ = parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    _ = parser.add_argument(
        "--directory",
        "-C",
        help="Change to DIRECTORY before doing anything",
        metavar="DIRECTORY",
        default=".",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparser = subparsers.add_parser(
        "requirements",
        help="Create .venv and install dependencies",
    )
    _ = subparser.add_argument(
        "extras",
        nargs="*",
        help="Optional dependency groups to install (e.g., web test dev)",
    )

    subparser = subparsers.add_parser(
        "test",
        help="Run tests (default: all tests in tests/)",
    )
    _ = subparser.add_argument(
        "--wheel",
        action="store_true",
        help="Test using Docker with a built wheel instead of local code",
    )
    _ = subparser.add_argument(
        "--arch",
        default="x86_64",
        help="Target architecture for wheel testing (default: x86_64)",
    )
    _ = subparser.add_argument(
        "--libc",
        default="glibc",
        choices=["glibc", "musl"],
        help="Target libc for wheel testing (default: glibc)",
    )
    _ = subparser.add_argument(
        "--python",
        default="3.11",
        help="Python version for wheel testing (default: 3.11)",
    )
    _ = subparser.add_argument(
        "path",
        nargs="?",
        default="tests/",
        help="Path to test file or directory (default: tests/)",
    )

    subparser = subparsers.add_parser(
        "build",
        help="Build wheel and source distribution",
    )
    _ = subparser.add_argument(
        "--sdist",
        action="store_true",
        help="Build source distribution",
    )
    _ = subparser.add_argument(
        "--wheel",
        action="store_true",
        help="Build wheel",
    )
    _ = subparser.add_argument(
        "--native-wheel",
        action="store_true",
        help="Build platform-specific wheel instead of pure Python wheel",
        dest="native_wheel",
    )
    _ = subparser.add_argument(
        "--arch",
        default="x86_64",
        help="Target architecture for manylinux build (default: x86_64)",
    )
    _ = subparser.add_argument(
        "--libc",
        default="glibc",
        choices=["glibc", "musl"],
        help="Target libc for manylinux build (default: glibc)",
    )
    _ = subparser.add_argument(
        "--python",
        default="3.11",
        help="Python version for manylinux build (default: 3.11)",
    )

    _ = subparsers.add_parser(
        "clean",
        help="Remove build artifacts",
    )

    subparser = subparsers.add_parser(
        "lint",
        help="Run linting",
    )
    _ = subparser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically fix issues where supported",
    )

    _ = subparsers.add_parser(
        "status",
        help="Output status information",
    )

    args = parser.parse_args(argv)

    os.chdir(os.path.abspath(args.directory))  # pyright: ignore[reportAny]
    return {
        "requirements": cmd_requirements,
        "test": cmd_test,
        "build": cmd_build,
        "clean": cmd_clean,
        "lint": cmd_lint,
        "status": cmd_status,
    }[args.command](args)  # pyright: ignore[reportAny]


if __name__ == "__main__":
    sys.exit(main())
