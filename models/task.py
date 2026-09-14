"""Data model module for managing individual Kanban tasks and subtasks."""

import calendar
import json
import uuid
from datetime import date, timedelta
from enum import Enum
from typing import Any, TypeVar


class TaskPriority(str, Enum):
    """Supported task priority values."""

    LOW = "LOW"
    HIGH = "HIGH"


class TaskStatus(str, Enum):
    """Supported Kanban column values."""

    TO_DO = "To Do"
    IN_PROGRESS = "In Progress"
    DONE = "Done"


class TaskRecurrence(str, Enum):
    """Supported recurring task schedules."""

    NONE = "None"
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"


DEFAULT_PRIORITY = TaskPriority.LOW
DEFAULT_STATUS = TaskStatus.TO_DO
DEFAULT_RECURRENCE = TaskRecurrence.NONE
EnumValue = TypeVar("EnumValue", bound=Enum)


class Task:
    """Represents a single task item within the Kanban application."""

    def __init__(
        self,
        title: str,
        priority: str | TaskPriority = DEFAULT_PRIORITY,
        status: str | TaskStatus = DEFAULT_STATUS,
        due_date: str = "",
        tags: list[str] | None = None,
        subtasks: list[dict[str, Any]] | None = None,
        task_id: str | None = None,
        recurrence: str | TaskRecurrence = DEFAULT_RECURRENCE,
    ) -> None:
        """Initialize a validated Task instance."""
        self.task_id: str = self._validate_task_id(task_id or str(uuid.uuid4()))
        self.title = title
        self.priority = priority
        self.status = status
        self.due_date = due_date
        self.tags = tags
        self.subtasks = subtasks
        self.recurrence = recurrence

    @staticmethod
    def _validate_task_id(task_id: str) -> str:
        """Validate and normalize a task identifier."""
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError("task_id must be a non-empty string")
        return task_id.strip()

    @staticmethod
    def _validate_title(title: str) -> str:
        """Validate and normalize a task title."""
        if not isinstance(title, str) or not title.strip():
            raise ValueError("title must be a non-empty string")
        return title.strip()

    @staticmethod
    def _validate_enum(
        value: str | Enum, enum_type: type[EnumValue], field: str
    ) -> EnumValue:
        """Validate a value against a supported enum type."""
        try:
            return enum_type(value)
        except (TypeError, ValueError) as err:
            allowed = ", ".join(member.value for member in enum_type)
            raise ValueError(f"{field} must be one of: {allowed}") from err

    @staticmethod
    def _validate_due_date(due_date: str) -> str:
        """Validate an optional ISO-formatted due date."""
        if not isinstance(due_date, str):
            raise ValueError("due_date must be an ISO date string")
        if due_date:
            try:
                date.fromisoformat(due_date)
            except ValueError as err:
                raise ValueError("due_date must use YYYY-MM-DD format") from err
        return due_date

    @staticmethod
    def _validate_tags(tags: list[str] | None) -> list[str]:
        """Validate and normalize task tags."""
        if tags is None:
            return []
        if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
            raise ValueError("tags must be a list of strings")
        normalized_tags: list[str] = []
        for tag in tags:
            normalized_tag = tag.strip()
            if normalized_tag and normalized_tag not in normalized_tags:
                normalized_tags.append(normalized_tag)
        return normalized_tags

    @staticmethod
    def _validate_recurrence(
        recurrence: str | TaskRecurrence,
    ) -> TaskRecurrence:
        """Validate a recurring-task schedule."""
        try:
            return TaskRecurrence(recurrence)
        except (TypeError, ValueError) as err:
            allowed = ", ".join(member.value for member in TaskRecurrence)
            raise ValueError(f"recurrence must be one of: {allowed}") from err

    @staticmethod
    def _validate_subtasks(
        subtasks: list[dict[str, Any]] | None,
    ) -> list[dict[str, Any]]:
        """Validate and normalize task subtasks."""
        if subtasks is None:
            return []
        if not isinstance(subtasks, list):
            raise ValueError("subtasks must be a list")

        validated_subtasks: list[dict[str, Any]] = []
        for subtask in subtasks:
            if not isinstance(subtask, dict):
                raise ValueError("each subtask must be an object")
            subtask_title = subtask.get("title")
            completed = subtask.get("completed", False)
            if not isinstance(subtask_title, str) or not subtask_title.strip():
                raise ValueError("each subtask requires a non-empty title")
            if not isinstance(completed, bool):
                raise ValueError("subtask completed must be a boolean")
            validated_subtasks.append(
                {"title": subtask_title.strip(), "completed": completed}
            )
        return validated_subtasks

    @property
    def title(self) -> str:
        """Return the validated task title."""
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        """Set the task title after validation."""
        self._title = self._validate_title(value)

    @property
    def priority(self) -> TaskPriority:
        """Return the validated task priority."""
        return self._priority

    @priority.setter
    def priority(self, value: str | TaskPriority) -> None:
        """Set the task priority after validation."""
        self._priority = self._validate_enum(value, TaskPriority, "priority")

    @property
    def status(self) -> TaskStatus:
        """Return the validated task status."""
        return self._status

    @status.setter
    def status(self, value: str | TaskStatus) -> None:
        """Set the task status after validation."""
        self._status = self._validate_enum(value, TaskStatus, "status")

    @property
    def due_date(self) -> str:
        """Return the optional ISO-formatted due date."""
        return self._due_date

    @due_date.setter
    def due_date(self, value: str) -> None:
        """Set the due date after validation."""
        self._due_date = self._validate_due_date(value)

    @property
    def tags(self) -> list[str]:
        """Return the normalized task tags."""
        return self._tags

    @tags.setter
    def tags(self, value: list[str] | None) -> None:
        """Set the task tags after validation."""
        self._tags = self._validate_tags(value)

    @property
    def subtasks(self) -> list[dict[str, Any]]:
        """Return the validated subtask records."""
        return self._subtasks

    @subtasks.setter
    def subtasks(self, value: list[dict[str, Any]] | None) -> None:
        """Set the subtasks after validation."""
        self._subtasks = self._validate_subtasks(value)

    @property
    def recurrence(self) -> TaskRecurrence:
        """Return the recurring-task schedule."""
        return self._recurrence

    @recurrence.setter
    def recurrence(self, value: str | TaskRecurrence) -> None:
        """Set the recurring-task schedule after validation."""
        validated = self._validate_recurrence(value)
        if validated != TaskRecurrence.NONE and not self.due_date:
            raise ValueError("recurring tasks require a due_date")
        self._recurrence = validated

    def mark_completed(self) -> None:
        """Mark task status as Done and set subtasks to completed."""
        self.status = TaskStatus.DONE
        for subtask in self.subtasks:
            subtask["completed"] = True

    def advance_recurrence(self) -> bool:
        """Move a recurring task to its next due date after completion."""
        if self.recurrence == TaskRecurrence.NONE or not self.due_date:
            return False
        current = date.fromisoformat(self.due_date)
        if self.recurrence == TaskRecurrence.DAILY:
            next_date = current + timedelta(days=1)
        elif self.recurrence == TaskRecurrence.WEEKLY:
            next_date = current + timedelta(days=7)
        else:
            next_month = current.month % 12 + 1
            next_year = current.year + (current.month // 12)
            next_day = min(current.day, calendar.monthrange(next_year, next_month)[1])
            next_date = current.replace(year=next_year, month=next_month, day=next_day)
        self.due_date = next_date.isoformat()
        self.status = TaskStatus.TO_DO
        self.subtasks = [
            {"title": subtask["title"], "completed": False} for subtask in self.subtasks
        ]
        return True

    def to_dict(self) -> dict[str, Any]:
        """Convert task instance attributes to a dictionary payload."""
        return {
            "task_id": self.task_id,
            "title": self.title,
            "priority": self.priority.value,
            "status": self.status.value,
            "due_date": self.due_date,
            "tags": self.tags,
            "subtasks": self.subtasks,
            "recurrence": self.recurrence.value,
        }

    def to_db_row(self) -> tuple[str, str, str, str, str, str, str, str]:
        """Convert task attributes to an SQL row tuple for database insertion."""
        tags_str: str = ",".join(self.tags)
        subtasks_json: str = json.dumps(self.subtasks)
        return (
            self.task_id,
            self.title,
            self.priority.value,
            self.status.value,
            self.due_date,
            tags_str,
            subtasks_json,
            self.recurrence.value,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        """Instantiate a Task instance from a dictionary payload."""
        return cls(
            task_id=data.get("task_id"),
            title=data.get("title", ""),
            priority=data.get("priority", DEFAULT_PRIORITY),
            status=data.get("status", DEFAULT_STATUS),
            due_date=data.get("due_date", ""),
            tags=data.get("tags", []),
            subtasks=data.get("subtasks", []),
            recurrence=data.get("recurrence", DEFAULT_RECURRENCE),
        )

    @classmethod
    def from_db_row(cls, row: tuple[Any, ...]) -> "Task":
        """Instantiate a Task instance directly from an SQL database query row."""
        task_id, title, priority, status, due_date = (
            row[0],
            row[1],
            row[2],
            row[3],
            row[4],
        )

        tags: list[str] = []
        if len(row) > 5 and row[5]:
            tags = [t.strip() for t in str(row[5]).split(",") if t.strip()]

        subtasks: list[dict[str, Any]] = []
        if len(row) > 6 and row[6]:
            try:
                decoded_subtasks = json.loads(row[6])
                if isinstance(decoded_subtasks, list):
                    subtasks = decoded_subtasks
            except (json.JSONDecodeError, TypeError):
                subtasks = []

        recurrence = str(row[7]) if len(row) > 7 and row[7] else DEFAULT_RECURRENCE

        return cls(
            task_id=str(task_id),
            title=str(title),
            priority=str(priority),
            status=str(status),
            due_date=str(due_date) if due_date else "",
            tags=tags,
            subtasks=subtasks,
            recurrence=recurrence,
        )
