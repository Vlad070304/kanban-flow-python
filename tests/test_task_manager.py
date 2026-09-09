import os
import unittest
from models.task import Task
from services.task_manager import TaskManager


class TestTaskModel(unittest.TestCase):
    # Tests covering Task dataclass serialization and property defaults.

    def test_task_creation_default_values(self):
        # Verify initial default state of Task model.
        task = Task(title="Default Task")
        self.assertEqual(task.title, "Default Task", "Task title should match initialization string")
        self.assertEqual(task.priority, "LOW", "Default task priority should be LOW")
        self.assertEqual(task.status, "To Do", "Default task status should be 'To Do'")
        self.assertIsNotNone(task.task_id, "Task ID should be automatically generated")
        self.assertGreater(len(task.task_id), 0, "Task ID should non-empty string")

    def test_task_creation_custom_values(self):
        # Verify custom task fields during instantiation.
        task = Task(title="Custom Task", priority="HIGH", status="In Progress", task_id="custom-id-999")
        self.assertEqual(task.title, "Custom Task")
        self.assertEqual(task.priority, "HIGH")
        self.assertEqual(task.status, "In Progress")
        self.assertEqual(task.task_id, "custom-id-999")

    def test_task_to_dict(self):
        # Verify dictionary serialization format.
        task = Task(title="Serialize Test", priority="HIGH", status="Done")
        data = task.to_dict()

        self.assertIsInstance(data, dict, "to_dict() should return a dictionary instance")
        self.assertEqual(data["title"], "Serialize Test")
        self.assertEqual(data["priority"], "HIGH")
        self.assertEqual(data["status"], "Done")
        self.assertEqual(data["task_id"], task.task_id)

    def test_task_from_dict(self):
        # Verify object construction from dictionary payload.
        data = {
            "task_id": "test-uuid-456",
            "title": "Deserialize Test",
            "priority": "LOW",
            "status": "In Progress"
        }
        task = Task.from_dict(data)

        self.assertEqual(task.task_id, "test-uuid-456")
        self.assertEqual(task.title, "Deserialize Test")
        self.assertEqual(task.priority, "LOW")
        self.assertEqual(task.status, "In Progress")

    def test_task_serialization_roundtrip(self):
        # Verify data consistency across to_dict -> from_dict conversion cycle.
        original = Task(title="Roundtrip Test", priority="HIGH", status="To Do")
        reconstructed = Task.from_dict(original.to_dict())

        self.assertEqual(original.task_id, reconstructed.task_id)
        self.assertEqual(original.title, reconstructed.title)
        self.assertEqual(original.priority, reconstructed.priority)
        self.assertEqual(original.status, reconstructed.status)


class TestTaskManager(unittest.TestCase):
    # Tests covering TaskManager state changes and JSON persistence logic.

    TEST_FILE = "test_kanban_data.json"

    def setUp(self):
        # Setup clean TaskManager instance before each test method runs.
        self.manager = TaskManager(storage_file=self.TEST_FILE)

    def tearDown(self):
        # Cleanup file system artifacts after each test method runs.
        if os.path.exists(self.TEST_FILE):
            os.remove(self.TEST_FILE)

    def test_add_multiple_tasks(self):
        # Test adding several task entities sequentially.
        task1 = self.manager.add_task("Task 1", priority="LOW")
        task2 = self.manager.add_task("Task 2", priority="HIGH", status="In Progress")

        self.assertEqual(len(self.manager.tasks), 2, "TaskManager should contain exactly 2 tasks")
        self.assertIn(task1, self.manager.tasks)
        self.assertIn(task2, self.manager.tasks)

    def test_remove_specific_task(self):
        # Test removing a single task among multiple stored records.
        task1 = self.manager.add_task("Keep Me")
        task2 = self.manager.add_task("Delete Me")

        self.assertEqual(len(self.manager.tasks), 2)
        self.manager.remove_task(task2.task_id)

        self.assertEqual(len(self.manager.tasks), 1)
        self.assertEqual(self.manager.tasks[0].title, "Keep Me")

    def test_remove_nonexistent_task(self):
        # Test calling remove_task with invalid ID without throwing errors.
        self.manager.add_task("Existing Task")
        self.manager.remove_task("invalid-nonexistent-id")
        self.assertEqual(len(self.manager.tasks), 1, "List size should remain unchanged")

    def test_clear_done_tasks(self):
        # Test batch purging of completed status tasks.
        self.manager.add_task("Task 1", status="To Do")
        self.manager.add_task("Task 2", status="Done")
        self.manager.add_task("Task 3", status="In Progress")
        self.manager.add_task("Task 4", status="Done")

        self.assertEqual(len(self.manager.tasks), 4)
        self.manager.clear_done()

        self.assertEqual(len(self.manager.tasks), 2)
        remaining_statuses = [t.status for t in self.manager.tasks]
        self.assertNotIn("Done", remaining_statuses)

    def test_load_nonexistent_file(self):
        # Test loading from file path when file has not been created yet.
        tasks = self.manager.load_from_file()
        self.assertEqual(tasks, [], "Loading missing file should return empty list without error")

    def test_save_and_load_persistence(self):
        # Test saving board state to disk and loading back from disk.
        self.manager.add_task("Persistent Task 1", priority="HIGH", status="In Progress")
        self.manager.add_task("Persistent Task 2", priority="LOW", status="Done")
        self.manager.save_to_file()

        self.assertTrue(os.path.exists(self.TEST_FILE), "Storage JSON file should be created on save")

        # Load file into brand-new manager instance
        new_manager = TaskManager(storage_file=self.TEST_FILE)
        loaded = new_manager.load_from_file()

        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0].title, "Persistent Task 1")
        self.assertEqual(loaded[0].priority, "HIGH")
        self.assertEqual(loaded[1].title, "Persistent Task 2")
        self.assertEqual(loaded[1].status, "Done")


if __name__ == "__main__":
    unittest.main()