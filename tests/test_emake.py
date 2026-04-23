# pyright: reportImplicitRelativeImport=false
"""Tests for emake module."""

import os
import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from emake.config import diff


def test_venv() -> None:
    """Test venv exists."""
    from emake.venv import get_venv  # noqa: PLC0415

    venv = get_venv()
    assert venv.exists


def test_diff_same_version(tmp_path: Path) -> None:
    """Test when version same - no diff."""
    config_text = """
[project]
name = "test"
license = "MIT"
requires-python = ">=3.11"
authors = [{name = "test", email = "test@localhost"}]

[build-system]
requires = ["setuptools>=70.1", "nuitka>=4.0.6"]
build-backend = "nuitka.distutils.Build"

[project.optional-dependencies]
test = ["pytest"]

[tool.pyright]
exclude = [".venv", "build"]

[tool.ruff]
exclude = [".venv", "build"]
"""
    os.chdir(tmp_path)
    with open("pyproject.toml", "w") as f:
        _ = f.write(config_text)

    stdout = StringIO()
    stderr = StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        result = diff()

    stdout_text = stdout.getvalue()
    print(stdout_text)
    stderr_text = stderr.getvalue()
    print(stderr_text, file=sys.stderr)
    assert result == 0
    assert "missing coverage for" not in stderr_text


def test_diff_newer_setuptools(tmp_path: Path) -> None:
    """Test when setuptools newer - ok for grug."""
    config_text = """
[project]
name = "test"
license = "MIT"
requires-python = ">=3.11"
authors = [{name = "test", email = "test@localhost"}]

[build-system]
requires = ["setuptools>=80", "nuitka>=4.0.6"]
build-backend = "nuitka.distutils.Build"

[project.optional-dependencies]
test = ["pytest"]

[tool.pyright]
exclude = [".venv", "build"]

[tool.ruff]
exclude = [".venv", "build"]
"""
    os.chdir(tmp_path)
    with open("pyproject.toml", "w") as f:
        _ = f.write(config_text)

    stdout = StringIO()
    stderr = StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        result = diff()

    stdout_text = stdout.getvalue()
    print(stdout_text)
    stderr_text = stderr.getvalue()
    print(stderr_text, file=sys.stderr)
    assert result == 0
    assert "missing coverage for" not in stderr_text


def test_diff_older_setuptools(tmp_path: Path) -> None:
    """Test when setuptools older - grug see diff."""
    config_text = """
[project]
name = "test"
license = "MIT"
requires-python = ">=3.11"
authors = [{name = "test", email = "test@localhost"}]

[build-system]
requires = ["setuptools>=60", "nuitka>=4.0.6"]
build-backend = "nuitka.distutils.Build"

[project.optional-dependencies]
test = ["pytest"]

[tool.pyright]
exclude = [".venv", "build"]

[tool.ruff]
exclude = [".venv", "build"]
"""
    os.chdir(tmp_path)
    with open("pyproject.toml", "w") as f:
        _ = f.write(config_text)

    stdout = StringIO()
    stderr = StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        result = diff()

    stdout_text = stdout.getvalue()
    print(stdout_text)
    stderr_text = stderr.getvalue()
    print(stderr_text, file=sys.stderr)
    assert result == 1
    assert "setuptools>=70.1" in stderr_text


def test_diff_exact_version(tmp_path: Path) -> None:
    """Test with exact version == 70.1."""
    config_text = """
[project]
name = "test"
license = "MIT"
requires-python = ">=3.11"
authors = [{name = "test", email = "test@localhost"}]

[build-system]
requires = ["setuptools==70.1", "nuitka>=4.0.6"]
build-backend = "nuitka.distutils.Build"

[project.optional-dependencies]
test = ["pytest"]

[tool.pyright]
exclude = [".venv", "build"]

[tool.ruff]
exclude = [".venv", "build"]
"""
    os.chdir(tmp_path)
    with open("pyproject.toml", "w") as f:
        _ = f.write(config_text)

    stdout = StringIO()
    stderr = StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        result = diff()

    stdout_text = stdout.getvalue()
    print(stdout_text)
    stderr_text = stderr.getvalue()
    print(stderr_text, file=sys.stderr)
    # == should also satisfy >=70.1
    assert result == 0
    assert "missing coverage for" not in stdout_text


def test_diff_complex_specifier(tmp_path: Path) -> None:
    """Test complex specifier like nuitka>=4.0.6,!=4.7."""
    config_text = """
[project]
name = "test"
license = "MIT"
requires-python = ">=3.11"
authors = [{name = "test", email = "test@localhost"}]

[build-system]
requires = ["setuptools>=70.1", "nuitka>=4.0.6,!=4.7"]
build-backend = "nuitka.distutils.Build"

[project.optional-dependencies]
test = ["pytest"]

[tool.pyright]
exclude = [".venv", "build"]

[tool.ruff]
exclude = [".venv", "build"]
"""
    os.chdir(tmp_path)
    with open("pyproject.toml", "w") as f:
        _ = f.write(config_text)

    stdout = StringIO()
    stderr = StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        result = diff()

    stdout_text = stdout.getvalue()
    print(stdout_text)
    stderr_text = stderr.getvalue()
    print(stderr_text, file=sys.stderr)
    assert result == 0
    assert "missing coverage for" not in stderr_text


def test_diff_nuitka_missing(tmp_path: Path) -> None:
    """Test when nuitka missing - grug report diff."""
    config_text = """
[project]
name = "test"
license = "MIT"
requires-python = ">=3.11"
authors = [{name = "test", email = "test@localhost"}]

[build-system]
requires = ["setuptools>=70.1"]
build-backend = "nuitka.distutils.Build"

[project.optional-dependencies]
test = ["pytest"]

[tool.pyright]
exclude = [".venv", "build"]

[tool.ruff]
exclude = [".venv", "build"]
"""
    os.chdir(tmp_path)
    with open("pyproject.toml", "w") as f:
        _ = f.write(config_text)

    stdout = StringIO()
    stderr = StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        result = diff()

    stdout_text = stdout.getvalue()
    print(stdout_text)
    stderr_text = stderr.getvalue()
    print(stderr_text, file=sys.stderr)
    assert result == 1
    assert "missing coverage for nuitka" in stderr_text


def test_diff_python_version_marker(tmp_path: Path) -> None:
    """Test requirement with python_version marker."""
    config_text = """
[project]
name = "test"
license = "MIT"
requires-python = ">=3.11"
authors = [{name = "test", email = "test@localhost"}]

[build-system]
requires = ["setuptools>=70.1; python_version >= '3.11'", "nuitka>=4.0.6"]
build-backend = "nuitka.distutils.Build"

[project.optional-dependencies]
test = ["pytest"]

[tool.pyright]
exclude = [".venv", "build"]

[tool.ruff]
exclude = [".venv", "build"]
"""
    os.chdir(tmp_path)
    with open("pyproject.toml", "w") as f:
        _ = f.write(config_text)

    stdout = StringIO()
    stderr = StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        result = diff()

    stdout_text = stdout.getvalue()
    print(stdout_text)
    stderr_text = stderr.getvalue()
    print(stderr_text, file=sys.stderr)
    assert result == 0
    assert "missing coverage for" not in stderr_text


def test_diff_sys_platform_marker(tmp_path: Path) -> None:
    """Test requirement with sys_platform marker."""
    config_text = """
[project]
name = "test"
license = "MIT"
requires-python = ">=3.11"
authors = [{name = "test", email = "test@localhost"}]

[build-system]
requires = ["setuptools>=70.1; sys_platform == 'win32'", "nuitka>=4.0.6"]
build-backend = "nuitka.distutils.Build"

[project.optional-dependencies]
test = ["pytest"]

[tool.pyright]
exclude = [".venv", "build"]

[tool.ruff]
exclude = [".venv", "build"]
"""
    os.chdir(tmp_path)
    with open("pyproject.toml", "w") as f:
        _ = f.write(config_text)

    stdout = StringIO()
    stderr = StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        result = diff()

    stdout_text = stdout.getvalue()
    print(stdout_text)
    stderr_text = stderr.getvalue()
    print(stderr_text, file=sys.stderr)
    assert result == 1
    assert "missing coverage for setuptools" in stderr_text
