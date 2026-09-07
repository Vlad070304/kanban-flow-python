"""
models/task.py
Task data model representation and dictionary serialization utilities.
"""

from dataclasses import dataclass, field
import uuid


@dataclass
class Task:
    """Represents a single task record on the Kanban board."""

    title: str
    priority: str = "LOW"
    status: str = "To Do"
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict:
        """Serializes the Task instance into a dictionary."""
        return {
            "task_id": self.task_id,
            "title": self.title,
            "priority": self.priority,
            "status": self.status
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Instantiates a Task object from dictionary key-value data."""
        return cls(
            title=data.get("title", ""),
            priority=data.get("priority", "LOW"),
            status=data.get("status", "To Do"),
            task_id=data.get("task_id", str(uuid.uuid4()))
        )
