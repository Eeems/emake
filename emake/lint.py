"""Linting for emake."""

import os
import subprocess
from pathlib import Path

from .venv import VirtualEnvironment

WHITELIST_DIR = Path(".emake/vulture")


def run_lint(venv: VirtualEnvironment, fix: bool = False) -> int:
    """Run linting tools.

    Args:
        venv: VirtualEnvironment instance.
        fix: If True, automatically fix issues where supported.

    Returns:
        Exit code from linting.
    """
    if not venv.exists:
        print("Error: Virtual environment not found. Run 'emake requirements' first.")
        return 1

    ret = 0
    # ruff check (supports --fix)
    print("Running ruff: ", end="", flush=True)
    cmd = [str(venv.python), "-m", "ruff", "check"]
    if fix:
        cmd.append("--fix")

    result = subprocess.run(cmd, capture_output=True)
    output = result.stdout.decode() + result.stderr.decode()
    # When --fix is used, ruff may return 1 even if it fixed some things
    if result.returncode != 0:
        print(f"FAIL ({result.returncode})")
        print(output)
        ret += 1

    elif fix and "Fixed" in output:
        print("OKAY (fixed)")

    else:
        print("OKAY")

    # basedpyright runs on each directory separately
    for tool in ["basedpyright"]:
        for directory in ["emake", "tests"]:
            print(f"Running {tool} {directory}: ", end="", flush=True)
            result = subprocess.run(
                [str(venv.python), "-m", tool, directory],
                capture_output=True,
            )
            if result.returncode != 0:
                print(f"FAIL ({result.returncode})")
                print(result.stdout.decode())
                ret += 1

            else:
                print("OKAY")

    # dodgy, ignore whitelist files
    print("Running dodgy: ", end="", flush=True)
    result = subprocess.run(
        [
            str(venv.python),
            "-m",
            "dodgy",
            "--zero-exit",
            "--ignore-paths",
            "dist/ build/ .venv/ emake/__whitelist.py tests/__whitelist.py",
        ],
        capture_output=True,
    )
    if result.returncode != 0:
        print(f"FAIL ({result.returncode})")
        print(result.stdout.decode())
        ret += 1

    else:
        print("OKAY")

    # pyroma
    print("Running pyroma: ", end="", flush=True)
    result = subprocess.run(
        [str(venv.python), "-m", "pyroma", "."],
        capture_output=True,
    )
    if result.returncode != 0:
        print(f"FAIL ({result.returncode})")
        print(result.stdout.decode())
        ret += 1

    else:
        print("OKAY")

    return ret
