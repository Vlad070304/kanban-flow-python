"""
models/task.py
Defines the core Task data model supporting unique IDs, priority levels,
status columns, optional due dates, and descriptive tags.
"""

import datetime
from typing import Any, Dict, List, Optional


class Task:
    """Represents an individual Kanban task item."""

    def __init__(
        self,
        task_id: str,
        title: str,
        priority: str = "LOW",
        status: str = "To Do",
        due_date: str = "",
        tags: Optional[List[str]] = None,
        completed_at: Optional[str] = None
    ) -> None:
        """Initializes a Task instance with attributes and metadata."""
        self.task_id: str = task_id
        self.title: str = title
        self.priority: str = priority
        self.status: str = status
        self.due_date: str = due_date
        self.tags: List[str] = tags if tags is not None else []
        self.completed_at: Optional[str] = completed_at

    def mark_completed(self) -> None:
        """Marks the task as completed."""
        self.completed_at = datetime.datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Serializes task attributes into a dictionary for JSON storage."""
        return {
            "task_id": self.task_id,
            "title": self.title,
            "priority": self.priority,
            "status": self.status,
            "due_date": self.due_date,
            "tags": self.tags,
            "completed_at": self.completed_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Creates a Task from a dictionary, ensuring backward compatibility for legacy records."""
        return cls(
            task_id=data.get("task_id", ""),
            title=data.get("title", ""),
            priority=data.get("priority", "LOW"),
            status=data.get("status", "To Do"),
            due_date=data.get("due_date", ""),
            tags=data.get("tags", []),
            completed_at=data.get("completed_at", None)
        )
