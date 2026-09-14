"""Tests for task reminder notification behavior."""

import unittest
from datetime import date
from unittest.mock import patch

from models.task import Task
from services.notification_service import (
    clear_reminder_state,
    notify_due_tasks,
    send_notification,
)


class TestNotificationService(unittest.TestCase):
    """Tests for deduplicated task reminder notifications."""

    def setUp(self) -> None:
        clear_reminder_state()

    def tearDown(self) -> None:
        clear_reminder_state()

    @patch("services.notification_service.send_notification")
    def test_notifies_once_per_day(
        self, mock_send_notification: unittest.mock.Mock
    ) -> None:
        """A repeated reminder check does not duplicate the native notification."""
        tasks = [Task(task_id="task-1", title="Submit report", due_date="2026-09-13")]

        first_count = notify_due_tasks(tasks, date(2026, 9, 13))
        second_count = notify_due_tasks(tasks, date(2026, 9, 13))

        self.assertEqual(first_count, 1)
        self.assertEqual(second_count, 0)
        mock_send_notification.assert_called_once_with(
            title="Task Reminder",
            message="1 task(s) due or overdue: Submit report",
        )

    @patch("services.notification_service.send_notification")
    def test_notifies_again_on_next_day(
        self, mock_send_notification: unittest.mock.Mock
    ) -> None:
        """A task can be reminded again on a later day while overdue."""
        task = Task(task_id="task-1", title="Submit report")

        notify_due_tasks([task], date(2026, 9, 13))
        notify_due_tasks([task], date(2026, 9, 14))

        self.assertEqual(mock_send_notification.call_count, 2)

    @patch("services.notification_service._PLYER_AVAILABLE", True)
    @patch("services.notification_service.notification", create=True)
    def test_send_notification_delegates_to_plyer(
        self, notification: unittest.mock.Mock
    ) -> None:
        """Verifies native notification arguments are passed to plyer."""
        send_notification("Title", "Message")

        notification.notify.assert_called_once_with(
            title="Title",
            message="Message",
            app_name="Task Manager Suite",
            timeout=6,
        )


if __name__ == "__main__":
    unittest.main()
