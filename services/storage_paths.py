"""Platform-aware paths for application data storage."""

import os
import sys
from pathlib import Path

APP_DIRECTORY_NAME = "KanbanTaskManager"


def get_app_data_dir() -> Path:
    """Return the platform-appropriate directory for application data."""
    if sys.platform == "win32":
        base_dir = os.environ.get("APPDATA")
        if base_dir:
            return Path(base_dir) / APP_DIRECTORY_NAME
        return Path.home() / "AppData" / "Roaming" / APP_DIRECTORY_NAME

    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_DIRECTORY_NAME

    base_dir = os.environ.get("XDG_DATA_HOME")
    if base_dir:
        return Path(base_dir) / APP_DIRECTORY_NAME
    return Path.home() / ".local" / "share" / APP_DIRECTORY_NAME


def get_app_data_path(filename: str) -> str:
    """Return a file path in the application data directory."""
    return str(get_app_data_dir() / filename)
