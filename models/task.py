<<<<<<< Updated upstream
"""
models/task.py
Defines the core Task data model supporting unique IDs, priority levels,
status columns, optional due dates, and descriptive tags.
"""

import datetime
from typing import Any, Dict, List, Optional


class Task:
    """Represents an individual Kanban task item."""
=======
"""Data model module for managing individual Kanban tasks and subtasks."""

import json
import uuid
from typing import Any, Dict, List, Optional, Tuple


class Task:
    """Represents a single task item within the Kanban application."""
>>>>>>> Stashed changes

    def __init__(
        self,
        title: str,
        priority: str = "LOW",
        status: str = "To Do",
        due_date: str = "",
        tags: Optional[List[str]] = None,
<<<<<<< Updated upstream
        completed_at: Optional[str] = None
    ) -> None:
        """Initializes a Task instance with attributes and metadata."""
        self.task_id: str = task_id
=======
        subtasks: Optional[List[Dict[str, Any]]] = None,
        task_id: Optional[str] = None
    ) -> None:
        """Initialize a new Task instance."""
        self.task_id: str = task_id or str(uuid.uuid4())
>>>>>>> Stashed changes
        self.title: str = title
        self.priority: str = priority
        self.status: str = status
        self.due_date: str = due_date
        self.tags: List[str] = tags if tags is not None else []
<<<<<<< Updated upstream
        self.completed_at: Optional[str] = completed_at

    def mark_completed(self) -> None:
        """Marks the task as completed."""
        self.completed_at = datetime.datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Serializes task attributes into a dictionary for JSON storage."""
=======
        self.subtasks: List[Dict[str, Any]] = subtasks if subtasks is not None else []

    def mark_completed(self) -> None:
        """Mark task status as Done and set subtasks to completed."""
        self.status = "Done"
        for subtask in self.subtasks:
            subtask["completed"] = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert task instance attributes to a dictionary payload."""
>>>>>>> Stashed changes
        return {
            "task_id": self.task_id,
            "title": self.title,
            "priority": self.priority,
            "status": self.status,
            "due_date": self.due_date,
            "tags": self.tags,
<<<<<<< Updated upstream
            "completed_at": self.completed_at
=======
            "subtasks": self.subtasks
>>>>>>> Stashed changes
        }

    def to_db_row(self) -> Tuple[str, str, str, str, str, str, str]:
        """Convert task instance attributes to an SQL row tuple for database insertion."""
        tags_str: str = ",".join(self.tags)
        subtasks_json: str = json.dumps(self.subtasks)
        return (
            self.task_id,
            self.title,
            self.priority,
            self.status,
            self.due_date,
            tags_str,
            subtasks_json
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
<<<<<<< Updated upstream
        """Creates a Task from a dictionary, ensuring backward compatibility for legacy records."""
        return cls(
            task_id=data.get("task_id", ""),
=======
        """Instantiate a Task instance from a dictionary payload."""
        return cls(
            task_id=data.get("task_id"),
>>>>>>> Stashed changes
            title=data.get("title", ""),
            priority=data.get("priority", "LOW"),
            status=data.get("status", "To Do"),
            due_date=data.get("due_date", ""),
            tags=data.get("tags", []),
<<<<<<< Updated upstream
            completed_at=data.get("completed_at", None)
=======
            subtasks=data.get("subtasks", [])
        )

    @classmethod
    def from_db_row(cls, row: Tuple[Any, ...]) -> "Task":
        """Instantiate a Task instance directly from an SQL database query row."""
        task_id, title, priority, status, due_date = row[0], row[1], row[2], row[3], row[4]

        tags: List[str] = []
        if len(row) > 5 and row[5]:
            tags = [t.strip() for t in str(row[5]).split(",") if t.strip()]

        subtasks: List[Dict[str, Any]] = []
        if len(row) > 6 and row[6]:
            try:
                subtasks = json.loads(row[6])
            except (json.JSONDecodeError, TypeError):
                subtasks = []

        return cls(
            task_id=str(task_id),
            title=str(title),
            priority=str(priority),
            status=str(status),
            due_date=str(due_date) if due_date else "",
            tags=tags,
            subtasks=subtasks
>>>>>>> Stashed changes
        )
