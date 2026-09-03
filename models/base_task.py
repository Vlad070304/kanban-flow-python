from abc import ABC, abstractmethod

class BaseTask(ABC):
    total_tasks_created = 0  # Class Variable

    def __init__(self, title: str, description: str):
        BaseTask.total_tasks_created += 1
        self.task_id = BaseTask.total_tasks_created
        self.title = title
        self.description = description
        self.status = "To Do"

    def set_status(self, status: str):
        self.status = status
        return self  

    @abstractmethod
    def get_summary(self) -> str:
        pass


class TimedTask(BaseTask):
    def __init__(self, title: str, description: str, duration_mins: int):
        super().__init__(title, description)
        self.duration_mins = duration_mins

    def get_summary(self) -> str:
        return f"[Timed: {self.duration_mins}m] #{self.task_id} {self.title} ({self.status})"


class RecurringTask(BaseTask):
    def __init__(self, title: str, description: str, frequency: str):
        super().__init__(title, description)
        self.frequency = frequency

    def get_summary(self) -> str:
        return f"[Repeat: {self.frequency}] #{self.task_id} {self.title} ({self.status})"