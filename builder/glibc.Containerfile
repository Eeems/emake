ARG PYTHON_VERSION=3.11

FROM python:${PYTHON_VERSION}

RUN <<EOT
  set -e
  apt-get update
  apt-get install -y \
    cargo \
    ccache \
    mold \
    patchelf \
    rustc
  python -m pip install \
    --upgrade \
    --root-user-action=ignore \
    --extra-index-url="https://wheels.eeems.codes" \
    nuitka[onefile]
EOT
