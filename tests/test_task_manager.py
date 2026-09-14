"""
tests/test_task_manager.py
Unit tests for Task model serialization and SQLite TaskManager service operations.
"""

import json
import os
import sqlite3
import tempfile
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

    def test_task_completion_and_dict_roundtrip(self) -> None:
        """Verifies completion updates subtasks and dictionary serialization."""
        task = Task(
            task_id="t-003",
            title="Complete task",
            subtasks=[{"title": "Step", "completed": False}],
        )

        task.mark_completed()
        restored = Task.from_dict(task.to_dict())

        self.assertEqual(task.status, "Done")
        self.assertTrue(task.subtasks[0]["completed"])
        self.assertEqual(restored.to_dict(), task.to_dict())

    def test_invalid_subtask_json_uses_empty_list(self) -> None:
        """Verifies malformed persisted subtask data does not break loading."""
        restored = Task.from_db_row(("id", "Title", "LOW", "To Do", "", "", "{"))

        self.assertEqual(restored.subtasks, [])


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

    def test_remove_and_clear_done(self) -> None:
        """Verifies task deletion works in memory and SQLite."""
        active = self.manager.add_task("Active")
        done = self.manager.add_task("Done", status="Done")

        self.assertTrue(self.manager.remove_task(active.task_id))
        self.assertFalse(self.manager.remove_task("missing"))
        self.manager.clear_done()

        loaded = TaskManager(db_path=self.TEST_DB).load_from_file()
        self.assertEqual([task.task_id for task in loaded], [])
        self.assertNotEqual(active.task_id, done.task_id)

    def test_due_task_filter_excludes_done_and_future_tasks(self) -> None:
        """Verifies due-task lookup excludes completed and future tasks."""
        self.manager.add_task("Due", due_date="2000-01-01")
        self.manager.add_task("Future", due_date="2999-01-01")
        self.manager.add_task("Completed", due_date="2000-01-01", status="Done")

        due_tasks = self.manager.get_due_or_overdue_tasks()

        self.assertEqual([task.title for task in due_tasks], ["Due"])

    def test_restore_backup_rejects_invalid_json(self) -> None:
        """Verifies invalid backup files return false without replacing tasks."""
        with tempfile.TemporaryDirectory() as directory:
            backup_path = os.path.join(directory, "invalid.json")
            with open(backup_path, "w", encoding="utf-8") as file:
                file.write("{")

            self.assertFalse(self.manager.restore_backup(backup_path))
            self.assertEqual(self.manager.tasks, [])

    def test_restore_backup_replaces_existing_tasks(self) -> None:
        """Verifies restoring a backup removes tasks absent from the backup."""
        stale_task = self.manager.add_task("Stale task")
        restored_task = Task(task_id="restored-1", title="Restored task")

        with tempfile.TemporaryDirectory() as directory:
            backup_path = os.path.join(directory, "tasks.json")
            with open(backup_path, "w", encoding="utf-8") as file:
                json.dump([restored_task.to_dict()], file)

            self.assertTrue(self.manager.restore_backup(backup_path))

        self.assertEqual([task.task_id for task in self.manager.tasks], ["restored-1"])
        self.assertNotEqual(self.manager.tasks[0].task_id, stale_task.task_id)

        loaded = TaskManager(db_path=self.TEST_DB).load_from_file()
        self.assertEqual([task.task_id for task in loaded], ["restored-1"])

    def test_restore_backup_rejects_invalid_structure_without_changes(self) -> None:
        """Verifies malformed backup data leaves memory and storage unchanged."""
        existing_task = self.manager.add_task("Existing task")

        with tempfile.TemporaryDirectory() as directory:
            backup_path = os.path.join(directory, "invalid-structure.json")
            with open(backup_path, "w", encoding="utf-8") as file:
                json.dump({"tasks": []}, file)

            self.assertFalse(self.manager.restore_backup(backup_path))

        self.assertEqual(
            [task.task_id for task in self.manager.tasks], [existing_task.task_id]
        )
        loaded = TaskManager(db_path=self.TEST_DB).load_from_file()
        self.assertEqual([task.task_id for task in loaded], [existing_task.task_id])

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

    def test_export_and_restore_backup(self) -> None:
        """Verifies JSON backups preserve task fields through restore."""
        task = self.manager.add_task(
            "Backup task",
            priority="HIGH",
            tags=["backup"],
            subtasks=[{"title": "Verify", "completed": False}],
        )

        with tempfile.TemporaryDirectory() as directory:
            backup_path = os.path.join(directory, "tasks.json")
            self.assertTrue(self.manager.export_backup(backup_path))

            restored_manager = TaskManager(
                db_path=os.path.join(directory, "restored.db")
            )
            self.assertTrue(restored_manager.restore_backup(backup_path))
            restored = restored_manager.tasks[0]

        self.assertEqual(restored.task_id, task.task_id)
        self.assertEqual(restored.tags, ["backup"])
        self.assertEqual(restored.subtasks, [{"title": "Verify", "completed": False}])


if __name__ == "__main__":
    unittest.main()
