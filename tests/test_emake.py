# pyright: reportImplicitRelativeImport=false
"""Tests for emake module."""


def test_config() -> None:
    """Test that config can be loaded."""
    from emake.config import get_project_config  # noqa: PLC0415

    config = get_project_config()
    assert config.name == "emake"


def test_venv() -> None:
    """Test that venv can be created."""
    from emake.venv import get_venv  # noqa: PLC0415

    venv = get_venv()
    assert venv.exists
