"""
models/task.py
Task data model representation with timestamps for metrics tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class Task:
    """Represents a single task record with analytical lifecycle metrics."""

    title: str
    priority: str = "LOW"
    status: str = "To Do"
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )
    completed_at: str = ""

    def mark_completed(self):
        """Sets task status to Done and logs completion timestamp."""
        self.status = "Done"
        self.completed_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """Serializes Task instance including analytical properties."""
        return {
            "task_id": self.task_id,
            "title": self.title,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Instantiates Task object from dictionary key-value data."""
        return cls(
            title=data.get("title", ""),
            priority=data.get("priority", "LOW"),
            status=data.get("status", "To Do"),
            task_id=data.get("task_id", str(uuid.uuid4())),
            created_at=data.get(
                "created_at", datetime.now().isoformat()
            ),
            completed_at=data.get("completed_at", ""),
        )
