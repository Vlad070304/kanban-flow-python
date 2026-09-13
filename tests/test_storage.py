"""
tests/test_storage.py
Unit tests for EventLogger storage and analytics aggregation methods.
"""

import json
import os
import unittest

from services.event_logger import EventLogger


class TestEventLogger(unittest.TestCase):
    """Test suite for EventLogger class functionality."""

    def setUp(self):
        """Redirects EventLogger log file to a temporary file for test isolation."""
        self.test_log_file = "test_event_log.json"
        EventLogger.LOG_FILE = self.test_log_file

    def tearDown(self):
        """Cleans up temporary log file after each test execution."""
        if os.path.exists(self.test_log_file):
            os.remove(self.test_log_file)

    def test_read_empty_logs(self):
        """Verifies empty list returned when log file does not exist."""
        logs = EventLogger.read_logs()
        self.assertEqual(logs, [])

    def test_log_event_and_read(self):
        """Verifies events are correctly written to file and read back."""
        EventLogger.log_event("TASK_COMPLETED", "Test Task", {"priority": "HIGH"})
        logs = EventLogger.read_logs()

        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["event"], "TASK_COMPLETED")
        self.assertEqual(logs[0]["target"], "Test Task")
        self.assertEqual(logs[0]["details"]["priority"], "HIGH")
        self.assertIn("timestamp", logs[0])

    def test_get_analytics_summary(self):
        """Verifies analytics summary calculation for tasks and focus sessions."""
        mock_logs = [
            {
                "timestamp": "2026-09-01 10:00:00",
                "event": "TASK_COMPLETED",
                "target": "Task 1",
                "details": {"priority": "LOW"},
            },
            {
                "timestamp": "2026-09-01 11:00:00",
                "event": "FOCUS_SESSION_COMPLETED",
                "target": "25m Session",
                "details": {"duration_min": 25},
            },
            {
                "timestamp": "2026-09-02 14:00:00",
                "event": "FOCUS_SESSION_COMPLETED",
                "target": "15m Session",
                "details": {"duration_min": 15},
            },
        ]

        with open(self.test_log_file, "w", encoding="utf-8") as file:
            json.dump(mock_logs, file)

        summary = EventLogger.get_analytics_summary()

        self.assertEqual(summary["completed_count"], 1)
        self.assertEqual(summary["focus_session_count"], 2)
        self.assertEqual(summary["total_focus_minutes"], 40)
        self.assertEqual(summary["daily_tasks"]["2026-09-01"], 1)
        self.assertEqual(summary["daily_focus"]["2026-09-01"], 25)
        self.assertEqual(summary["daily_focus"]["2026-09-02"], 15)
        self.assertEqual(len(summary["logs"]), 3)


if __name__ == "__main__":
    unittest.main()
