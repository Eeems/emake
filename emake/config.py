"""Parse pyproject.toml for project configuration."""

from pathlib import Path
from tomllib import load


class ProjectConfig:
    """Represents project configuration from pyproject.toml."""

    path: Path

    def __init__(self, path: Path | None = None):
        """Initialize config from pyproject.toml.

        Args:
            path: Path to pyproject.toml. If None, searches current directory.
        """
        if path is None:
            path = self._find_pyproject()
        self.path = path
        with open(path, "rb") as f:
            self._data: dict = load(f)

    def _find_pyproject(self) -> Path:
        """Find pyproject.toml in current or parent directories."""
        current = Path.cwd()
        for parent in [current] + list(current.parents):
            pyproject = parent / "pyproject.toml"
            if pyproject.exists():
                return pyproject
        raise FileNotFoundError("pyproject.toml not found")

    @property
    def name(self) -> str:
        """Package name from [project].name."""
        project: dict = self._data["project"]
        return str(project["name"])

    @property
    def version(self) -> str:
        """Package version from [project].version."""
        project: dict = self._data["project"]
        return str(project["version"])

    @property
    def extras(self) -> dict[str, list[str]]:
        """Dict of optional dependencies from [project.optional-dependencies]."""
        project: dict = self._data["project"]
        extras = project.get("optional-dependencies")
        return dict(extras) if extras else {}


def get_project_config(path: Path | None = None) -> ProjectConfig:
    """Get project configuration.

    Args:
        path: Path to pyproject.toml. If None, searches automatically.

    Returns:
        ProjectConfig instance.
    """
    return ProjectConfig(path)
