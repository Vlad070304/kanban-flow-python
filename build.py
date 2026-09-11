"""Build script for packaging the Task Manager Suite into a standalone executable."""

import subprocess
import sys


def build_executable() -> None:
    """Run PyInstaller with appropriate flags for a standalone desktop bundle."""
    print("Initializing PyInstaller build process...")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name=TaskManagerSuite",
        "main.py",
    ]

    try:
        subprocess.run(cmd, check=True, text=True)
        print("Executable build completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Build failed with exit code {e.returncode}.", file=sys.stderr)
        sys.exit(e.returncode)


if __name__ == "__main__":
    build_executable()
