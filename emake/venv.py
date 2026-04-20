"""Virtual environment management for emake."""

import os
import subprocess
import sys
from pathlib import Path


class VirtualEnvironment:
    """Manages a virtual environment."""

    def __init__(self, path: Path) -> None:
        """Initialize virtual environment manager.

        Args:
            path: Path to virtual environment. Defaults to .venv in cwd.
        """
        self.path: Path = path.resolve()
        self.python: Path = self.path / "bin" / "python"
        self.pip: Path = self.path / "bin" / "pip"

    @property
    def exists(self) -> bool:
        """Check if virtual environment exists."""
        return (
            self.path.exists(follow_symlinks=True)
            and self.python.exists(follow_symlinks=True)
            and self.pip.exists(follow_symlinks=True)
        )

    def _chronic(
        self,
        *args: Path | str,
        env: dict[str, str] | None = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        proc = subprocess.run(
            args,
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
        if check and proc.returncode != 0:
            raise subprocess.CalledProcessError(
                proc.returncode,
                proc.args,  # pyright: ignore[reportAny]
                proc.stdout,
                proc.stderr,
            )

        return proc

    def ensure(self) -> None:
        if not self.exists:
            self.create()

        _ = self._chronic(self.python, "-um", "ensurepip")
        _ = self._chronic(self.pip, "install", "--upgrade", "pip")

    def create(self) -> None:
        """Create the virtual environment."""
        print(f"Creating virtual environment at {self.path}")
        _ = self._chronic(
            "python" if "__compiled__" in globals() else sys.executable,
            "-m",
            "venv",
            "--system-site-packages",
            "--upgrade",
            "--clear",
            self.path,
        )

    def ensure_build_tools(self) -> None:
        """Ensure build and wheel are installed in the venv."""
        self.ensure()
        _ = self._chronic(self.pip, "install", "build", "wheel")

    def ensure_test_tools(self) -> None:
        """Ensure pytest is installed in the venv."""
        self.ensure()
        _ = self._chronic(self.pip, "install", "pytest")

    def ensure_lint_tools(self) -> None:
        """Ensure linting tools are installed in the venv."""
        self.ensure()
        _ = self._chronic(
            self.pip,
            "install",
            "ruff",
            "vulture",
            "basedpyright",
            "dodgy",
            "pyroma",
        )

    def install(self, extras: list[str] | None = None) -> None:
        """Install the package with optional extras.

        Args:
            extras: List of extra dependency groups to install.
        """
        self.ensure()
        # Build install command
        _ = self._chronic(
            self.pip,
            "install",
            "--quiet",
            "--editable",
            f".[{','.join(extras)}]" if extras else ".",
        )
        print("Dependencies installed")

    def run(
        self, *args: str, env: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        """Run a command in the virtual environment.

        Args:
            *args: Command and arguments to run.
            env: Additional environment variables.

        Returns:
            CompletedProcess instance.
        """
        self.ensure()
        run_env: dict[str, str] = os.environ.copy()
        if env:
            run_env.update(env)

        return self._chronic(
            self.python,
            *args,
            env=run_env,
        )


def get_venv(path: Path | None = None) -> VirtualEnvironment:
    """Get a VirtualEnvironment instance.

    Args:
        path: Optional path to .venv directory.

    Returns:
        VirtualEnvironment instance.
    """
    return VirtualEnvironment(path or Path(".venv"))
