"""Test runner for emake."""

import sys

from .venv import VirtualEnvironment


def run_tests(venv: VirtualEnvironment, path: str = "tests/") -> int:
    """Run pytest in the virtual environment.

    Args:
        venv: VirtualEnvironment instance.
        path: Path to test file or directory.

    Returns:
        Exit code from pytest.
    """
    if not venv.exists:
        print(
            "Error: Virtual environment not found. Run 'emake requirements' first.",
            file=sys.stderr,
        )
        return 1

    return venv.run("-um", "pytest", "-vv", path).returncode
