import os
import subprocess
import sys

from .wheel import check_docker, get_platform, get_python_image, get_python_interpreter


def build_executable(
    package: str,
    arch: str,
    libc: str,
    python: str,
    setup: str | None,
) -> None:
    if not check_docker():
        print("Error: Docker is not available", file=sys.stderr)
        sys.exit(1)

    script = f"""
cd /src
{setup or ""}
mkdir -p build/
python -m pip install \
  --upgrade \
  --root-user-action=ignore \
  nuitka[onefile]
python -m nuitka \
  --python-flag=-m \
  --mode=onefile \
  --output-dir=build/ \
  --output-filename="../dist/{package}-{arch}-cp{get_python_interpreter(python)}-{libc}" \
  --include-package-data={package} \
  {package}
owner=$(stat -c '%u:%g' .)
chown -R "$owner" build/ dist/
"""
    if libc == "glibc":
        script = f"apt-get update;apt-get install -y patchelf;{script}"

    else:
        script = (
            f"apk add --no-cache patchelf binutils gcc python3-dev musl-dev;{script}"
        )

    print(f"Building executables for {arch} ({libc}) with Python {python}...")
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
            f"--volume={os.getcwd()}:/src",
            f"--platform={get_platform(arch)}",
            get_python_image(python, libc),
            "/bin/sh",
            "-ec",
            script,
        ],
        check=True,
    )

    print(f"Manylinux wheel built for {arch}")
