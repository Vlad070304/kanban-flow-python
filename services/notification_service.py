"""Service handling cross-platform desktop notifications via plyer."""

import logging
from collections.abc import Sequence
from datetime import date

from models.task import Task

LOGGER: logging.Logger = logging.getLogger(__name__)

try:
    from plyer import notification

    _PLYER_AVAILABLE = True
except ImportError:
    _PLYER_AVAILABLE = False


def send_notification(title: str, message: str) -> None:
    """Trigger a native desktop notification if plyer is available."""
    if _PLYER_AVAILABLE:
        try:
            notification.notify(
                title=title, message=message, app_name="Task Manager Suite", timeout=6
            )
        except Exception as err:  # pylint: disable=broad-exception-caught
            LOGGER.error("Failed to send desktop notification: %s", err)
    else:
        LOGGER.warning("plyer package not installed. Skipping desktop notification.")


_REMINDER_KEYS: set[tuple[str, str]] = set()


def notify_due_tasks(tasks: Sequence[Task], reminder_date: date | None = None) -> int:
    """Notify once per day about the supplied due or overdue tasks."""
    if not tasks:
        return 0

    today = reminder_date or date.today()
    new_tasks = [
        task
        for task in tasks
        if (task.task_id, today.isoformat()) not in _REMINDER_KEYS
    ]
    if not new_tasks:
        return 0

    for task in new_tasks:
        _REMINDER_KEYS.add((task.task_id, today.isoformat()))

    titles = ", ".join(task.title for task in new_tasks[:3])
    extra = f" (+{len(new_tasks) - 3} more)" if len(new_tasks) > 3 else ""
    send_notification(
        title="Task Reminder",
        message=f"{len(new_tasks)} task(s) due or overdue: {titles}{extra}",
    )
    return len(new_tasks)


def clear_reminder_state() -> None:
    """Clear reminder state, primarily for tests and application resets."""
    _REMINDER_KEYS.clear()
