"""Focus timer behavior shared by the Kanban board."""

import threading
import time
from tkinter import messagebox
from typing import Any

import config
from gui.dialogs.focus_timer_dialog import FocusTimerDialog
from services.event_logger import EventLogger
from services.notification_service import send_notification


class FocusTimerMixin:
    """Provide focus timer dialog, lifecycle, and rendering behavior."""

    def open_timer_dialog(self: Any) -> None:
        """Open focus timer modal window."""
        FocusTimerDialog(self.parent, self)

    def start_focus_timer(
        self: Any, minutes: int = 25, task_id: str | None = None
    ) -> None:
        """Start a focus timer countdown worker thread."""
        if self._timer_running:
            messagebox.showwarning("Timer Running", "A focus timer is already active!")
            return

        self._timer_running = True
        self._focus_task_id = task_id
        focus_task = next(
            (task for task in self.task_manager.tasks if task.task_id == task_id),
            None,
        )
        task_title = focus_task.title if focus_task else "Unassigned"
        total_seconds: int = minutes * 60
        EventLogger.log_event(
            "FOCUS_SESSION_STARTED",
            f"{minutes}m Session",
            {
                "duration_min": minutes,
                "task_id": task_id,
                "task_title": task_title,
            },
        )

        def timer_worker() -> None:
            remaining: int = total_seconds
            while remaining > 0 and self._timer_running:
                mins, secs = divmod(remaining, 60)
                time_str: str = f"Focus Timer: {mins:02d}:{secs:02d} remaining"
                self.after(
                    0,
                    lambda t=time_str: self._draw_timer_canvas(t),
                )
                time.sleep(1)
                remaining -= 1

            if self._timer_running:
                self._timer_running = False
                self.after(0, lambda: self._on_timer_completed(minutes))

        threading.Thread(target=timer_worker, daemon=True).start()

    def cancel_focus_timer(self: Any) -> None:
        """Cancel current focus timer thread."""
        if self._timer_running:
            self._timer_running = False
            EventLogger.log_event(
                "FOCUS_SESSION_CANCELLED",
                "Focus Session",
                {"task_id": self._focus_task_id},
            )
            self.update_progress_bar()
            messagebox.showinfo("Timer Cancelled", "Focus session was stopped.")

    def _draw_timer_canvas(self: Any, text_str: str) -> None:
        """Render focus timer remaining time string on progress canvas."""
        self.canvas.delete("all")
        width: int = self.canvas.winfo_width() or 880
        self.canvas.create_rectangle(
            10, 5, width - 10, 30, outline="#FAB387", fill=config.FRAME_BG, width=2
        )
        self.canvas.create_text(
            width / 2, 17, text=text_str, fill="#FAB387", font=("Arial", 10, "bold")
        )

    def _on_timer_completed(self: Any, minutes: int) -> None:
        """Handle focus timer expiration callback and send desktop notification."""
        self.update_progress_bar()
        EventLogger.log_event(
            "FOCUS_SESSION_COMPLETED",
            f"{minutes}m Session",
            {
                "duration_min": minutes,
                "task_id": self._focus_task_id,
            },
        )
        msg: str = f"Great job! Your {minutes}-minute focus session is complete."
        send_notification(title="Focus Timer Expired", message=msg)
        messagebox.showinfo("Focus Complete", msg)
