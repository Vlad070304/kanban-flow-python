from dataclasses import dataclass, field
import uuid


@dataclass
class Task:
    #Represents an individual Kanban task card.
    title: str
    priority: str = "LOW"
    status: str = "To Do"
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict:
        #Serialize task instance to dictionary format.
        return {
            "task_id": self.task_id,
            "title": self.title,
            "priority": self.priority,
            "status": self.status
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        #Deserialize dictionary data into a Task instance.
        return cls(
            title=data.get("title", ""),
            priority=data.get("priority", "LOW"),
            status=data.get("status", "To Do"),
            task_id=data.get("task_id", str(uuid.uuid4()))
        )