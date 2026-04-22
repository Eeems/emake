name: Check and Build

on:
  push:
    branches:
      - master
  pull_request:
  workflow_dispatch:
  release:
    types: [ released ]

permissions: read-all

jobs:
  lint:
    name: Lint codebase
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python: &python-versions
          - "3.11"
          - "3.12"
          - "3.13"
          - "3.14"
    steps:
      - name: Checkout the Git repository
        uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: ${{{{ matrix.python }}}}
          cache: pip
      - name: Run lint
        run: |
          set -e
          pip install wheel packaging
          make lint

  test:
    name: Test with python ${{ matrix.python }}
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python: *python-versions
    steps:
      - name: Checkout the Git repository
        uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: ${{{{ matrix.python }}}}
          cache: pip
      - name: Run tests
        run: |
          set -e
          pip install wheel packaging
          make test

  build-sdist:
    name: Build sdist
    needs: [ lint, test ]
    runs-on: ubuntu-latest
    steps:
      - name: Checkout the Git repository
        uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: "3.11"
          cache: pip
      - name: Install build tool
        run: pip install build
      - name: Building sdist
        run: |
          set -e
          pip install wheel packaging
          make sdist
      - uses: actions/upload-artifact@v6
        with:
          name: pip-sdist
          path: dist/*
          if-no-files-found: error

  build-any-wheel:
    name: Build wheel
    needs: [ lint, test ]
    runs-on: ubuntu-latest
    steps:
      - name: Checkout the Git repository
        uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: "3.11"
          cache: pip
      - name: Install build tool
        run: pip install build
      - name: Building package
        run: make wheel
      - uses: actions/upload-artifact@v6
        with:
          name: pip-wheel-none-any
          path: dist/*
          if-no-files-found: error

  publish:
    name: Publish to PyPi
    if: github.event_name == 'release' && startsWith(github.ref, 'refs/tags')
    needs: [ build-sdist, build-any-wheel ]
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: write
    environment:
      name: pypi
      url: https://pypi.org/p/{project_name}
    steps:
      - name: Download pip packages
        id: download
        uses: actions/download-artifact@v8
        with:
          pattern: pip-*
          merge-multiple: true
          path: dist
      - name: Publish package distributions to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          packages-dir: ${{{{ steps.download.outputs.download-path }}}}
          skip-existing: true

  release:
    name: Add release artifacts
    if: github.event_name == 'release' && startsWith(github.ref, 'refs/tags')
    needs: publish
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - name: Checkout the Git repository
        uses: actions/checkout@v6
      - name: Download artifact
        id: download
        uses: actions/download-artifact@v8
        with:
          pattern: pip-*
          merge-multiple: true
          path: dist
      - name: Upload to release
        run: find . -type f | xargs -rI {{}} gh release upload "$TAG" {{}} --clobber
