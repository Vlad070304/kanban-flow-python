"""
models/task.py
Task data model supporting dictionary and SQL tuple conversions.
"""

from typing import List, Optional, Dict, Any, Tuple


class Task:
    """Represents an individual task domain model."""

    def __init__(
        self,
        task_id: str,
        title: str,
        priority: str = "LOW",
        status: str = "To Do",
        due_date: str = "",
        tags: Optional[List[str]] = None
    ) -> None:
        self.task_id: str = task_id
        self.title: str = title
        self.priority: str = priority
        self.status: str = status
        self.due_date: str = due_date
        self.tags: List[str] = tags if tags is not None else []

    def to_dict(self) -> Dict[str, Any]:
        """Serializes task attributes into a dictionary."""
        return {
            "task_id": self.task_id,
            "title": self.title,
            "priority": self.priority,
            "status": self.status,
            "due_date": self.due_date,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Factory method instantiating a Task from a dictionary."""
        return cls(
            task_id=data["task_id"],
            title=data["title"],
            priority=data.get("priority", "LOW"),
            status=data.get("status", "To Do"),
            due_date=data.get("due_date", ""),
            tags=data.get("tags", []),
        )

    def to_db_row(self) -> Tuple[str, str, str, str, str, str]:
        """Converts task attributes into a tuple for SQLite INSERT/UPDATE operations."""
        tags_str = ",".join(self.tags) if self.tags else ""
        return (self.task_id, self.title, self.priority, self.status, self.due_date, tags_str)

    @classmethod
    def from_db_row(cls, row: Tuple[str, str, str, str, str, str]) -> "Task":
        """Factory method instantiating a Task from a database row tuple."""
        task_id, title, priority, status, due_date, tags_str = row
        tags = tags_str.split(",") if tags_str else []
        return cls(
            task_id=task_id,
            title=title,
            priority=priority,
            status=status,
            due_date=due_date,
            tags=tags,
        )
