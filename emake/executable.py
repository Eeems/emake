import os
import subprocess
import sys
from platform import uname

from .wheel import check_docker, get_platform, get_python_image, get_python_interpreter


def build_executable(
    package: str,
    arch: str,
    libc: str,
    python: str,
    setup: str | None,
    no_compress: bool,
) -> None:
    if not check_docker():
        print("Error: Docker is not available", file=sys.stderr)
        sys.exit(1)

    flags: list[str] = [
        "--python-flag=-m",
        "--mode=onefile",
        "--output-dir=build/",
        f"--output-filename=../dist/{package}-{arch}-{get_python_interpreter(python)}-{libc}",
        f"--include-package-data={package}",
    ]
    # Currently unable to do compression in github actions due to memory constraints
    if no_compress:
        flags.append("--onefile-no-compression")

    script = f"""
cd /src
{setup or ""}
mkdir -p build/ dist/
python -m pip install \
  --upgrade \
  --root-user-action=ignore \
  --extra-index-url="https://wheels.eeems.codes" \
  nuitka[onefile]
python -m pip install \
  --upgrade \
  --root-user-action=ignore \
  --extra-index-url="https://wheels.eeems.codes" \
  --editable \
  .
python -m nuitka {" ".join(flags)} {package}
owner=$(stat -c '%u:%g' .)
chown -R "$owner" build/ dist/
"""
    if libc == "glibc":
        script = f"apt-get update;apt-get install -y patchelf;{script}"

    else:
        script = f"apk add --no-cache patchelf binutils gcc musl-dev libffi-dev zstd-libs;{script}"

    print(f"Building executables for {arch} ({libc}) with Python {python}...")
    if arch != uname().machine:
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
            f"--volume={os.getcwd()}:/src",
            f"--platform={get_platform(arch)}",
            get_python_image(python, libc),
            "/bin/sh",
            "-ec",
            script,
        ],
        check=True,
    )

    print(f"Executable built for {arch}")
