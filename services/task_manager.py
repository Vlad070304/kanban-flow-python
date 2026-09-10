"""
services/task_manager.py
Service handling task collection management and SQLite persistence.
"""

import os
import sqlite3
from typing import List, Optional

from models.task import Task


class TaskManager:
    """Manages CRUD operations and database persistence for Task objects."""

    def __init__(self, db_path: str = "kanban_data.db") -> None:
        """Initializes TaskManager with target SQLite database path."""
        self.db_path: str = db_path
        self.tasks: List[Task] = []
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Returns a configured SQLite database connection."""
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        """Creates tasks table if it does not already exist."""
        query = """
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL,
            due_date TEXT,
            tags TEXT
        );
        """
        try:
            with self._get_connection() as conn:
                conn.execute(query)
                conn.commit()
        except sqlite3.Error:
            pass

    def add_task(
        self,
        title: str,
        priority: str = "LOW",
        status: str = "To Do",
        due_date: str = "",
        tags: Optional[List[str]] = None
    ) -> Task:
        """Creates and persists a new task instance in SQLite."""
        task_id = f"task-{len(self.tasks) + 1000}"
        task = Task(
            task_id=task_id,
            title=title,
            priority=priority,
            status=status,
            due_date=due_date,
            tags=tags if tags else []
        )
        self.tasks.append(task)
        self.save_to_file()
        return task

    def remove_task(self, task_id: str) -> bool:
        """Removes a task from local state and SQLite storage by ID."""
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
        """Removes all tasks marked with status 'Done' from memory and SQLite."""
        self.tasks = [t for t in self.tasks if t.status != "Done"]
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM tasks WHERE status = 'Done';")
                conn.commit()
        except sqlite3.Error:
            pass

    def save_to_file(self) -> bool:
        """Saves current in-memory task collection to SQLite database."""
        query = """
        INSERT OR REPLACE INTO tasks (
            task_id, title, priority, status, due_date, tags
        ) VALUES (?, ?, ?, ?, ?, ?);
        """
        try:
            with self._get_connection() as conn:
                conn.executemany(query, [t.to_db_row() for t in self.tasks])
                conn.commit()
            return True
        except sqlite3.Error:
            return False

    def load_from_file(self) -> List[Task]:
        """Loads all tasks from SQLite database into memory."""
        if not os.path.exists(self.db_path):
            self.tasks = []
            return self.tasks

        try:
            with self._get_connection() as conn:
                query = (
                    "SELECT task_id, title, priority, status, due_date, tags "
                    "FROM tasks;"
                )
                cursor = conn.execute(query)
                rows = cursor.fetchall()
                self.tasks = [Task.from_db_row(row) for row in rows]
                return self.tasks
        except sqlite3.Error:
            self.tasks = []
            return self.tasks
