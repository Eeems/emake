ARG PYTHON_VERSION=3.11

FROM python:${PYTHON_VERSION}-alpine

RUN <<EOT
  set -e
  apk add --no-cache \
    patchelf \
    binutils \
    gcc \
    musl-dev \
    libffi-dev \
    zstd-libs \
    make \
    mold \
    ccache
  python -m pip install \
    --upgrade \
    --root-user-action=ignore \
    --extra-index-url="https://wheels.eeems.codes" \
    nuitka[onefile]
EOT
