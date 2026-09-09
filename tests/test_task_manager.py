"""
tests/test_task_manager.py
Unit tests verifying Task model serialization and TaskManager operations.
"""

import os
import unittest

from models.task import Task
from services.task_manager import TaskManager


class TestTaskModel(unittest.TestCase):
    """Test suite verifying Task model initialization and serialization."""

    def test_task_creation_default_values(self) -> None:
        """Verifies task creation requires task_id and assigns defaults."""
        task = Task(task_id="t-1", title="Default Task")
        self.assertEqual(task.task_id, "t-1")
        self.assertEqual(task.title, "Default Task")
        self.assertEqual(task.priority, "LOW")
        self.assertEqual(task.status, "To Do")

    def test_task_creation_custom_values(self) -> None:
        """Verifies task creation with explicit custom metadata."""
        task = Task(
            task_id="t-2",
            title="Custom Task",
            priority="HIGH",
            status="In Progress",
            due_date="2026-11-01",
            tags=["Urgent"]
        )
        self.assertEqual(task.priority, "HIGH")
        self.assertEqual(task.tags, ["Urgent"])

    def test_task_to_dict(self) -> None:
        """Verifies task dictionary serialization."""
        task = Task(
            task_id="t-3",
            title="Serialize Test",
            priority="HIGH",
            status="Done"
        )
        data = task.to_dict()
        self.assertEqual(data["task_id"], "t-3")
        self.assertEqual(data["title"], "Serialize Test")

    def test_task_from_dict(self) -> None:
        """Verifies task deserialization from dictionary."""
        data = {
            "task_id": "t-4",
            "title": "From Dict",
            "priority": "LOW",
            "status": "To Do",
            "due_date": "",
            "tags": []
        }
        task = Task.from_dict(data)
        self.assertEqual(task.task_id, "t-4")
        self.assertEqual(task.title, "From Dict")

    def test_task_serialization_roundtrip(self) -> None:
        """Verifies roundtrip dict conversion produces identical attributes."""
        original = Task(
            task_id="t-5",
            title="Roundtrip Test",
            priority="HIGH",
            status="To Do"
        )
        data = original.to_dict()
        reconstructed = Task.from_dict(data)
        self.assertEqual(original.task_id, reconstructed.task_id)
        self.assertEqual(original.title, reconstructed.title)


class TestTaskManager(unittest.TestCase):
    """Test suite verifying TaskManager CRUD and file persistence operations."""

    TEST_FILE = "test_kanban_data.json"

    def setUp(self) -> None:
        """Instantiates clean TaskManager before each test."""
        self.manager = TaskManager(self.TEST_FILE)

    def tearDown(self) -> None:
        """Cleans up temporary JSON files after tests."""
        if os.path.exists(self.TEST_FILE):
            os.remove(self.TEST_FILE)

    def test_add_multiple_tasks(self) -> None:
        """Verifies adding tasks with all mandatory positional arguments."""
        self.manager.add_task("Task 1", "LOW", "To Do")
        self.manager.add_task("Task 2", "HIGH", "To Do")
        self.assertEqual(len(self.manager.tasks), 2)

    def test_remove_specific_task(self) -> None:
        """Verifies deleting task by task_id."""
        t1 = self.manager.add_task("Task 1", "LOW", "To Do")
        self.manager.add_task("Task 2", "HIGH", "To Do")
        self.manager.remove_task(t1.task_id)
        self.assertEqual(len(self.manager.tasks), 1)

    def test_remove_nonexistent_task(self) -> None:
        """Verifies attempting to remove unknown task_id degrades gracefully."""
        self.manager.add_task("Task 1", "LOW", "To Do")
        self.manager.remove_task("invalid-id")
        self.assertEqual(len(self.manager.tasks), 1)

    def test_clear_done_tasks(self) -> None:
        """Verifies clearing Done status tasks."""
        t1 = self.manager.add_task("Task 1", "LOW", "Done")
        self.manager.add_task("Task 2", "HIGH", "To Do")
        self.manager.clear_done()
        self.assertEqual(len(self.manager.tasks), 1)
        self.assertNotEqual(self.manager.tasks[0].task_id, t1.task_id)

    def test_save_and_load_persistence(self) -> None:
        """Verifies file saving and reloading produces matching tasks."""
        self.manager.add_task("Persistent Task", "HIGH", "To Do")
        self.manager.save_to_file()

        new_manager = TaskManager(self.TEST_FILE)
        loaded_tasks = new_manager.load_from_file()
        self.assertEqual(len(loaded_tasks), 1)
        self.assertEqual(loaded_tasks[0].title, "Persistent Task")

    def test_load_nonexistent_file(self) -> None:
        """Verifies loading non-existent file returns empty task list."""
        manager = TaskManager("non_existent_file.json")
        tasks = manager.load_from_file()
        self.assertEqual(tasks, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
