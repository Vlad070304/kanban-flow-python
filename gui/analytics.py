"""
gui/analytics.py
Analytics dashboard window displaying completed tasks, productivity statistics,
total focus time, native visual charts, and activity history export.
"""

from collections import defaultdict
import concurrent.futures
import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import config
from services.event_logger import EventLogger

THREAD_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=2)


class AnalyticsWindow(tk.Toplevel):
    """Top-level modal window showing task completion metrics, charts, and export options."""

    def __init__(self, parent, board_ref):
        super().__init__(parent)
        self.board = board_ref

        self.title("Productivity & Focus Analytics")
        self.geometry("620x680")
        self.configure(bg=config.BG_COLOR)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _calculate_metrics(self):
        """Processes event log file to calculate task, focus metrics, and daily trends."""
        logs = EventLogger.read_logs()

        completed_tasks = [
            log for log in logs if log.get("event") == "TASK_COMPLETED"
        ]
        completed_count = len(completed_tasks)

        focus_sessions = [
            log for log in logs if log.get("event") == "FOCUS_SESSION_COMPLETED"
        ]
        focus_session_count = len(focus_sessions)

        total_focus_minutes = 0
        for session in focus_sessions:
            details = session.get("details", {})
            total_focus_minutes += details.get("duration_min", 0)

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

    def _build_ui(self):
        """Constructs metric summary cards, native chart, and log export controls."""
        metrics = self._calculate_metrics()

        # Header Title
        header_frame = tk.Frame(self, bg=config.BG_COLOR)
        header_frame.pack(fill=tk.X, padx=15, pady=(15, 5))

        tk.Label(
            header_frame,
            text="Productivity Overview",
            fg=config.TEXT_COLOR,
            bg=config.BG_COLOR,
            font=("Arial", 14, "bold")
        ).pack(side=tk.LEFT)

        btn_export = tk.Button(
            header_frame,
            text="Export Analytics CSV",
            bg="#89B4FA",
            fg="#11111B",
            font=("Arial", 9, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            command=self._export_analytics_csv
        )
        btn_export.pack(side=tk.RIGHT)

        # Metrics Cards Container
        cards_frame = tk.Frame(self, bg=config.BG_COLOR)
        cards_frame.pack(fill=tk.X, padx=15, pady=10)

        self._create_stat_card(
            cards_frame,
            title="Completed Tasks",
            value=str(metrics["completed_count"]),
            accent_color="#A6E3A1"
        )

        self._create_stat_card(
            cards_frame,
            title="Focus Sessions",
            value=f"{metrics['focus_session_count']}",
            accent_color="#FAB387"
        )

        hours, mins = divmod(metrics["total_focus_minutes"], 60)
        time_display = f"{hours}h {mins}m" if hours > 0 else f"{mins} mins"
        self._create_stat_card(
            cards_frame,
            title="Total Focus Time",
            value=time_display,
            accent_color="#89B4FA"
        )

        # Chart Section (Native Tkinter Canvas)
        chart_frame = tk.Frame(self, bg=config.FRAME_BG)
        chart_frame.pack(fill=tk.X, padx=15, pady=10)

        self._render_native_chart(chart_frame, metrics)

        # Recent Activity History Header
        tk.Label(
            self,
            text="Recent Activity History",
            fg=config.TEXT_COLOR,
            bg=config.BG_COLOR,
            font=("Arial", 10, "bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        # Log Table Container
        table_frame = tk.Frame(self, bg=config.FRAME_BG)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background=config.FRAME_BG,
            foreground=config.TEXT_COLOR,
            fieldbackground=config.FRAME_BG,
            rowheight=20,
            font=("Arial", 8)
        )
        style.configure(
            "Treeview.Heading",
            background="#313244",
            foreground=config.TEXT_COLOR,
            font=("Arial", 8, "bold")
        )

        tree = ttk.Treeview(
            table_frame,
            columns=("Timestamp", "Event", "Target"),
            show="headings",
            selectmode="none"
        )
        tree.heading("Timestamp", text="Timestamp")
        tree.heading("Event", text="Event Type")
        tree.heading("Target", text="Details / Target")

        tree.column("Timestamp", width=140, anchor="center")
        tree.column("Event", width=160, anchor="w")
        tree.column("Target", width=220, anchor="w")

        scrollbar = ttk.Scrollbar(
            table_frame, orient=tk.VERTICAL, command=tree.yview
        )
        tree.configure(yscroll=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for item in reversed(metrics["logs"]):
            tree.insert(
                "",
                tk.END,
                values=(
                    item.get("timestamp", ""),
                    item.get("event", ""),
                    item.get("target", "")
                )
            )

    def _render_native_chart(self, parent_frame, metrics):
        """Renders native dual bar/line trend chart using Tkinter Canvas."""
        canvas = tk.Canvas(
            parent_frame, height=180, bg=config.FRAME_BG, highlightthickness=0
        )
        canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        all_dates = sorted(list(
            set(metrics["daily_tasks"].keys()) | set(metrics["daily_focus"].keys())
        ))

        if len(all_dates) > 7:
            all_dates = all_dates[-7:]

        if not all_dates:
            today = datetime.date.today().strftime("%Y-%m-%d")
            all_dates = [today]

        task_counts = [metrics["daily_tasks"][d] for d in all_dates]
        focus_mins = [metrics["daily_focus"][d] for d in all_dates]

        # Fix: Direct non-nested max calculation
        max_tasks = max(*task_counts, 5)
        max_focus = max(*focus_mins, 60)

        width = 560
        height = 140
        margin_left = 40
        margin_bottom = 30
        plot_width = width - margin_left - 20
        plot_height = height - margin_bottom

        # Draw Chart Legend
        canvas.create_rectangle(
            margin_left, 5, margin_left + 12, 17, fill="#A6E3A1", outline=""
        )
        canvas.create_text(
            margin_left + 50, 11, text="Tasks Done", fill=config.TEXT_COLOR, font=("Arial", 8)
        )

        canvas.create_line(
            margin_left + 100, 11, margin_left + 120, 11, fill="#FAB387", width=2
        )
        canvas.create_text(
            margin_left + 160, 11, text="Focus (Mins)", fill=config.TEXT_COLOR, font=("Arial", 8)
        )

        num_points = len(all_dates)
        step = plot_width / max(num_points, 1)

        line_points = []

        for i, date_str in enumerate(all_dates):
            x_center = margin_left + (i * step) + (step / 2)

            # Draw Bars (Tasks Done)
            t_val = task_counts[i]
            bar_h = (t_val / max_tasks) * (plot_height - 20)
            y_top = height - margin_bottom - bar_h

            canvas.create_rectangle(
                x_center - 12, y_top, x_center + 12, height - margin_bottom,
                fill="#A6E3A1", outline=""
            )

            # Record Points for Focus Line
            f_val = focus_mins[i]
            line_h = (f_val / max_focus) * (plot_height - 20)
            y_line = height - margin_bottom - line_h
            line_points.append((x_center, y_line))

            # X Axis Labels
            short_date = date_str[-5:]
            canvas.create_text(
                x_center, height - 12, text=short_date,
                fill=config.TEXT_COLOR, font=("Arial", 7)
            )

        # Draw Focus Line
        for i in range(len(line_points) - 1):
            pt1 = line_points[i]
            pt2 = line_points[i + 1]
            canvas.create_line(
                pt1[0], pt1[1], pt2[0], pt2[1], fill="#FAB387", width=2
            )

        for pt in line_points:
            canvas.create_oval(
                pt[0] - 3, pt[1] - 3, pt[0] + 3, pt[1] + 3,
                fill="#FAB387", outline=""
            )

    def _create_stat_card(self, parent, title: str, value: str, accent_color: str):
        """Renders stylized stat card component."""
        card = tk.Frame(parent, bg=config.FRAME_BG, bd=1, relief=tk.RAISED)
        card.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=4)

        tk.Label(
            card,
            text=title,
            fg=config.TEXT_COLOR,
            bg=config.FRAME_BG,
            font=("Arial", 8, "bold")
        ).pack(pady=(8, 2))

        tk.Label(
            card,
            text=value,
            fg=accent_color,
            bg=config.FRAME_BG,
            font=("Arial", 14, "bold")
        ).pack(pady=(0, 8))

    def _export_analytics_csv(self):
        """Dispatches non-blocking thread to export activity logs into CSV file."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if not filepath:
            return

        logs = EventLogger.read_logs()

        def write_analytics_file(log_data, path):
            lines = ["Timestamp,Event,Target,Details\n"]
            for log in log_data:
                ts = log.get("timestamp", "")
                evt = log.get("event", "")
                target = str(log.get("target", "")).replace(",", " ")
                details = str(log.get("details", "")).replace(",", ";")
                lines.append(f"{ts},{evt},{target},{details}\n")

            with open(path, "w", encoding="utf-8") as file:
                file.writelines(lines)
            return len(log_data)

        def on_export_done(future):
            try:
                count = future.result()
                msg = f"Successfully exported {count} analytics records to:\n{filepath}"
                self.after(0, lambda: messagebox.showinfo("Export Success", msg))
            except (IOError, OSError, PermissionError) as err:
                err_msg = f"Failed to export analytics: {err}"
                self.after(0, lambda: messagebox.showerror("Export Error", err_msg))

        future = THREAD_EXECUTOR.submit(write_analytics_file, logs, filepath)
        future.add_done_callback(on_export_done)
