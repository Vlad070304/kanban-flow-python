"""
services/event_logger.py
Service for appending and reading JSON event logs.
"""

import datetime
import json
import os
from typing import Any, Dict, List


class EventLogger:
    """Handles structured application event logging."""

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
