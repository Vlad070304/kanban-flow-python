"""
services/task_manager.py
Service handling task collection management, JSON persistence, and backups.
"""

import json
import os
from typing import List, Optional

from models.task import Task


class TaskManager:
    """Manages CRUD operations, persistence, and backup options for Task objects."""

    def __init__(self, filepath: str = "kanban_data.json") -> None:
        self.filepath: str = filepath
        self.tasks: List[Task] = []
<<<<<<< Updated upstream
=======
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Returns a configured SQLite database connection."""
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        """Creates tasks table and ensures subtasks column exists."""
        create_query = """
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL,
            due_date TEXT,
            tags TEXT,
            subtasks TEXT
        );
        """
        try:
            with self._get_connection() as conn:
                conn.execute(create_query)
                # Auto-migrate existing database schema if subtasks column is missing
                cursor = conn.execute("PRAGMA table_info(tasks);")
                columns = [column[1] for column in cursor.fetchall()]
                if "subtasks" not in columns:
                    conn.execute("ALTER TABLE tasks ADD COLUMN subtasks TEXT;")
                conn.commit()
        except sqlite3.Error:
            pass
>>>>>>> Stashed changes

    def add_task(
        self,
        title: str,
        priority: str = "LOW",
        status: str = "To Do",
        due_date: str = "",
        tags: Optional[List[str]] = None,
        subtasks: Optional[List[dict]] = None
    ) -> Task:
        """Creates and adds a new task instance to the collection."""
        task_id = f"task-{len(self.tasks) + 1000}"
        task = Task(
            task_id=task_id,
            title=title,
            priority=priority,
            status=status,
            due_date=due_date,
            tags=tags if tags else [],
            subtasks=subtasks if subtasks else []
        )
        self.tasks.append(task)
        return task

    def remove_task(self, task_id: str) -> bool:
        """Removes a task from the collection matching the given task_id."""
        initial_count = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.task_id != task_id]
<<<<<<< Updated upstream
        return len(self.tasks) < initial_count
=======
        if len(self.tasks) < initial_count:
            try:
                with self._get_connection() as conn:
                    conn.execute(
                        "DELETE FROM tasks WHERE task_id = ?;", (task_id,)
                    )
                    conn.commit()
                return True
            except sqlite3.Error:
                return False
        return False
>>>>>>> Stashed changes

    def clear_done(self) -> None:
        """Removes all tasks currently marked with status 'Done'."""
        self.tasks = [t for t in self.tasks if t.status != "Done"]

    def save_to_file(self) -> bool:
<<<<<<< Updated upstream
        """Saves current task collection to primary storage file."""
=======
        """Saves current in-memory task collection to SQLite database."""
        query = """
        INSERT OR REPLACE INTO tasks (
            task_id, title, priority, status, due_date, tags, subtasks
        )
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """
>>>>>>> Stashed changes
        try:
            data = [t.to_dict() for t in self.tasks]
            with open(self.filepath, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)
            return True
        except OSError:
            return False

    def load_from_file(self) -> List[Task]:
        """Loads task collection from primary storage file."""
        if not os.path.exists(self.filepath):
            self.tasks = []
            return self.tasks

        try:
<<<<<<< Updated upstream
            with open(self.filepath, "r", encoding="utf-8") as file:
                data = json.load(file)
            self.tasks = [Task.from_dict(item) for item in data]
            return self.tasks
        except (OSError, json.JSONDecodeError, KeyError):
=======
            with self._get_connection() as conn:
                query = (
                    "SELECT task_id, title, priority, status, due_date, "
                    "tags, subtasks FROM tasks;"
                )
                cursor = conn.execute(query)
                rows = cursor.fetchall()
                self.tasks = [Task.from_db_row(row) for row in rows]
                return self.tasks
        except sqlite3.Error:
>>>>>>> Stashed changes
            self.tasks = []
            return self.tasks

    def export_backup(self, target_filepath: str) -> bool:
        """Exports current task collection to a user-specified JSON backup file."""
        try:
            data = [task.to_dict() for task in self.tasks]
            with open(target_filepath, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)
            return True
        except (OSError, TypeError):
            return False

    def restore_backup(self, source_filepath: str) -> bool:
        """Restores tasks from a backup JSON file and persists to primary storage."""
        try:
            with open(source_filepath, "r", encoding="utf-8") as file:
                data = json.load(file)
            self.tasks = [Task.from_dict(item) for item in data]
            self.save_to_file()
            return True
        except (OSError, json.JSONDecodeError, KeyError):
            return False
