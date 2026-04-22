"""Parse pyproject.toml for project configuration."""

from importlib import resources
from io import BytesIO
from pathlib import Path
from tomllib import load
from typing import (
    Any,
    cast,
)

from packaging.requirements import Requirement
from packaging.version import Version


class ProjectConfig:
    """Represents project configuration from pyproject.toml."""

    def __init__(self, file: Path | BytesIO | None = None) -> None:
        """Initialize config from pyproject.toml.

        Args:
            path: Path to pyproject.toml. If None, searches current directory.
            file: File-like object to load from instead of path.
        """
        self._data: dict[str, Any]  # pyright: ignore[reportExplicitAny]
        if isinstance(file, BytesIO):
            self._data = load(file)
            return

        elif file is None:
            file = self._find_pyproject()

        with open(file, "rb") as f:
            self._data = load(f)

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
        project: dict[str, object] = self._data["project"]  # pyright: ignore[reportAny]
        name_val = project["name"]
        assert isinstance(name_val, str), name_val
        return name_val

    @property
    def version(self) -> str:
        """Package version from [project].version."""
        project: dict[str, object] = self._data["project"]  # pyright: ignore[reportAny]
        version_val = project["version"]
        assert isinstance(version_val, str), version_val
        return version_val

    @property
    def extras(self) -> dict[str, list[str]] | None:
        """Dict of optional dependencies from [project.optional-dependencies]."""
        project: dict[str, object] = self._data["project"]  # pyright: ignore[reportAny]
        extras_val = project.get("optional-dependencies")
        if extras_val is None:
            return None

        assert isinstance(extras_val, dict), extras_val
        return cast(dict[str, list[str]], extras_val)

    @property
    def build_system_requires(self) -> list[str]:
        """Build system requires from [build-system].requires."""
        build_system: dict[str, object] = self._data["build-system"]  # pyright: ignore[reportAny]
        requires_val = build_system["requires"]
        assert isinstance(requires_val, list), requires_val
        return cast(list[str], requires_val)

    @property
    def build_backend(self) -> str:
        """Build backend from [build-system].build-backend."""
        build_system: dict[str, object] = self._data["build-system"]  # pyright: ignore[reportAny]
        backend_val = build_system["build-backend"]
        assert isinstance(backend_val, str), backend_val
        return backend_val

    @property
    def pyright_exclude(self) -> list[str] | None:
        """Pyright exclude from [tool.pyright].exclude."""
        tool: dict[str, object] = self._data["tool"]  # pyright: ignore[reportAny]
        pyright_val = tool.get("pyright")
        if pyright_val is None:
            return None

        assert isinstance(pyright_val, dict), pyright_val
        pyright_dict = cast(dict[str, object], pyright_val)
        exclude_val = pyright_dict.get("exclude")
        if exclude_val is None:
            return None

        assert isinstance(exclude_val, list), exclude_val
        return cast(list[str], exclude_val)

    @property
    def ruff_lint_exclude(self) -> list[str] | None:
        """Ruff lint exclude from [tool.ruff.lint].exclude."""
        tool: dict[str, object] = self._data["tool"]  # pyright: ignore[reportAny]
        ruff_val = tool.get("ruff")
        if ruff_val is None:
            return None

        assert isinstance(ruff_val, dict), ruff_val
        ruff_dict = cast(dict[str, object], ruff_val)
        ruff_lint_val = ruff_dict.get("lint")
        if ruff_lint_val is None:
            return None

        assert isinstance(ruff_lint_val, dict), ruff_lint_val
        ruff_lint_dict = cast(dict[str, object], ruff_lint_val)
        exclude_val = ruff_lint_dict.get("exclude")
        if exclude_val is None:
            return None

        assert isinstance(exclude_val, list), exclude_val
        return cast(list[str], exclude_val)


def diff() -> int:
    """Compare project's pyproject.toml against template.

    Returns:
        Exit code - 0 if no differences, 1 if differences found.
    """
    template = resources.files("emake").joinpath("pyproject.toml.tpl").read_text()
    template_text = template.format(
        name="x",
        description="x",
        author_name="x",
        author_email="x",
        license_spdx="x",
        python_version="x",
    )
    with BytesIO(template_text.encode()) as template_io:
        template_config = ProjectConfig(template_io)
        project = ProjectConfig()

        # Compare build-system.requires
        expected_reqs = template_config.build_system_requires
        actual_reqs = project.build_system_requires
        expected_dict: dict[str, Requirement] = {}
        actual_dict: dict[str, Requirement] = {}

        for req_str in expected_reqs:
            r = Requirement(req_str)
            expected_dict[r.name] = r
        for req_str in actual_reqs:
            r = Requirement(req_str)
            actual_dict[r.name] = r

        for req_str in expected_reqs:
            expected_req = expected_dict[Requirement(req_str).name]
            actual_req = actual_dict.get(expected_req.name)
            if actual_req is None:
                print(f"build-system.requires: expected {req_str}, got missing")
            else:
                actual_spec = next(iter(actual_req.specifier))
                assert actual_spec is not None
                actual_ver = Version(actual_spec.version)
                if actual_ver not in expected_req.specifier:
                    print(
                        f"build-system.requires: expected {req_str}, got {str(actual_req)}"
                    )

        # Compare build-system.build-backend
        if template_config.build_backend != project.build_backend:
            print(
                f"build-system.build-backend: expected {template_config.build_backend}, got {project.build_backend}"
            )

        # Compare tool.pyright.exclude
        if template_config.pyright_exclude != project.pyright_exclude:
            print(
                f"tool.pyright.exclude: expected {template_config.pyright_exclude}, got {project.pyright_exclude}"
            )

        # Compare tool.ruff.lint.exclude
        if template_config.ruff_lint_exclude != project.ruff_lint_exclude:
            print(
                f"tool.ruff.lint.exclude: expected {template_config.ruff_lint_exclude}, got {project.ruff_lint_exclude}"
            )

    return 0
