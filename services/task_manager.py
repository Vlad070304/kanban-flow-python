"""
services/task_manager.py
Task management service handling CRUD operations and JSON persistence.
"""

import json
import os
from typing import List
from models.task import Task


class TaskManager:
    """Service class managing task lifecycle state and file I/O operations."""

    def __init__(self, storage_file: str = "kanban_data.json"):
        """Initializes task collection and specifies storage file path."""
        self.storage_file = storage_file
        self.tasks: List[Task] = []

    def add_task(self, title: str, priority: str = "LOW", status: str = "To Do") -> Task:
        """Creates and appends a new Task instance to the manager state."""
        task = Task(title=title, priority=priority, status=status)
        self.tasks.append(task)
        return task

    def remove_task(self, task_id: str) -> bool:
        """Removes a task matching the target task ID."""
        initial_len = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.task_id != task_id]
        return len(self.tasks) < initial_len

    def clear_done(self):
        """Removes all tasks currently marked with status 'Done'."""
        self.tasks = [t for t in self.tasks if t.status != "Done"]

    def save_to_file(self):
        """Saves active task collection to disk as JSON."""
        data = [t.to_dict() for t in self.tasks]
        try:
            with open(self.storage_file, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)
        except (IOError, TypeError) as err:
            print(f"Error saving file: {err}")

    def load_from_file(self) -> List[Task]:
        """Loads task objects from disk into manager state."""
        if not os.path.exists(self.storage_file):
            return []

        try:
            with open(self.storage_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                self.tasks = [Task.from_dict(item) for item in data]
                return self.tasks
        except (IOError, json.JSONDecodeError) as err:
            print(f"Error loading file: {err}")
            return []
