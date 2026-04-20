"""Parse pyproject.toml for project configuration."""

from pathlib import Path
from tomllib import TOMLDecodeError, load


class ProjectConfig:
    """Represents project configuration from pyproject.toml."""

    def __init__(self, path: Path | None = None):
        """Initialize config from pyproject.toml.

        Args:
            path: Path to pyproject.toml. If None, searches current directory.
        """
        if path is None:
            path = self._find_pyproject()
        self.path = path
        self._data = self._load(path)

    def _find_pyproject(self) -> Path:
        """Find pyproject.toml in current or parent directories."""
        current = Path.cwd()
        for parent in [current] + list(current.parents):
            pyproject = parent / "pyproject.toml"
            if pyproject.exists():
                return pyproject
        raise FileNotFoundError("pyproject.toml not found")

    def _load(self, path: Path) -> dict:
        """Load and parse pyproject.toml."""
        with open(path, "rb") as f:
            return load(f)

    @property
    def name(self) -> str:
        """Package name from [project].name."""
        return self._data["project"]["name"]

    @property
    def version(self) -> str:
        """Package version from [project].version."""
        return self._data["project"]["version"]

    @property
    def package_name(self) -> str:
        """Package name with dashes replaced by underscores."""
        return self.name.replace("-", "_")

    @property
    def dependencies(self) -> list[str]:
        """List of dependencies from [project].dependencies."""
        return self._data["project"].get("dependencies", [])

    @property
    def extras(self) -> dict[str, list[str]]:
        """Dict of optional dependencies from [project.optional-dependencies]."""
        return self._data["project"].get("optional-dependencies", {})

    @property
    def python_requires(self) -> str:
        """Python version requirement."""
        return self._data["project"].get("requires-python", ">=3.11")

    @property
    def build_system(self) -> dict:
        """Build system configuration."""
        return self._data.get("build-system", {})


def get_project_config(path: Path | None = None) -> ProjectConfig:
    """Get project configuration.

    Args:
        path: Path to pyproject.toml. If None, searches automatically.

    Returns:
        ProjectConfig instance.
    """
    return ProjectConfig(path)