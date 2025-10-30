"""Utility script to create a local virtual environment and install dependencies.

Run this script with the Python interpreter you want to use for the game, e.g.::

    python setup_env.py

It creates (or updates) a `.venv` folder in the repository root and installs the
requirements listed in ``requirements.txt``. The script uses only the standard
library, so it works with any Python version that ships with the ``venv``
module (3.3+).
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.resolve()
ENV_DIR = PROJECT_ROOT / ".venv"
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"


def create_environment(*, recreate: bool) -> Path:
    """Create the virtual environment and return the path to its python exe."""

    if recreate and ENV_DIR.exists():
        print(f"Removing existing environment at {ENV_DIR}")
        shutil.rmtree(ENV_DIR)

    if ENV_DIR.exists():
        print(f"Environment already exists at {ENV_DIR}")
    else:
        print(f"Creating virtual environment at {ENV_DIR}")
        builder = venv.EnvBuilder(with_pip=True, clear=False)
        builder.create(ENV_DIR)

    python_path = ENV_DIR / ("Scripts" if os.name == "nt" else "bin") / "python"
    return python_path


def install_requirements(python_path: Path) -> None:
    """Install project dependencies inside the virtual environment."""

    if not REQUIREMENTS_FILE.exists():
        print("No requirements.txt found, skipping dependency installation")
        return

    print("Upgrading pip inside the virtual environment")
    subprocess.check_call([str(python_path), "-m", "pip", "install", "--upgrade", "pip"])

    print(f"Installing dependencies from {REQUIREMENTS_FILE}")
    subprocess.check_call([str(python_path), "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)])


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a local venv for Pac-Man")
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Recreate the virtual environment even if it already exists.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    try:
        python_path = create_environment(recreate=args.recreate)
        install_requirements(python_path)
    except subprocess.CalledProcessError as exc:
        print(f"Command failed with exit code {exc.returncode}")
        return exc.returncode
    except OSError as exc:
        print(f"Filesystem error: {exc}")
        return 1

    activation_hint = (
        f"source {ENV_DIR}/bin/activate"
        if os.name != "nt"
        else f"{ENV_DIR}\\Scripts\\activate.bat"
    )
    print("\nEnvironment ready! Activate it with:\n  " + activation_hint)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
