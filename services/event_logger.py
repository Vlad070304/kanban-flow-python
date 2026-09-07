"""
services/event_logger.py
Append-only JSON logger for tracking board lifecycle events and completion history.
"""

from datetime import datetime
import json
import os


class EventLogger:
    """Handles persistent event logging for historical board operations."""

    LOG_FILE = "kanban_events.json"

    @classmethod
    def log_event(cls, event_type: str, task_title: str, extra_data: dict = None):
        """Appends a new event record to the log file."""
        events = cls.load_events()

        payload = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "task_title": task_title,
        }
        if extra_data:
            payload.update(extra_data)

        events.append(payload)

        try:
            with open(cls.LOG_FILE, "w", encoding="utf-8") as file:
                json.dump(events, file, indent=4)
        except IOError as err:
            print(f"Error writing event log: {err}")

    @classmethod
    def load_events(cls) -> list:
        """Reads historical log events from disk."""
        if not os.path.exists(cls.LOG_FILE):
            return []

        try:
            with open(cls.LOG_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except (IOError, json.JSONDecodeError) as err:
            print(f"Error reading event log: {err}")
            return []
