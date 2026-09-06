import json
import os
from typing import List
from models.task import Task


class TaskManager:
    #Manages task lifecycle, filtering, and JSON serialization.

    def __init__(self, storage_file: str = "kanban_data.json"):
        #Initialize manager with dynamic or default storage path.
        self.storage_file = storage_file
        self.tasks: List[Task] = []

    def add_task(self, title: str, priority: str = "LOW", status: str = "To Do") -> Task:
        #Create and store a new task model.
        task = Task(title=title, priority=priority, status=status)
        self.tasks.append(task)
        return task

    def remove_task(self, task_id: str) -> None:
        #Remove task matching target ID.
        self.tasks = [t for t in self.tasks if t.task_id != task_id]

    def clear_done(self) -> None:
        #Remove all completed tasks.
        self.tasks = [t for t in self.tasks if t.status != "Done"]

    def save_to_file(self) -> None:
        #Serialize current task models to JSON.
        data = [t.to_dict() for t in self.tasks]
        try:
            with open(self.storage_file, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)
        except (IOError, TypeError) as err:
            print(f"Error saving task data: {err}")

    def load_from_file(self) -> List[Task]:
        #Deserialize tasks from JSON storage.
        if not os.path.exists(self.storage_file):
            self.tasks = []
            return self.tasks

        try:
            with open(self.storage_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                self.tasks = [Task.from_dict(item) for item in data]
        except (IOError, json.JSONDecodeError) as err:
            print(f"Error loading task data: {err}")
            self.tasks = []

        return self.tasks