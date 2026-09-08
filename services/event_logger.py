"""
services/event_logger.py
Service for appending, reading, and aggregating JSON event logs.
"""

from collections import defaultdict
import datetime
import json
import os
from typing import Any, Dict, List


class EventLogger:
    """Handles structured application event logging and data aggregation."""

    LOG_FILE = "event_log.json"

    @classmethod
    def log_event(cls, event_type: str, target: str, details: Dict[str, Any]):
        """Appends a timestamped event entry to the log file."""
        entry = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "event": event_type,
            "target": target,
            "details": details
        }

        logs = cls.read_logs()
        logs.append(entry)

        try:
            with open(cls.LOG_FILE, "w", encoding="utf-8") as file:
                json.dump(logs, file, indent=4)
        except (IOError, TypeError) as err:
            print(f"Error saving log event: {err}")

    @classmethod
    def read_logs(cls) -> List[Dict[str, Any]]:
        """Reads and returns all logged events."""
        if not os.path.exists(cls.LOG_FILE):
            return []

        try:
            with open(cls.LOG_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except (IOError, json.JSONDecodeError):
            return []

    @classmethod
    def get_analytics_summary(cls) -> Dict[str, Any]:
        """Aggregates task completions, focus time, and daily trend metrics from event logs."""
        logs = cls.read_logs()

        completed_tasks = [
            log for log in logs if log.get("event") == "TASK_COMPLETED"
        ]
        completed_count = len(completed_tasks)

        focus_sessions = [
            log for log in logs if log.get("event") == "FOCUS_SESSION_COMPLETED"
        ]
        focus_session_count = len(focus_sessions)

        total_focus_minutes = sum(
            session.get("details", {}).get("duration_min", 0)
            for session in focus_sessions
        )

        daily_tasks = defaultdict(int)
        daily_focus = defaultdict(int)

        for log in logs:
            ts_str = log.get("timestamp", "")
            if not ts_str:
                continue
            date_key = ts_str.split(" ")[0]

            if log.get("event") == "TASK_COMPLETED":
                daily_tasks[date_key] += 1
            elif log.get("event") == "FOCUS_SESSION_COMPLETED":
                dur = log.get("details", {}).get("duration_min", 0)
                daily_focus[date_key] += dur

        return {
            "completed_count": completed_count,
            "focus_session_count": focus_session_count,
            "total_focus_minutes": total_focus_minutes,
            "daily_tasks": daily_tasks,
            "daily_focus": daily_focus,
            "logs": logs
        }
