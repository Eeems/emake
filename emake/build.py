"""Build management for emake."""

import os
import subprocess
import sys
from pathlib import Path

from emake.config import ProjectConfig
from emake.venv import VirtualEnvironment


def build_wheel(
    venv: VirtualEnvironment,
    config: ProjectConfig,
    native: bool = False,
) -> None:
    """Build a wheel.

    Args:
        venv: VirtualEnvironment instance.
        config: ProjectConfig instance.
        native: If True, build platform-specific wheel. If False, build pure Python wheel.
    """
    if not venv.exists:
        print("Error: Virtual environment not found. Run 'emake requirements' first.", file=sys.stderr)
        sys.exit(1)

    dist_dir = Path("dist")
    dist_dir.mkdir(exist_ok=True)

    cmd = [str(venv.python), "-m", "build", "--wheel"]

    if not native:
        cmd.append("--config-setting=build_with_nuitka=false")

    print(f"Building {'native' if native else 'pure'} wheel...")
    subprocess.run(cmd, check=True)
    print("Wheel built successfully")


def build_sdist(venv: VirtualEnvironment, config: ProjectConfig) -> None:
    """Build a source distribution.

    Args:
        venv: VirtualEnvironment instance.
        config: ProjectConfig instance.
    """
    if not venv.exists:
        print("Error: Virtual environment not found. Run 'emake requirements' first.", file=sys.stderr)
        sys.exit(1)

    dist_dir = Path("dist")
    dist_dir.mkdir(exist_ok=True)

    print("Building sdist...")
    subprocess.run(
        [str(venv.python), "-m", "build", "--sdist"],
        check=True,
    )
    print("sdist built successfully")


def build_all(venv: VirtualEnvironment, config: ProjectConfig) -> None:
    """Build both wheel and sdist.

    Args:
        venv: VirtualEnvironment instance.
        config: ProjectConfig instance.
    """
    if not venv.exists:
        print("Error: Virtual environment not found. Run 'emake requirements' first.", file=sys.stderr)
        sys.exit(1)

    dist_dir = Path("dist")
    dist_dir.mkdir(exist_ok=True)

    print("Building wheel and sdist...")
    subprocess.run(
        [str(venv.python), "-m", "build"],
        check=True,
    )
    print("Build complete")


def clean() -> None:
    """Remove build artifacts."""
    print("Cleaning build artifacts...")

    # Directories to remove
    dirs_to_remove = ["build", "dist", ".venv", "wheelhouse"]
    for d in dirs_to_remove:
        path = Path(d)
        if path.exists():
            import shutil

            shutil.rmtree(path)

    # Files to remove
    import glob

    files_to_remove = glob.glob("*.egg-info")
    for f in files_to_remove:
        path = Path(f)
        if path.exists():
            import shutil

            shutil.rmtree(path)

    # Additional patterns
    for pattern in ["*.build", "*.dist"]:
        for f in glob.glob(pattern):
            path = Path(f)
            if path.exists():
                import shutil

                shutil.rmtree(path)

    # Clean pycache
    for d in Path(".").rglob("__pycache__"):
        import shutil

        shutil.rmtree(d)

    for f in Path(".").rglob("*.pyc"):
        f.unlink()

    print("Clean complete")