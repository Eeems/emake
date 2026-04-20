"""Linting for emake."""

import subprocess
from pathlib import Path

from .venv import VirtualEnvironment

WHITELIST_DIR = Path(".emake/vulture")


def run_tool(venv: VirtualEnvironment, tool: str, *args: str) -> bool:
    print(f"Running {tool}: ", end="", flush=True)
    result = subprocess.run(
        [venv.python, "-um", tool, *args],
        capture_output=True,
        text=True,
        check=False,
    )
    output = result.stdout + result.stderr
    if result.returncode != 0:
        print(f"FAIL ({result.returncode})")
        print(output)
        return False

    print("OKAY")
    return True


def run_lint(venv: VirtualEnvironment, fix: bool = False) -> int:
    """Run linting tools.

    Args:
        venv: VirtualEnvironment instance.
        fix: If True, automatically fix issues where supported.

    Returns:
        Exit code from linting.
    """
    venv.ensure_lint_tools()
    ret = 0
    if run_tool(venv, "ruff", "check", *(["--fix"] if fix else [])):
        ret += 1

    if run_tool(venv, "basedpyright", "--project=pyproject.toml"):
        ret += 1

    if run_tool(venv, "dodgy", "--zero-exit"):
        ret += 1

    if run_tool(venv, "pyroma", "."):
        ret += 1

    return ret
