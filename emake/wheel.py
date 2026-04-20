"""Docker-based manylinux wheel building for emake."""

import os
import subprocess
import sys
from pathlib import Path

# Default values
DEFAULT_LIBC = "glibc"
DEFAULT_ARCH = "x86_64"
DEFAULT_PYTHON = "3.11"


def check_docker() -> bool:
    """Check if Docker is available."""
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def get_arch() -> str:
    """Get architecture from environment or use default."""
    return os.environ.get("arch", DEFAULT_ARCH)


def get_libc() -> str:
    """Get libc from environment or use default."""
    return os.environ.get("libc", DEFAULT_LIBC)


def get_python() -> str:
    """Get Python version from environment or use default."""
    return os.environ.get("python", DEFAULT_PYTHON)


def get_python_interpreter(python_version: str = DEFAULT_PYTHON) -> str:
    """Get the Python interpreter tag for manylinux.

    Args:
        python_version: Python version (e.g., "3.11").

    Returns:
        Interpreter tag (e.g., "cp311-cp311").
    """
    return f"cp{python_version.replace('.', '')}-cp{python_version.replace('.', '')}"


def get_docker_image(arch: str, libc: str) -> str:
    """Get the Docker image for the given architecture and libc.

    Args:
        arch: Architecture (e.g., "x86_64", "aarch64").
        libc: Libc type (e.g., "glibc", "musl").

    Returns:
        Docker image name.
    """
    if libc == "musl":
        return f"musllinux_1_2_{arch}"
    elif arch == "armv7l":
        return f"manylinux_2_35_{arch}"
    elif arch == "riscv64":
        return f"manylinux_2_39_{arch}"
    else:
        return f"manylinux_2_34_{arch}"


def build_manylinux_wheel(
    native: bool,
    arch: str | None = None,
    libc: str | None = None,
    python: str | None = None,
) -> None:
    """Build a manylinux wheel using Docker.

    Args:
        arch: Target architecture. Defaults to environment or "x86_64".
        libc: Target libc. Defaults to environment or "glibc".
        python: Python version. Defaults to environment or "3.11".
    """
    arch = arch or get_arch()
    libc = libc or get_libc()
    python = python or get_python()

    if not check_docker():
        print("Error: Docker is not available", file=sys.stderr)
        sys.exit(1)

    image = get_docker_image(arch, libc)
    python_interpreter = get_python_interpreter(python)

    flags: list[str] = []
    if not native:  # TODO determine based on build system in use
        flags.append("--config-setting=build_with_nuitka=false")

    # Create build script
    script = f"""
set -e
manylinux-interpreters ensure "{python_interpreter}";
PATH="/opt/python/{python_interpreter}/bin:$PATH";
cd /src;
rm -rf build/
python -m pip install --upgrade build;
python -m build --wheel {" ".join(flags)};
auditwheel repair dist/*_{arch}.whl;
owner=$(stat -c '%u:%g' .)
chown -R "$owner" dist/ *.egg-info/ build/ wheelhouse/
"""

    # Run Docker container
    print(f"Building manylinux wheel for {arch} ({libc}) with Python {python}...")

    # Setup binfmt for non-x86_64 architectures
    if arch != "x86_64":
        _ = subprocess.run(
            [
                "docker",
                "run",
                "--privileged",
                "--rm",
                "tonistiigi/binfmt",
                "--install",
                "all",
            ],
            check=True,
        )

    _ = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{Path.cwd()}:/src",
            f"quay.io/pypa/{image}:latest",
            "/bin/bash",
            "-ec",
            script,
        ],
        check=True,
    )

    print(f"Manylinux wheel built for {arch}")


def test_manylinux_wheel(
    wheel_path: Path | None = None,
    arch: str | None = None,
    libc: str | None = None,
    python: str | None = None,
) -> None:
    """Test a built manylinux wheel.

    Args:
        wheel_path: Path to wheel file. If None, searches wheelhouse/.
        arch: Target architecture. Defaults to environment or "x86_64".
        libc: Target libc. Defaults to environment or "glibc".
        python: Python version. Defaults to environment or "3.11".
    """
    arch = arch or get_arch()
    libc = libc or get_libc()
    python = python or get_python()

    if not check_docker():
        print("Error: Docker is not available", file=sys.stderr)
        sys.exit(1)

    # Find wheel if not provided
    if wheel_path is None:
        # Check wheelhouse for manylinux wheels, then dist for any wheel
        for directory in ["wheelhouse", "dist"]:
            dir_path = Path(directory)
            if dir_path.exists():
                # Try architecture-specific first, then any wheel file
                wheels = list(dir_path.glob(f"*_{arch}.whl"))
                if not wheels:
                    wheels = list(dir_path.glob("*.whl"))
                if wheels:
                    wheel_path = wheels[0]
                    break

    if wheel_path is None or not wheel_path.exists():
        print(f"Error: No wheel found for architecture {arch}", file=sys.stderr)
        sys.exit(1)

    # Create test script
    script = f"""
set -e
cd /src;
pip install "{wheel_path}" web test;
git config --global user.email 'root@localhost';
git config --global user.name "Test Runner";
git config --global init.defaultBranch trunk;
mkdir -p /tmp/test
cd /tmp/test;
cp -r /src/tests .
python -m pytest -vv tests;
"""

    # Select image based on libc
    if libc == "musl":
        image = f"python:{python}-alpine"
        script = f"apk add --no-cache git;{script}"
    else:
        image = f"python:{python}"

    # Setup binfmt for non-x86_64 architectures
    if arch != "x86_64":
        _ = subprocess.run(
            [
                "docker",
                "run",
                "--privileged",
                "--rm",
                "tonistiigi/binfmt",
                "--install",
                "all",
            ],
            check=True,
        )

    print(f"Testing wheel {wheel_path} on {image}...")

    _ = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--volume",
            f"{Path.cwd()}:/src",
            "--platform",
            f"linux/{arch}" if arch != "x86_64" else "linux/amd64",
            image,
            "/bin/sh",
            "-ec",
            script,
        ],
        check=True,
    )

    print("Wheel tests passed")
