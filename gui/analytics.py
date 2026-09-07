"""
gui/analytics.py
Analytics window featuring performance charts and an interactive log viewer tab.
"""

import tkinter as tk
from tkinter import ttk
import config
from services.event_logger import EventLogger


class AnalyticsWindow(tk.Toplevel):
    """Top-level window displaying analytics dashboard and historical event log tab."""

    def __init__(self, parent, kanban_board):
        """Initializes tabbed layout and renders chart and log components."""
        super().__init__(parent)
        self.kanban_board = kanban_board

        self.title("Analytics & Event History")
        self.geometry("520x540")
        self.configure(bg=config.BG_COLOR)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tab_dashboard = tk.Frame(self.notebook, bg=config.BG_COLOR)
        self.tab_logs = tk.Frame(self.notebook, bg=config.BG_COLOR)

        self.notebook.add(self.tab_dashboard, text=" Dashboard & Chart ")
        self.notebook.add(self.tab_logs, text=" Event Log Viewer ")

        self.counts = {}
        self._render_dashboard_tab()
        self._render_logs_tab()

    def _calculate_metrics(self) -> dict:
        """Computes current task states and historical counts."""
        counts = {"To Do": 0, "In Progress": 0, "Done": 0, "High Priority": 0}

        for col_name, frame in self.kanban_board.column_frames.items():
            for card in frame.winfo_children():
                if col_name in counts:
                    counts[col_name] += 1
                labels = card.winfo_children()
                if len(labels) >= 2 and "HIGH" in labels[1].cget("text"):
                    counts["High Priority"] += 1

        total_tasks = counts["To Do"] + counts["In Progress"] + counts["Done"]
        completion_rate = (
            (counts["Done"] / total_tasks * 100) if total_tasks > 0 else 0
        )

        events = EventLogger.load_events()
        completed_events = len(
            [e for e in events if e.get("event_type") == "TASK_COMPLETED"]
        )

        if counts["In Progress"] > 4:
            health_status = "[WARNING] WIP Bottleneck (>4 active)"
        elif counts["High Priority"] > 2:
            health_status = "[RISK] Stalled High Priority Tasks"
        else:
            health_status = "[OK] Healthy Flow"

        self.counts = counts

        return {
            "Total Active Tasks": total_tasks,
            "Historical Completed Events": completed_events,
            "Completion Rate": f"{int(completion_rate)}%",
            "Board Health": health_status,
        }

    def _render_dashboard_tab(self):
        """Renders metrics panel and canvas bar chart."""
        tk.Label(
            self.tab_dashboard,
            text="Project Overview & Health",
            font=("Arial", 12, "bold"),
            fg=config.TEXT_COLOR,
            bg=config.BG_COLOR,
        ).pack(pady=(10, 5))

        metrics = self._calculate_metrics()

        for label, val in metrics.items():
            frame = tk.Frame(self.tab_dashboard, bg=config.FRAME_BG, pady=4, padx=12)
            frame.pack(fill=tk.X, padx=15, pady=2)

            is_health = label == "Board Health"
            val_str = str(val)
            val_color = (
                "#F38BA8"
                if "[WARNING]" in val_str or "[RISK]" in val_str
                else (config.ACCENT_COLOR if not is_health else "#A6E3A1")
            )

            tk.Label(
                frame, text=f"{label}:", font=("Arial", 9, "bold"),
                fg=config.TEXT_COLOR, bg=config.FRAME_BG
            ).pack(side=tk.LEFT)

            tk.Label(
                frame, text=val_str, font=("Arial", 9 if is_health else 10, "bold"),
                fg=val_color, bg=config.FRAME_BG
            ).pack(side=tk.RIGHT)

        self._render_distribution_chart()

    def _render_distribution_chart(self):
        """Renders custom Tkinter Canvas bar chart."""
        tk.Label(
            self.tab_dashboard,
            text="Task Distribution",
            font=("Arial", 11, "bold"),
            fg=config.TEXT_COLOR,
            bg=config.BG_COLOR,
        ).pack(pady=(12, 4))

        canvas = tk.Canvas(
            self.tab_dashboard, height=170, bg=config.FRAME_BG, highlightthickness=0
        )
        canvas.pack(fill=tk.X, padx=15, pady=5)

        cols = ["To Do", "In Progress", "Done"]
        colors = ["#F38BA8", "#FAB387", "#A6E3A1"]
        max_val = max([self.counts.get(c, 0) for c in cols] + [1])

        bar_width = 50
        gap = 45
        start_x = 75
        max_bar_height = 100

        for idx, col in enumerate(cols):
            val = self.counts.get(col, 0)
            height = (val / max_val) * max_bar_height
            x0 = start_x + idx * (bar_width + gap)
            y0 = 130 - height
            x1 = x0 + bar_width
            y1 = 130

            canvas.create_rectangle(x0, y0, x1, y1, fill=colors[idx], outline="")

            canvas.create_text(
                x0 + bar_width / 2, y0 - 8,
                text=str(val), fill=config.TEXT_COLOR, font=("Arial", 9, "bold")
            )

            canvas.create_text(
                x0 + bar_width / 2, 145,
                text=col, fill=config.TEXT_COLOR, font=("Arial", 9)
            )

    def _render_logs_tab(self):
        """Renders structured text box displaying event log history."""
        frame = tk.Frame(self.tab_logs, bg=config.BG_COLOR)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_area = tk.Text(
            frame,
            bg=config.FRAME_BG,
            fg=config.TEXT_COLOR,
            insertbackground="white",
            font=("Courier", 9),
            yscrollcommand=scrollbar.set,
            wrap=tk.WORD,
        )
        text_area.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_area.yview)

        events = EventLogger.load_events()
        if not events:
            text_area.insert(tk.END, "No event logs found.")
        else:
            for evt in reversed(events):
                ts = evt.get("timestamp", "")[:19].replace("T", " ")
                etype = evt.get("event_type", "EVENT")
                title = evt.get("task_title", "")
                prio = evt.get("priority", "")
                prio_str = f" [{prio}]" if prio else ""
                log_line = f"[{ts}] {etype}: {title}{prio_str}\n"
                text_area.insert(tk.END, log_line)

        text_area.config(state=tk.DISABLED)
