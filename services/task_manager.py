"""
services/task_manager.py
Service handling task collection management, JSON persistence, and backups.
"""

import json
import os
from typing import List, Optional

from models.task import Task


class TaskManager:
    """Manages CRUD operations, persistence, and backup options for Task objects."""

    def __init__(self, filepath: str = "kanban_data.json") -> None:
        self.filepath: str = filepath
        self.tasks: List[Task] = []

    def add_task(
        self,
        title: str,
        priority: str = "LOW",
        status: str = "To Do",
        due_date: str = "",
        tags: Optional[List[str]] = None
    ) -> Task:
        """Creates and adds a new task instance to the collection."""
        task_id = f"task-{len(self.tasks) + 1000}"
        task = Task(
            task_id=task_id,
            title=title,
            priority=priority,
            status=status,
            due_date=due_date,
            tags=tags if tags else []
        )
        self.tasks.append(task)
        return task

    def remove_task(self, task_id: str) -> bool:
        """Removes a task from the collection matching the given task_id."""
        initial_count = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.task_id != task_id]
        return len(self.tasks) < initial_count

    def clear_done(self) -> None:
        """Removes all tasks currently marked with status 'Done'."""
        self.tasks = [t for t in self.tasks if t.status != "Done"]

    def save_to_file(self) -> bool:
        """Saves current task collection to primary storage file."""
        try:
            data = [t.to_dict() for t in self.tasks]
            with open(self.filepath, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)
            return True
        except OSError:
            return False

    def load_from_file(self) -> List[Task]:
        """Loads task collection from primary storage file."""
        if not os.path.exists(self.filepath):
            self.tasks = []
            return self.tasks

        try:
            with open(self.filepath, "r", encoding="utf-8") as file:
                data = json.load(file)
            self.tasks = [Task.from_dict(item) for item in data]
            return self.tasks
        except (OSError, json.JSONDecodeError, KeyError):
            self.tasks = []
            return self.tasks

    def export_backup(self, target_filepath: str) -> bool:
        """Exports current task collection to a user-specified JSON backup file."""
        try:
            data = [task.to_dict() for task in self.tasks]
            with open(target_filepath, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)
            return True
        except (OSError, TypeError):
            return False

    def restore_backup(self, source_filepath: str) -> bool:
        """Restores tasks from a backup JSON file and persists to primary storage."""
        try:
            with open(source_filepath, "r", encoding="utf-8") as file:
                data = json.load(file)
            self.tasks = [Task.from_dict(item) for item in data]
            self.save_to_file()
            return True
        except (OSError, json.JSONDecodeError, KeyError):
            return False
