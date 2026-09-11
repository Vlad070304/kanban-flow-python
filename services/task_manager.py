"""Services handling task collection management, SQLite persistence, and backups."""

import datetime
import json
import sqlite3
from typing import Any, Dict, List, Optional

from models.task import Task


class TaskManager:
    """Manages CRUD operations, SQLite persistence, and backup options for Task objects."""

    def __init__(self, db_path: str = "kanban_data.db") -> None:
        """Initialize TaskManager with an SQLite database connection target."""
        self.db_path: str = db_path
        self.tasks: List[Task] = []
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Return a configured SQLite database connection."""
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        """Create tasks table and ensure subtasks column exists."""
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
                cursor = conn.execute("PRAGMA table_info(tasks);")
                columns = [column[1] for column in cursor.fetchall()]
                if "subtasks" not in columns:
                    conn.execute("ALTER TABLE tasks ADD COLUMN subtasks TEXT;")
                conn.commit()
        except sqlite3.Error:
            pass

    def add_task(
        self,
        title: str,
        priority: str = "LOW",
        status: str = "To Do",
        due_date: str = "",
        tags: Optional[List[str]] = None,
        subtasks: Optional[List[Dict[str, Any]]] = None
    ) -> Task:
        """Create and add a new task instance to the collection."""
        task = Task(
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
        """Remove a task matching task_id from memory and database."""
        initial_count = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.task_id != task_id]
        if len(self.tasks) < initial_count:
            try:
                with self._get_connection() as conn:
                    conn.execute("DELETE FROM tasks WHERE task_id = ?;", (task_id,))
                    conn.commit()
                return True
            except sqlite3.Error:
                return False
        return False

    def clear_done(self) -> None:
        """Remove all completed tasks with status 'Done' from memory and database."""
        done_ids = [t.task_id for t in self.tasks if t.status == "Done"]
        self.tasks = [t for t in self.tasks if t.status != "Done"]
        if done_ids:
            try:
                with self._get_connection() as conn:
                    placeholders = ",".join(["?"] * len(done_ids))
                    conn.execute(
                        f"DELETE FROM tasks WHERE task_id IN ({placeholders});", done_ids
                    )
                    conn.commit()
            except sqlite3.Error:
                pass

    def get_due_or_overdue_tasks(self) -> List[Task]:
        """Return all incomplete tasks whose due date is today or earlier."""
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        due_tasks = []
        for task in self.tasks:
            if task.status != "Done" and task.due_date:
                if task.due_date <= today_str:
                    due_tasks.append(task)
        return due_tasks

    def save_to_file(self) -> bool:
        """Save current in-memory task collection to the SQLite database."""
        query = """
        INSERT OR REPLACE INTO tasks (
            task_id, title, priority, status, due_date, tags, subtasks
        )
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        try:
            with self._get_connection() as conn:
                for task in self.tasks:
                    conn.execute(query, task.to_db_row())
                conn.commit()
            return True
        except sqlite3.Error:
            return False

    def load_from_file(self) -> List[Task]:
        """Load task collection directly from the SQLite database."""
        try:
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
            self.tasks = []
            return self.tasks

    def export_backup(self, target_filepath: str) -> bool:
        """Export current task collection to a user-specified JSON backup file."""
        try:
            data = [task.to_dict() for task in self.tasks]
            with open(target_filepath, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)
            return True
        except (OSError, TypeError):
            return False

    def restore_backup(self, source_filepath: str) -> bool:
        """Restore tasks from a JSON backup file and persist to primary SQLite storage."""
        try:
            with open(source_filepath, "r", encoding="utf-8") as file:
                data = json.load(file)
            self.tasks = [Task.from_dict(item) for item in data]
            self.save_to_file()
            return True
        except (OSError, json.JSONDecodeError, KeyError):
            return False
