"""Docker-based manylinux wheel building for emake."""

import os
import subprocess
import sys
from glob import iglob


def check_docker() -> bool:
    """Check if Docker is available."""
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            check=False,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def get_python_interpreter(python_version: str) -> str:
    """Get the Python interpreter tag for manylinux.

    Args:
        python_version: Python version (e.g., "3.11").

    Returns:
        Interpreter tag (e.g., "cp311-cp311").
    """
    return f"cp{python_version.replace('.', '')}-cp{python_version.replace('.', '')}"


def get_manylinux_image(arch: str, libc: str) -> str:
    """Get the Docker image for the given architecture and libc.

    Args:
        arch: Architecture (e.g., "x86_64", "aarch64").
        libc: Libc type (e.g., "glibc", "musl").

    Returns:
        Docker image name.
    """
    if libc == "musl":
        return f"musllinux_1_2_{arch}"

    if arch == "armv7l":
        return f"manylinux_2_35_{arch}"

    if arch == "riscv64":
        return f"manylinux_2_39_{arch}"

    return f"manylinux_2_34_{arch}"


def build_manylinux_wheel(
    native: bool,
    arch: str,
    libc: str,
    python: str,
    setup: str | None,
) -> None:
    """Build a manylinux wheel using Docker.

    Args:
        arch: Target architecture. Defaults to environment or "x86_64".
        libc: Target libc. Defaults to environment or "glibc".
        python: Python version. Defaults to environment or "3.11".
    """

    if not check_docker():
        print("Error: Docker is not available", file=sys.stderr)
        sys.exit(1)

    image = get_manylinux_image(arch, libc)
    python_interpreter = get_python_interpreter(python)

    flags: list[str] = []
    if not native:  # TODO determine based on build system in use
        flags.append("--config-setting=build_with_nuitka=false")

    script = f"""
set -e
manylinux-interpreters ensure "{python_interpreter}"
PATH="/opt/python/{python_interpreter}/bin:$PATH"
cd /src
{setup or ""}
rm -rf build/
python -m pip install \
  --upgrade \
  --extra-index-url="https://wheels.eeems.codes" \
  build
python -m build --wheel {" ".join(flags)}
{f"auditwheel repair dist/*_{arch}.whl" if native else ""}
owner=$(stat -c '%u:%g' .)
chown -R "$owner" dist/ *.egg-info/ build/
{f"rm -f dist/*_{arch}.whl" if native else ""}
{"mv wheelhouse/* dist/" if native else ""}
rm -rf wheelhouse/
"""

    print(f"Building manylinux wheel for {arch} ({libc}) with Python {python}...")
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
            f"{os.getcwd()}:/src",
            f"quay.io/pypa/{image}:latest",
            "/bin/bash",
            "-ec",
            script,
        ],
        check=True,
    )

    print(f"Manylinux wheel built for {arch}")


def find_wheel(directory: str, arch: str) -> str | None:
    if not os.path.exists(directory):
        return None

    for file in iglob(f"{directory}/*_{arch}.whl"):
        return file

    for file in iglob(f"{directory}/*.whl"):
        return file

    return None


def get_platform(arch: str) -> str:
    match arch:
        case "i686":
            return "linux/386"

        case "armv7l":
            return "linux/arm/v7"

        case _:
            return f"linux/{arch}"


def get_python_image(python: str, libc: str) -> str:
    if libc == "musl":
        return f"python:{python}-alpine"

    return f"python:{python}"


def test_manylinux_wheel(arch: str, libc: str, python: str, setup: str | None) -> None:
    """Test a built manylinux wheel"""
    if not check_docker():
        print("Error: Docker is not available", file=sys.stderr)
        sys.exit(1)

    wheel_path: str | None = None
    for directory in ["wheelhouse", "dist"]:
        wheel_path = find_wheel(directory, arch)
        if wheel_path is not None:
            break

    else:
        raise FileNotFoundError(f"Error: No wheel found for architecture {arch}")

    script = f"""
cd /src
{setup or ""}
pip install \
  --root-user-action=ignore \
  --extra-index-url="https://wheels.eeems.codes" \
  "{wheel_path}"[test]
git config --global user.email 'root@localhost'
git config --global user.name "Test Runner"
git config --global init.defaultBranch trunk
mkdir -p /tmp/test
cd /tmp/test;
cp -r /src/tests .
python -m pytest -vv tests
"""

    if libc == "musl":
        script = f"apk add --no-cache git;{script}"

    def install_rust() -> str:
        match libc:
            case "musl":
                return "apk add --no-cache gcc musl-dev python3-dev libffi-dev openssl-dev cargo pkgconfig;"

            case "glibc":
                return 'apt-get update;DEBIAN_FRONTEND="noninteractive" apt-get install -y rustc cargo;'

            case _:
                raise NotImplementedError(f"ERROR: Unknown libc {libc}")

    match arch:
        case "i686":
            script = f"{install_rust()}{script}"

        case "s390x":
            script = f"{install_rust()}{script}"

        case "riscv64":
            if python == "3.11" and libc == "glibc":
                print(
                    "WARNING: python image does not support cp311-manylinux_2_39_riscv64, exiting without error",
                    file=sys.stderr,
                )
                return

            script = f"{install_rust()}{script}"

        case "ppc64le":
            if libc == "musl":
                script = f"{install_rust()}{script}"

        case "armv7l":
            if libc == "musl":
                script = f"{install_rust()}{script}"

        case _:
            pass

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

    image = get_python_image(python, libc)
    print(f"Testing wheel {wheel_path} on {image}...")
    _ = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            f"--volume={os.getcwd()}:/src",
            f"--platform={get_platform(arch)}",
            image,
            "/bin/sh",
            "-ec",
            script,
        ],
        check=True,
    )

    print("Wheel tests passed")
