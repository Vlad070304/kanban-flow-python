"""
gui/analytics.py
Analytics dashboard window displaying project task distribution and metrics.
"""

import tkinter as tk
import config


class AnalyticsWindow(tk.Toplevel):
    """Analytics top-level window rendering board metrics and task counts."""

    def __init__(self, parent, kanban_board):
        """Initializes analytics view and calculates current task metrics."""
        super().__init__(parent)
        self.kanban_board = kanban_board

        self.title("Analytics Dashboard")
        self.geometry("380x300")
        self.configure(bg=config.BG_COLOR)

        self._render_metrics()

    def _render_metrics(self):
        """Renders summary cards for task completion stats."""
        tk.Label(
            self, text="Board Analytics Overview",
            font=("Arial", 14, "bold"), fg=config.TEXT_COLOR, bg=config.BG_COLOR
        ).pack(pady=(15, 10))

        stats = self._calculate_stats()

        for label, val in stats.items():
            frame = tk.Frame(self, bg=config.FRAME_BG, pady=5, padx=10)
            frame.pack(fill=tk.X, padx=20, pady=3)

            tk.Label(
                frame, text=f"{label}:", font=("Arial", 10, "bold"),
                fg=config.TEXT_COLOR, bg=config.FRAME_BG
            ).pack(side=tk.LEFT)

            tk.Label(
                frame, text=str(val), font=("Arial", 10, "bold"),
                fg=config.ACCENT_COLOR, bg=config.FRAME_BG
            ).pack(side=tk.RIGHT)

    def _calculate_stats(self) -> dict:
        """Calculates metric breakdowns across column states."""
        counts = {"To Do": 0, "In Progress": 0, "Done": 0, "High Priority": 0}

        for col_name, frame in self.kanban_board.column_frames.items():
            for card in frame.winfo_children():
                if col_name in counts:
                    counts[col_name] += 1
                labels = card.winfo_children()
                if len(labels) >= 2 and "HIGH" in labels[1].cget("text"):
                    counts["High Priority"] += 1

        total = counts["To Do"] + counts["In Progress"] + counts["Done"]
        ratio = (counts["Done"] / total * 100) if total > 0 else 0

        return {
            "Total Tasks": total,
            "To Do": counts["To Do"],
            "In Progress": counts["In Progress"],
            "Done": counts["Done"],
            "High Priority Tasks": counts["High Priority"],
            "Completion Rate": f"{int(ratio)}%"
        }
