"""Tests for emake module."""


def test_version():
    """Test that version is set correctly."""
    from emake import __version__

    assert __version__ == "0.0.1"


def test_config():
    """Test that config can be loaded."""
    from emake.config import get_project_config

    config = get_project_config()
    assert config.name == "emake"
    assert config.version == "0.0.1"


def test_venv():
    """Test that venv can be created."""
    from emake.venv import get_venv

    venv = get_venv()
    assert venv.exists