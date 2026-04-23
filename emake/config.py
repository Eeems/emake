"""Parse pyproject.toml for project configuration."""

from collections import defaultdict
from collections.abc import Mapping
from importlib import resources
from io import BytesIO
from pathlib import Path
from tomllib import load
from typing import (
    Any,
    cast,
)

from packaging.markers import Marker
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name
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
    def ruff_exclude(self) -> list[str] | None:
        """Ruff exclude from [tool.ruff].exclude."""
        tool: dict[str, object] = self._data["tool"]  # pyright: ignore[reportAny]
        ruff_val = tool.get("ruff")
        if ruff_val is None:
            return None

        assert isinstance(ruff_val, dict), ruff_val
        ruff_dict = cast(dict[str, object], ruff_val)
        exclude_val = ruff_dict.get("exclude")
        if exclude_val is None:
            return None

        assert isinstance(exclude_val, list), exclude_val
        return cast(list[str], exclude_val)

    @property
    def requires_python(self) -> str | None:
        """Get requires-python from [project] and return the requirement value"""
        project = self._data.get("project", {})  # pyright: ignore[reportAny]
        if project is None:
            return None

        assert isinstance(project, dict), project
        project = cast(dict[str, str], project)
        requires_python = project.get("requires-python", None)
        if requires_python is None:
            return None

        assert isinstance(requires_python, str), requires_python
        return requires_python


def _diff_lists(name: str, expected: list[str] | None, actual: list[str] | None) -> int:
    difference = set(expected or []) - set(actual or [])
    if not difference:
        return 0

    print(f"{name}: expected {expected}, got {actual}")
    return 1


def _get_min_version(spec: SpecifierSet) -> str | None:
    """Get minimum version from a specifier like >=3.8 or ==3.8."""
    for s in spec:
        if s.operator == ">=":
            return s.version

        if s.operator == "==":
            return s.version

    return None


def _specifier_covers(exp_spec: SpecifierSet, act_spec: SpecifierSet) -> bool:
    """Check if actual specifier covers expected.

    For >= specifiers, actual covers expected if actual's min version
    is greater than or equal to expected's min version.
    For == specifiers, actual must also be == (exact match required).
    """
    # Check for == first (exact version match required)
    exp_exact = None
    act_exact = None
    for s in exp_spec:
        if s.operator == "==":
            exp_exact = s.version
            break

    for s in act_spec:
        if s.operator == "==":
            act_exact = s.version
            break

    # If expected is exact, actual must match exactly
    if exp_exact is not None:
        if act_exact is None:
            # Check if actual's >= covers expected's ==
            act_min = _get_min_version(act_spec)
            if act_min is None:
                return False

            return Version(str(act_min)) >= Version(str(exp_exact))
        return exp_exact == act_exact

    # For >= specifiers
    exp_min = _get_min_version(exp_spec)
    act_min = _get_min_version(act_spec)

    if exp_min is None:
        return True

    if act_min is None:
        return False

    return Version(str(act_min)) >= Version(str(exp_min))


def _generate_marker_environments(requires_python: str) -> list[Mapping[str, str]]:
    """Generate marker test environments based on requires_python."""
    spec = SpecifierSet(requires_python)
    min_ver = None
    for s in spec:
        if s.operator == ">=":
            min_ver = s.version
            break

    test_version = str(min_ver) if min_ver else requires_python
    envs: list[Mapping[str, str]] = []
    for p in ["linux", "darwin", "win32"]:
        envs.append(
            {
                "python_version": test_version,
                "python_full_version": f"{test_version}.0",
                "sys_platform": p,
                "platform_system": p.capitalize(),
            }
        )

    return envs


def _marker_covers(
    exp_marker: Marker | None,
    act_marker: Marker | None,
    requires_python: str,
) -> bool:
    """Check if actual marker covers expected marker."""
    if exp_marker == act_marker:
        return True

    if act_marker is None:
        return True

    test_envs = _generate_marker_environments(requires_python)

    for env in test_envs:
        try:
            exp_result = True if exp_marker is None else exp_marker.evaluate(environment=env)
            act_result = act_marker.evaluate(environment=env)

            if exp_result and not act_result:
                return False

        except Exception:  # noqa: S112
            continue

    return True


def requirements_not_satisfied_by(
    expected: list[str],
    actual: list[str],
    requires_python: str,
) -> list[str]:
    """Find requirements not satisfied by actual.

    Compares expected requirements against actual requirements, returning those
    not covered by actual (missing or incompatible versions/markers).
    """
    reqs1 = [Requirement(x) for x in expected]
    reqs2 = [Requirement(x) for x in actual]
    groups1: dict[str, list[Requirement]] = defaultdict(list)
    groups2: dict[str, list[Requirement]] = defaultdict(list)
    for req in reqs1:
        name = canonicalize_name(req.name)
        groups1[name].append(req)

    for req in reqs2:
        name = canonicalize_name(req.name)
        groups2[name].append(req)

    not_covered: list[str] = []
    for name, reqs1_list in groups1.items():
        if name not in groups2:
            # Package missing from actual - add all expected requirements
            for req1 in reqs1_list:
                not_covered.append(str(req1))
            continue

        for req1 in reqs1_list:
            for req2 in groups2[name]:
                if (
                    _marker_covers(req1.marker, req2.marker, requires_python)
                    and set(req1.extras).issubset(set(req2.extras))
                    and _specifier_covers(req1.specifier, req2.specifier)
                ):
                    break

            else:
                not_covered.append(str(req1))

    return not_covered


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
    failed = 0
    with BytesIO(template_text.encode()) as template_io:
        template_config = ProjectConfig(template_io)
        project = ProjectConfig()
        if project.requires_python is None:
            print("Error: 'pyproject.toml' does not specify a 'requires-python' value.")
            failed += 1

        else:
            missing = requirements_not_satisfied_by(
                template_config.build_system_requires,
                project.build_system_requires,
                project.requires_python,
            )
            if missing:
                print(
                    f"build-system.requires: missing coverage for {', '.join(missing)}"
                )
                failed = 1

        if template_config.build_backend != project.build_backend:
            print(
                f"build-system.build-backend: expected {template_config.build_backend}, got {project.build_backend}"
            )
            failed = 1

        failed += _diff_lists(
            "tool.pyright.exclude",
            template_config.pyright_exclude,
            project.pyright_exclude,
        )
        failed += _diff_lists(
            "tool.ruff.exclude", template_config.ruff_exclude, project.ruff_exclude
        )

    return failed
