"""Test runner for emake."""

import os
import subprocess
import sys

from emake.venv import VirtualEnvironment


def run_tests(venv: VirtualEnvironment, path: str = "tests/") -> int:
    """Run pytest in the virtual environment.

    Args:
        venv: VirtualEnvironment instance.
        path: Path to test file or directory.

    Returns:
        Exit code from pytest.
    """
    if not venv.exists:
        print("Error: Virtual environment not found. Run 'emake requirements' first.", file=sys.stderr)
        return 1

    env = os.environ.copy()
    result = subprocess.run(
        [str(venv.python), "-m", "pytest", "-vv", path],
        env=env,
    )
    return result.returncode