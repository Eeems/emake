"""Virtual environment management for emake."""

import os
import subprocess
import sys
import venv
from pathlib import Path


VENV_DIR = Path(".venv")
VENV_ACTIVATE = VENV_DIR / "bin" / "activate"
VENV_PYTHON = VENV_DIR / "bin" / "python"


class VirtualEnvironment:
    """Manages a virtual environment."""

    def __init__(self, path: Path | None = None):
        """Initialize virtual environment manager.

        Args:
            path: Path to virtual environment. Defaults to .venv in cwd.
        """
        self.path = path or VENV_DIR
        self.activate = self.path / "bin" / "activate"
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
        subprocess.run(
            [str(self.python), "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            capture_output=True,
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

    def run(self, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
        """Run a command in the virtual environment.

        Args:
            *args: Command and arguments to run.
            env: Additional environment variables.

        Returns:
            CompletedProcess instance.
        """
        if not self.exists:
            raise RuntimeError("Virtual environment not created")

        run_env = os.environ.copy()
        if env:
            run_env.update(env)

        return subprocess.run(
            [str(self.python)] + list(args),
            check=True,
            capture_output=True,
            text=True,
            env=run_env,
        )

    def run_interactive(self, *args: str, env: dict | None = None) -> None:
        """Run a command interactively in the virtual environment.

        Args:
            *args: Command and arguments to run.
            env: Additional environment variables.
        """
        if not self.exists:
            raise RuntimeError("Virtual environment not created")

        run_env = os.environ.copy()
        if env:
            run_env.update(env)

        subprocess.run(
            [str(self.python)] + list(args),
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