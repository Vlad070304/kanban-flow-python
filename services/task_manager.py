"""Services handling task collection management, SQLite persistence, and backups."""

import datetime
import json
import logging
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

from models.task import Task
from services.storage_errors import StorageError
from services.storage_paths import get_app_data_path

LOGGER = logging.getLogger(__name__)


class TaskManager:
    """Manage CRUD operations, SQLite persistence, and task backups."""

    CURRENT_SCHEMA_VERSION = 1

    def __init__(self, db_path: str | None = None) -> None:
        """Initialize TaskManager with an SQLite database connection target."""
        self.db_path: str = db_path or get_app_data_path("kanban_data.db")
        self.tasks: list[Task] = []
        self._init_db()

    @property
    def filepath(self) -> str:
        """Return the database file path for compatibility with tests."""
        return self.db_path

    def _get_connection(self) -> sqlite3.Connection:
        """Return a configured SQLite database connection."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        """Initialize the database and apply all pending schema migrations."""
        try:
            with closing(self._get_connection()) as conn, conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        version INTEGER PRIMARY KEY,
                        applied_at TEXT NOT NULL
                    );
                    """
                )
                applied_versions = {
                    row[0]
                    for row in conn.execute(
                        "SELECT version FROM schema_migrations ORDER BY version;"
                    )
                }

                migrations = {1: self._migration_001_initial_schema}
                for version in range(1, self.CURRENT_SCHEMA_VERSION + 1):
                    if version in applied_versions:
                        continue
                    migrations[version](conn)
                    conn.execute(
                        """
                        INSERT INTO schema_migrations (version, applied_at)
                        VALUES (?, ?);
                        """,
                        (
                            version,
                            datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        ),
                    )
        except (OSError, sqlite3.Error) as err:
            LOGGER.exception("Database initialization failed for %s", self.db_path)
            raise StorageError("initialize database", self.db_path, err) from err

    @staticmethod
    def _migration_001_initial_schema(conn: sqlite3.Connection) -> None:
        """Create the task table and upgrade legacy databases with subtasks."""
        conn.execute(
            """
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
        )
        columns = {column[1] for column in conn.execute("PRAGMA table_info(tasks);")}
        if "subtasks" not in columns:
            conn.execute("ALTER TABLE tasks ADD COLUMN subtasks TEXT;")

    def add_task(
        self,
        title: str,
        priority: str = "LOW",
        status: str = "To Do",
        due_date: str = "",
        tags: list[str] | None = None,
        subtasks: list[dict[str, Any]] | None = None,
    ) -> Task:
        """Create and add a new task instance to the collection."""
        task = Task(
            title=title,
            priority=priority,
            status=status,
            due_date=due_date,
            tags=tags if tags else [],
            subtasks=subtasks if subtasks else [],
        )
        self.tasks.append(task)
        self.save_to_file()
        return task

    def remove_task(self, task_id: str) -> bool:
        """Remove a task matching task_id from memory and database."""
        initial_count = len(self.tasks)
        updated_tasks = [t for t in self.tasks if t.task_id != task_id]
        if len(updated_tasks) < initial_count:
            try:
                with closing(self._get_connection()) as conn:
                    with conn:
                        conn.execute("DELETE FROM tasks WHERE task_id = ?;", (task_id,))
                self.tasks = updated_tasks
                return True
            except (OSError, sqlite3.Error):
                LOGGER.exception("Delete task failed for %s", self.db_path)
                return False
        return False

    def clear_done(self) -> bool:
        """Remove all completed tasks with status 'Done' from memory and database."""
        done_ids = [t.task_id for t in self.tasks if t.status == "Done"]
        try:
            with closing(self._get_connection()) as conn:
                with conn:
                    if done_ids:
                        placeholders = ",".join(["?"] * len(done_ids))
                        conn.execute(
                            f"DELETE FROM tasks WHERE task_id IN ({placeholders});",
                            done_ids,
                        )
            self.tasks = [t for t in self.tasks if t.status != "Done"]
            return True
        except (OSError, sqlite3.Error):
            LOGGER.exception("Clear completed tasks failed for %s", self.db_path)
            return False

    def get_due_or_overdue_tasks(self) -> list[Task]:
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
            with closing(self._get_connection()) as conn:
                with conn:
                    for task in self.tasks:
                        conn.execute(query, task.to_db_row())
            return True
        except (OSError, sqlite3.Error):
            LOGGER.exception("Save tasks failed for %s", self.db_path)
            return False

    def load_from_file(self) -> list[Task]:
        """Load task collection directly from the SQLite database."""
        try:
            with closing(self._get_connection()) as conn:
                query = (
                    "SELECT task_id, title, priority, status, due_date, "
                    "tags, subtasks FROM tasks;"
                )
                cursor = conn.execute(query)
                rows = cursor.fetchall()
                self.tasks = [Task.from_db_row(row) for row in rows]
                return self.tasks
        except (OSError, sqlite3.Error):
            LOGGER.exception("Load tasks failed for %s", self.db_path)
            return self.tasks

    def export_backup(self, target_filepath: str) -> bool:
        """Export current task collection to a user-specified JSON backup file."""
        try:
            data = [task.to_dict() for task in self.tasks]
            with open(target_filepath, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)
            return True
        except (OSError, TypeError):
            LOGGER.exception("Export backup failed for %s", target_filepath)
            return False

    def restore_backup(self, source_filepath: str) -> bool:
        """Replace current tasks with a validated JSON backup atomically."""
        try:
            with open(source_filepath, encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, list) or not all(
                isinstance(item, dict) for item in data
            ):
                LOGGER.warning(
                    "Restore backup rejected invalid structure: %s", source_filepath
                )
                return False

            restored_tasks = [Task.from_dict(item) for item in data]
            query = """
            INSERT INTO tasks (
                task_id, title, priority, status, due_date, tags, subtasks
            )
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """
            with closing(self._get_connection()) as conn:
                with conn:
                    conn.execute("DELETE FROM tasks;")
                    conn.executemany(
                        query, (task.to_db_row() for task in restored_tasks)
                    )

            self.tasks = restored_tasks
            return True
        except (OSError, json.JSONDecodeError, sqlite3.Error, TypeError, ValueError):
            LOGGER.exception("Restore backup failed for %s", source_filepath)
            return False
