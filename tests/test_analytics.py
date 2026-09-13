import csv
import os
import tempfile
import unittest

from gui.analytics import export_analytics_csv


class TestAnalyticsExport(unittest.TestCase):
    """Tests for analytics CSV export behavior."""

    def test_exports_activity_records(self) -> None:
        """Verifies analytics records are exported with safe comma handling."""
        logs = [
            {
                "timestamp": "2026-09-13 10:00:00",
                "event": "TASK_COMPLETED",
                "target": "Task, one",
                "details": {"priority": "HIGH"},
            }
        ]

        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "analytics.csv")
            count = export_analytics_csv(logs, path)

            with open(path, newline="", encoding="utf-8") as file:
                rows = list(csv.reader(file))

        self.assertEqual(count, 1)
        self.assertEqual(rows[0], ["Timestamp", "Event", "Target", "Details"])
        self.assertEqual(rows[1][2], "Task one")
        self.assertEqual(rows[1][3], "{'priority': 'HIGH'}")


if __name__ == "__main__":
    unittest.main()
