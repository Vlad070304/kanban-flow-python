"""Tests for platform-aware application storage paths."""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from services.storage_paths import get_app_data_dir, get_app_data_path


class TestStoragePaths(unittest.TestCase):
    """Verify default data locations across supported platforms."""

    def test_windows_uses_appdata(self) -> None:
        """Verifies Windows uses the roaming application data directory."""
        with patch.dict(os.environ, {"APPDATA": r"C:\Users\Test\AppData\Roaming"}):
            with patch.object(sys, "platform", "win32"):
                self.assertEqual(
                    get_app_data_dir().name,
                    "KanbanTaskManager",
                )
                self.assertTrue(
                    str(get_app_data_dir())
                    .replace("\\", "/")
                    .endswith("/KanbanTaskManager")
                )

    def test_macos_uses_application_support(self) -> None:
        """Verifies macOS uses its standard application support directory."""
        with patch.object(sys, "platform", "darwin"):
            self.assertEqual(
                get_app_data_dir(),
                Path.home() / "Library" / "Application Support" / "KanbanTaskManager",
            )

    def test_linux_uses_xdg_data_home(self) -> None:
        """Verifies Linux honors XDG_DATA_HOME."""
        with patch.dict(os.environ, {"XDG_DATA_HOME": "/tmp/test-data"}):
            with patch.object(sys, "platform", "linux"):
                self.assertEqual(
                    get_app_data_path("tasks.db"),
                    str(Path("/tmp/test-data") / "KanbanTaskManager" / "tasks.db"),
                )
