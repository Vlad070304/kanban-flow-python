"""Headless release smoke test for core application workflows."""

import csv
import json
import tempfile
from pathlib import Path

from models.task import TaskRecurrence
from services.event_logger import EventLogger
from services.task_manager import TaskManager


def run_smoke_test() -> None:
    """Exercise persistence, import/export, recurrence, and analytics paths."""
    with tempfile.TemporaryDirectory(prefix="kanban-release-smoke-") as directory:
        root = Path(directory)
        EventLogger.LOG_FILE = str(root / "events.json")

        manager = TaskManager(db_path=str(root / "tasks.db"))
        task = manager.add_task(
            "Release smoke task",
            due_date="2026-09-14",
            recurrence=TaskRecurrence.DAILY,
            tags=["release"],
        )
        if task.recurrence != TaskRecurrence.DAILY:
            raise AssertionError("Recurring task metadata was not persisted in memory")

        backup_path = root / "backup.json"
        if not manager.export_backup(str(backup_path)):
            raise AssertionError("JSON backup export failed")

        restored_manager = TaskManager(db_path=str(root / "restored.db"))
        if not restored_manager.restore_backup(str(backup_path)):
            raise AssertionError("JSON backup restore failed")
        restored_task = restored_manager.tasks[0]
        if restored_task.recurrence != TaskRecurrence.DAILY:
            raise AssertionError("Recurring task metadata was lost during restore")

        csv_path = root / "tasks.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "TaskId",
                    "Title",
                    "Status",
                    "Priority",
                    "DueDate",
                    "Tags",
                    "Recurrence",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "TaskId": "csv-task",
                    "Title": "CSV import task",
                    "Status": "To Do",
                    "Priority": "HIGH",
                    "DueDate": "2026-09-15",
                    "Tags": "release;csv",
                    "Recurrence": "Weekly",
                }
            )

        if not restored_manager.import_tasks(str(csv_path)):
            raise AssertionError("CSV task import failed")
        if not any(task.task_id == "csv-task" for task in restored_manager.tasks):
            raise AssertionError("CSV task was not added to the task collection")

        EventLogger.log_event(
            "FOCUS_SESSION_COMPLETED",
            "25m Session",
            {"duration_min": 25, "task_id": task.task_id},
        )
        summary = EventLogger.get_analytics_summary()
        if summary["focus_by_task"][task.task_id] != 25:
            raise AssertionError("Focus analytics did not track the task")

        payload = json.loads(backup_path.read_text(encoding="utf-8"))
        if payload[0]["task_id"] != task.task_id:
            raise AssertionError("Backup payload is missing the original task")


if __name__ == "__main__":
    run_smoke_test()
    print("Release smoke test passed.")
