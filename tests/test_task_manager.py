"""
tests/test_task_manager.py
Unit tests for Task model serialization and SQLite TaskManager service operations.
"""

import os
import sqlite3
import unittest
from contextlib import closing

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
    LEGACY_DB = "legacy_tasks.db"

    def setUp(self) -> None:
        """Instantiates TaskManager instance with test database prior to each test."""
        self.manager = TaskManager(db_path=self.TEST_DB)

    def tearDown(self) -> None:
        """Removes temporary test database file after each test execution."""
        if os.path.exists(self.TEST_DB):
            os.remove(self.TEST_DB)
        if os.path.exists(self.LEGACY_DB):
            os.remove(self.LEGACY_DB)

    def test_add_and_persists_sqlite(self) -> None:
        """Verifies task added is written to SQLite DB."""
        task = self.manager.add_task("SQLite Task")
        self.assertEqual(len(self.manager.tasks), 1)

        new_manager = TaskManager(db_path=self.TEST_DB)
        loaded = new_manager.load_from_file()
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].task_id, task.task_id)

    def test_migrates_legacy_database_and_records_version(self) -> None:
        """Verifies legacy databases receive the subtasks migration once."""
        with closing(sqlite3.connect(self.LEGACY_DB)) as connection, connection:
            connection.execute(
                """
                CREATE TABLE tasks (
                    task_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    due_date TEXT,
                    tags TEXT
                );
                """
            )
            connection.execute(
                """
                INSERT INTO tasks
                    (task_id, title, priority, status, due_date, tags)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                ("legacy-1", "Legacy task", "LOW", "To Do", "", "legacy"),
            )

        TaskManager(db_path=self.LEGACY_DB)
        with closing(sqlite3.connect(self.LEGACY_DB)) as connection, connection:
            columns = {
                column[1] for column in connection.execute("PRAGMA table_info(tasks);")
            }
            migration_versions = [
                row[0]
                for row in connection.execute("SELECT version FROM schema_migrations;")
            ]
            task_row = connection.execute(
                "SELECT task_id, subtasks FROM tasks WHERE task_id = ?;",
                ("legacy-1",),
            ).fetchone()

        self.assertIn("subtasks", columns)
        self.assertEqual(migration_versions, [1])
        self.assertEqual(task_row, ("legacy-1", None))

        TaskManager(db_path=self.LEGACY_DB)
        with closing(sqlite3.connect(self.LEGACY_DB)) as connection, connection:
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM schema_migrations;"
                ).fetchone()[0],
                1,
            )


if __name__ == "__main__":
    unittest.main()
