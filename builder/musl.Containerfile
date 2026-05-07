ARG PYTHON_VERSION=3.11

FROM python:${PYTHON_VERSION}-alpine

RUN <<EOT
  set -e
  apk add --no-cache \
    binutils \
    cargo \
    ccache \
    gcc \
    git \
    libffi-dev \
    make \
    mold \
    musl-dev \
    openssl-dev \
    patchelf \
    pkgconfig \
    python3-dev \
    zstd-libs
  python -m pip install \
    --upgrade \
    --root-user-action=ignore \
    --extra-index-url="https://wheels.eeems.codes" \
    nuitka[onefile]
EOT
