"""Tests for emake module."""


def test_config():
    """Test that config can be loaded."""
    from emake.config import get_project_config

    config = get_project_config()
    assert config.name == "emake"


def test_venv():
    """Test that venv can be created."""
    from emake.venv import get_venv

    venv = get_venv()
    assert venv.exists
