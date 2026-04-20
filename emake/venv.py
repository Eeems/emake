"""Virtual environment management for emake."""

import os
import subprocess
import venv
from pathlib import Path


VENV_DIR = Path(".venv")


class VirtualEnvironment:
    """Manages a virtual environment."""

    path: Path
    python: Path

    def __init__(self, path: Path | None = None):
        """Initialize virtual environment manager.

        Args:
            path: Path to virtual environment. Defaults to .venv in cwd.
        """
        self.path = path or VENV_DIR
        self.python = self.path / "bin" / "python"

    @property
    def exists(self) -> bool:
        """Check if virtual environment exists."""
        return self.path.exists() and self.python.exists()

    def create(self) -> None:
        """Create the virtual environment."""
        print(f"Creating virtual environment at {self.path}")
        builder = venv.EnvBuilder(with_pip=True, upgrade_deps=True)
        builder.create(self.path)
        self._upgrade_pip()

    def _upgrade_pip(self) -> None:
        """Upgrade pip in the virtual environment."""
        _ = subprocess.run(
            [str(self.python), "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            capture_output=True,
        )

    def ensure_build_tools(self) -> None:
        """Ensure build and wheel are installed in the venv."""
        if not self.exists:
            self.create()
        self._upgrade_pip()
        _ = subprocess.run(
            [str(self.python), "-m", "pip", "install", "--quiet", "build", "wheel"],
            check=True,
        )

    def ensure_test_tools(self) -> None:
        """Ensure pytest is installed in the venv."""
        if not self.exists:
            self.create()
        self._upgrade_pip()
        _ = subprocess.run(
            [str(self.python), "-m", "pip", "install", "--quiet", "pytest"],
            check=True,
        )

    def ensure_lint_tools(self) -> None:
        """Ensure linting tools are installed in the venv."""
        if not self.exists:
            self.create()
        _ = subprocess.run(
            [
                str(self.python),
                "-m",
                "pip",
                "install",
                "--quiet",
                "ruff",
                "vulture",
                "basedpyright",
                "dodgy",
                "pyroma",
            ],
            check=True,
        )

    def install(self, extras: list[str] | None = None) -> None:
        """Install the package with optional extras.

        Args:
            extras: List of extra dependency groups to install.
        """
        if not self.exists:
            self.create()
        else:
            print(f"Using existing virtual environment at {self.path}")

        # Build install command
        cmd = [str(self.python), "-m", "pip", "install", "--quiet", "--editable", "."]

        if extras:
            extra_str = ",".join(extras)
            cmd[4] = f".[{extra_str}]"

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error installing: {result.stderr}")
            raise subprocess.CalledProcessError(result.returncode, cmd)
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
        if not self.exists:
            raise RuntimeError("Virtual environment not created")

        run_env: dict[str, str] = os.environ.copy()
        if env:
            run_env.update(env)

        return subprocess.run(
            [str(self.python)] + list(args),
            check=True,
            capture_output=True,
            text=True,
            env=run_env,
        )


def get_venv(path: Path | None = None) -> VirtualEnvironment:
    """Get a VirtualEnvironment instance.

    Args:
        path: Optional path to .venv directory.

    Returns:
        VirtualEnvironment instance.
    """
    return VirtualEnvironment(path)
