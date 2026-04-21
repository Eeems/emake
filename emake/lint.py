"""Linting for emake."""

import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .venv import VirtualEnvironment

WHITELIST_DIR = Path(".emake/vulture")

SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


def run_lint_async(
    venv: VirtualEnvironment,
    tool: str,
    *args: str,
) -> tuple[int, str, str]:
    """Run a linting tool in background.

    Args:
        venv: VirtualEnvironment instance.
        tool: Tool name to run.
        *args: Arguments to pass to the tool.

    Returns:
        Tuple of (tool name, success, returncode, output).
    """
    result = venv.run("-um", tool, *args, capture_output=True)
    return result.returncode, result.stdout, result.stderr


def run_lint(venv: VirtualEnvironment, fix: bool = False) -> int:
    """Run linting tools concurrently.

    Args:
        venv: VirtualEnvironment instance.
        fix: If True, automatically fix issues where supported.

    Returns:
        Exit code - number of tools that failed.
    """
    venv.ensure_lint_tools()
    venv.install()
    tools = [
        ("ruff", "check", *(["--fix"] if fix else [])),
        ("basedpyright", "--project=pyproject.toml"),
        ("dodgy", "--zero-exit"),
        ("pyroma", "."),
    ]

    failed = 0
    spinner_idx = 0
    with ThreadPoolExecutor(max_workers=len(tools)) as executor:
        futures = {
            tool: executor.submit(
                run_lint_async,
                venv,
                tool,
                *args,
            )
            for tool, *args in tools
        }
        while not all(x.done() for x in futures.values()):
            spinner_idx = (spinner_idx + 1) % len(SPINNER_FRAMES)
            for tool, future in futures.items():
                if future.done():
                    returncode, _, _ = future.result()
                    print(
                        f"{tool}: {'PASS' if not returncode else f'FAIL ({returncode})'}"
                    )
                    continue

                print(f"{tool}: [{SPINNER_FRAMES[spinner_idx]}]")

            print("", end="", flush=True)
            time.sleep(0.1)
            print("\x1b[1A" * len(tools), end="")

    for tool, future in futures.items():
        returncode, stdout, stderr = future.result()
        print(f"{tool}: {'PASS' if not returncode else f'FAIL ({returncode})'}")
        if returncode:
            print(stdout)
            print(stderr, file=sys.stderr)
            failed += 1

    if failed:
        print(f"{failed} failed")

    return failed
