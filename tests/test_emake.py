# pyright: reportImplicitRelativeImport=false
"""Tests for emake module."""

import os
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from emake.config import ProjectConfig, diff


def test_config() -> None:
    """Test config loads."""
    config = ProjectConfig()
    assert config.name == "emake"


def test_venv() -> None:
    """Test venv exists."""
    from emake.venv import get_venv  # noqa: PLC0415

    venv = get_venv()
    assert venv.exists


def test_diff_same_version(tmp_path: Path) -> None:
    """Test when version same - no diff."""
    config_text = """
[project]
requires-python = ">=3.11"

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

    output = StringIO()
    with redirect_stdout(output):
        result = diff()

    stdout = output.getvalue()
    print(stdout)
    assert result == 0
    assert "requires" not in stdout


def test_diff_newer_setuptools(tmp_path: Path) -> None:
    """Test when setuptools newer - ok for grug."""
    config_text = """
[project]
requires-python = ">=3.11"

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

    output = StringIO()
    with redirect_stdout(output):
        result = diff()

    stdout = output.getvalue()
    print(stdout)
    assert result == 0
    assert "requires" not in stdout


def test_diff_older_setuptools(tmp_path: Path) -> None:
    """Test when setuptools older - grug see diff."""
    config_text = """
[project]
requires-python = ">=3.11"

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

    output = StringIO()
    with redirect_stdout(output):
        result = diff()

    stdout = output.getvalue()
    print(stdout)
    assert result == 1
    assert "setuptools>=70.1" in stdout


def test_diff_exact_version(tmp_path: Path) -> None:
    """Test with exact version == 70.1."""
    config_text = """
[project]
requires-python = ">=3.11"

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

    output = StringIO()
    with redirect_stdout(output):
        result = diff()

    stdout = output.getvalue()
    print(stdout)
    # == should also satisfy >=70.1
    assert result == 0
    assert "requires" not in stdout


def test_diff_complex_specifier(tmp_path: Path) -> None:
    """Test complex specifier like nuitka>=4.0.6,!=4.7."""
    config_text = """
[project]
requires-python = ">=3.11"

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

    output = StringIO()
    with redirect_stdout(output):
        result = diff()

    stdout = output.getvalue()
    print(stdout)
    assert result == 0
    assert "requires" not in stdout


def test_diff_nuitka_missing(tmp_path: Path) -> None:
    """Test when nuitka missing - grug report diff."""
    config_text = """
[project]
requires-python = ">=3.11"

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

    output = StringIO()
    with redirect_stdout(output):
        result = diff()

    stdout = output.getvalue()
    print(stdout)
    assert result == 1
    assert "nuitka" in stdout
    assert "missing" in stdout


def test_diff_python_version_marker(tmp_path: Path) -> None:
    """Test requirement with python_version marker."""
    config_text = """
[project]
requires-python = ">=3.11"

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

    output = StringIO()
    with redirect_stdout(output):
        result = diff()

    stdout = output.getvalue()
    print(stdout)
    assert result == 0
    assert "requires" not in stdout


def test_diff_sys_platform_marker(tmp_path: Path) -> None:
    """Test requirement with sys_platform marker."""
    config_text = """
[project]
requires-python = ">=3.11"

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

    output = StringIO()
    with redirect_stdout(output):
        result = diff()

    stdout = output.getvalue()
    print(stdout)
    assert result == 1
    assert "setuptools" in stdout
