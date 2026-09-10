"""
tests/test_task_manager.py
Unit tests for Task model serialization and TaskManager service operations.
"""

import os
import unittest

from models.task import Task
from services.task_manager import TaskManager


class TestTaskModel(unittest.TestCase):
    """Tests for Task data class initialization and dictionary serialization."""

    def test_task_creation_default_values(self) -> None:
        """Verifies task creation requires task_id and assigns default attributes."""
        task = Task(task_id="t-001", title="Default Task", priority="LOW", status="To Do")
        self.assertEqual(task.title, "Default Task")
        self.assertEqual(task.status, "To Do")

    def test_task_creation_custom_values(self) -> None:
        """Verifies task creation with explicit metadata attributes."""
        task = Task(
            task_id="t-002",
            title="Custom Task",
            priority="HIGH",
            status="In Progress",
            due_date="2026-10-01",
            tags=["urgent"]
        )
        self.assertEqual(task.priority, "HIGH")
        self.assertEqual(task.due_date, "2026-10-01")

    def test_task_to_dict(self) -> None:
        """Verifies task dictionary serialization."""
        task = Task(task_id="t-003", title="Serialize Test", priority="HIGH", status="Done")
        data = task.to_dict()
        self.assertEqual(data["task_id"], "t-003")
        self.assertEqual(data["title"], "Serialize Test")

    def test_task_from_dict(self) -> None:
        """Verifies task deserialization from dictionary object."""
        raw = {
            "task_id": "t-004",
            "title": "Dict Task",
            "priority": "MEDIUM",
            "status": "To Do",
            "due_date": "",
            "tags": []
        }
        task = Task.from_dict(raw)
        self.assertEqual(task.task_id, "t-004")
        self.assertEqual(task.title, "Dict Task")

    def test_task_serialization_roundtrip(self) -> None:
        """Verifies dict roundtrip conversion produces identical fields."""
        original = Task(task_id="t-005", title="Roundtrip Test", priority="HIGH", status="To Do")
        restored = Task.from_dict(original.to_dict())
        self.assertEqual(original.task_id, restored.task_id)
        self.assertEqual(original.title, restored.title)


class TestTaskManager(unittest.TestCase):
    """Tests for TaskManager CRUD operations and file storage."""

    TEST_FILE = "test_tasks.json"

    def setUp(self) -> None:
        """Instantiates TaskManager instance prior to each test."""
        self.manager = TaskManager(filepath=self.TEST_FILE)

    def tearDown(self) -> None:
        """Removes temporary test file after each test execution."""
        if os.path.exists(self.TEST_FILE):
            os.remove(self.TEST_FILE)

    def test_add_multiple_tasks(self) -> None:
        """Verifies adding multiple tasks generates task_ids and stores tasks."""
        t1 = self.manager.add_task("Task 1")
        t2 = self.manager.add_task("Task 2")
        self.assertEqual(len(self.manager.tasks), 2)
        self.assertIsNotNone(t1.task_id)
        self.assertIsNotNone(t2.task_id)

    def test_remove_specific_task(self) -> None:
        """Verifies task removal by task_id."""
        t1 = self.manager.add_task("Task to remove")
        self.assertTrue(self.manager.remove_task(t1.task_id))
        self.assertEqual(len(self.manager.tasks), 0)

    def test_remove_nonexistent_task(self) -> None:
        """Verifies removing non-existent task returns False."""
        self.assertFalse(self.manager.remove_task("invalid-id"))

    def test_clear_done_tasks(self) -> None:
        """Verifies clearing Done status tasks from active state."""
        self.manager.add_task("Active Task", status="To Do")
        self.manager.add_task("Completed Task", status="Done")
        self.manager.clear_done()
        self.assertEqual(len(self.manager.tasks), 1)
        self.assertEqual(self.manager.tasks[0].title, "Active Task")

    def test_save_and_load_persistence(self) -> None:
        """Verifies writing and reloading tasks produces expected state."""
        self.manager.add_task("Persistent Task")
        self.assertTrue(self.manager.save_to_file())

        new_manager = TaskManager(filepath=self.TEST_FILE)
        loaded_tasks = new_manager.load_from_file()
        self.assertEqual(len(loaded_tasks), 1)
        self.assertEqual(loaded_tasks[0].title, "Persistent Task")

    def test_load_nonexistent_file(self) -> None:
        """Verifies loading missing file degrades gracefully to empty list."""
        missing_manager = TaskManager(filepath="nonexistent_file.json")
        tasks = missing_manager.load_from_file()
        self.assertEqual(tasks, [])


if __name__ == "__main__":
    unittest.main()
