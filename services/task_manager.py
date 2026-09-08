"""
services/task_manager.py
Handles task persistence, file loading with backward compatibility,
and collection management operations.
"""

import json
import os
import uuid
from typing import List, Optional

from models.task import Task


class TaskManager:
    """Manages the lifecycle and persistence of application tasks."""

    def __init__(self, filepath: str) -> None:
        """Initializes TaskManager with a target JSON storage path."""
        self.filepath: str = filepath
        self.tasks: List[Task] = []

    def load_from_file(self) -> List[Task]:
        """Loads tasks from storage, safely handling legacy files missing new fields."""
        if not os.path.exists(self.filepath):
            return []

        try:
            with open(self.filepath, "r", encoding="utf-8") as file:
                raw_data = json.load(file)
                self.tasks = [Task.from_dict(item) for item in raw_data]
        except (json.JSONDecodeError, IOError, OSError):
            self.tasks = []

        return self.tasks

    def save_to_file(self) -> None:
        """Serializes and writes all tasks to the JSON storage file."""
        raw_data = [task.to_dict() for task in self.tasks]
        with open(self.filepath, "w", encoding="utf-8") as file:
            json.dump(raw_data, file, indent=4)

    def add_task(
        self,
        title: str,
        priority: str,
        status: str,
        due_date: str = "",
        tags: Optional[List[str]] = None
    ) -> Task:
        """Creates a new task with optional due dates and tags, then appends it."""
        task_id: str = str(uuid.uuid4())[:8]
        new_task = Task(
            task_id=task_id,
            title=title,
            priority=priority,
            status=status,
            due_date=due_date,
            tags=tags
        )
        self.tasks.append(new_task)
        return new_task

    def remove_task(self, task_id: str) -> None:
        """Removes a specific task by its unique identifier."""
        self.tasks = [t for t in self.tasks if t.task_id != task_id]

    def clear_done(self) -> None:
        """Removes all tasks currently marked with 'Done' status."""
        self.tasks = [t for t in self.tasks if t.status != "Done"]
