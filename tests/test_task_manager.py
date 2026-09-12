"""
tests/test_task_manager.py
Unit tests for Task model serialization and SQLite TaskManager service operations.
"""

import os
import unittest

from models.task import Task
from services.task_manager import TaskManager


class TestTaskModel(unittest.TestCase):
    """Tests for Task data class initialization and conversion handlers."""

    def test_task_creation_default_values(self) -> None:
        """Verifies task creation requires task_id and assigns default attributes."""
        task = Task(
            task_id="t-001", title="Default Task", priority="LOW", status="To Do"
        )
        self.assertEqual(task.title, "Default Task")
        self.assertEqual(task.status, "To Do")

    def test_task_db_row_roundtrip(self) -> None:
        """Verifies DB tuple conversion produces identical object fields."""
        original = Task(
            task_id="t-002",
            title="Database Task",
            priority="HIGH",
            status="In Progress",
            due_date="2026-10-01",
            tags=["urgent", "db"],
        )
        row = original.to_db_row()
        restored = Task.from_db_row(row)
        self.assertEqual(original.task_id, restored.task_id)
        self.assertEqual(original.tags, restored.tags)


class TestTaskManagerSQLite(unittest.TestCase):
    """Tests for TaskManager SQLite operations."""

    TEST_DB = "test_tasks.db"

    def setUp(self) -> None:
        """Instantiates TaskManager instance with test database prior to each test."""
        self.manager = TaskManager(db_path=self.TEST_DB)

    def tearDown(self) -> None:
        """Removes temporary test database file after each test execution."""
        if os.path.exists(self.TEST_DB):
            os.remove(self.TEST_DB)

    def test_add_and_persists_sqlite(self) -> None:
        """Verifies task added is written to SQLite DB."""
        task = self.manager.add_task("SQLite Task")
        self.assertEqual(len(self.manager.tasks), 1)

        new_manager = TaskManager(db_path=self.TEST_DB)
        loaded = new_manager.load_from_file()
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].task_id, task.task_id)


if __name__ == "__main__":
    unittest.main()
