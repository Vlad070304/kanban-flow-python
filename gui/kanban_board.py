"""Kanban board component module managing main views, data, and background tasks."""

import concurrent.futures
import datetime
import logging
import re
import sqlite3
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Any

import config
from gui.analytics import AnalyticsWindow
from gui.dialogs.focus_timer_dialog import FocusTimerDialog
from gui.widgets.kanban_card import KanbanCard
from models.task import Task
from services.event_logger import EventLogger
from services.notification_service import send_notification
from services.task_manager import TaskManager

logging.basicConfig(
    filename="app_error.log",
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
LOGGER: logging.Logger = logging.getLogger(__name__)

THREAD_EXECUTOR: concurrent.futures.ThreadPoolExecutor = (
    concurrent.futures.ThreadPoolExecutor(max_workers=2)
)


class KanbanBoard(tk.Frame):
    """Main Kanban board frame coordinating task columns, filters, and persistence."""

    DATA_FILE: str = "kanban_data.db"

    def __init__(self, parent: tk.Widget) -> None:
        """Initialize KanbanBoard container instance."""
        super().__init__(parent, bg=config.BG_COLOR)
        self.parent: tk.Widget = parent
        self.columns: list[str] = ["To Do", "In Progress", "Done"]
        self.column_frames: dict[str, tk.LabelFrame] = {}
        self.all_cards: list[KanbanCard] = []
        self.task_manager: TaskManager = TaskManager(self.DATA_FILE)
        self.total_cards: int = 0
        self.done_cards: int = 0
        self._timer_running: bool = False

        self._setup_filter_toolbar()
        self._setup_canvas_metric()
        self._setup_board_columns()
        self._setup_input_panel()
        self._bind_keyboard_events()
        self.load_board_data()

    def _is_valid_date_format(self, date_str: str) -> bool:
        """Validate if provided date string complies with YYYY-MM-DD pattern."""
        pattern = r"^\d{4}-\d{2}-\d{2}$"
        if not re.match(pattern, date_str):
            return False
        try:
            datetime.datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def save_board_state(self) -> bool:
        """Public interface for saving board state to database safely."""
        try:
            self.task_manager.save_to_file()
            return True
        except (sqlite3.Error, OSError) as err:
            LOGGER.error("Error saving task data: %s", err)
            messagebox.showerror("Save Error", f"Failed to save data changes:\n{err}")
            return False

    def _setup_filter_toolbar(self) -> None:
        """Construct top toolbar for search and filter actions with hover bindings."""
        toolbar: tk.Frame = tk.Frame(self, bg=config.FRAME_BG, padx=15, pady=8)
        toolbar.pack(fill=tk.X, padx=15, pady=(10, 0))

        tk.Label(
            toolbar,
            text="Search:",
            fg=config.TEXT_COLOR,
            bg=config.FRAME_BG,
            font=("Arial", 9, "bold"),
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.search_var: tk.StringVar = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.filter_tasks())

        self.entry_search: tk.Entry = tk.Entry(
            toolbar,
            textvariable=self.search_var,
            width=20,
            bg="#313244",
            fg=config.TEXT_COLOR,
            insertbackground="white",
        )
        self.entry_search.pack(side=tk.LEFT, padx=(0, 15))

        tk.Label(
            toolbar,
            text="Filter:",
            fg=config.TEXT_COLOR,
            bg=config.FRAME_BG,
            font=("Arial", 9, "bold"),
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.filter_mode: tk.StringVar = tk.StringVar(value="All")

        btn_all: tk.Button = tk.Button(
            toolbar,
            text="All",
            bg="#313244",
            fg=config.TEXT_COLOR,
            font=("Arial", 8, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            command=lambda: self.set_filter_mode("All"),
        )
        btn_all.pack(side=tk.LEFT, padx=2)

        btn_high: tk.Button = tk.Button(
            toolbar,
            text="High Priority",
            bg="#313244",
            fg=config.TEXT_COLOR,
            font=("Arial", 8, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            command=lambda: self.set_filter_mode("High"),
        )
        btn_high.pack(side=tk.LEFT, padx=2)

        btn_today: tk.Button = tk.Button(
            toolbar,
            text="Due Today",
            bg="#313244",
            fg=config.TEXT_COLOR,
            font=("Arial", 8, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            command=lambda: self.set_filter_mode("Today"),
        )
        btn_today.pack(side=tk.LEFT, padx=2)

        self.filter_buttons: dict[str, tk.Button] = {
            "All": btn_all,
            "High": btn_high,
            "Today": btn_today,
        }

        for btn in self.filter_buttons.values():
            btn.bind(
                "<Enter>",
                lambda e, b=btn: (  # type: ignore[misc]
                    b.config(bg="#45475A")
                    if self.filter_mode.get() != b.cget("text")
                    else None
                ),
            )
            btn.bind(
                "<Leave>",
                lambda e, b=btn: self._update_filter_button_styles(),  # type: ignore[misc]
            )

        self._update_filter_button_styles()

    def set_filter_mode(self, mode: str) -> None:
        """Set active filter mode and trigger task update."""
        self.filter_mode.set(mode)
        self._update_filter_button_styles()
        self.filter_tasks()

    def _update_filter_button_styles(self) -> None:
        """Update filter button styles based on current filter mode."""
        active_mode: str = self.filter_mode.get()
        for mode, btn in self.filter_buttons.items():
            if mode == active_mode:
                btn.config(bg=config.ACCENT_COLOR, fg="#11111B")
            else:
                btn.config(bg="#313244", fg=config.TEXT_COLOR)

    def filter_tasks(self) -> None:
        """Filter visible cards based on active search string and selection criteria."""
        query: str = self.search_var.get().strip().lower()
        mode: str = self.filter_mode.get()
        today_str: str = datetime.date.today().strftime("%Y-%m-%d")

        for card in self.all_cards:
            if not card.winfo_exists():
                continue

            title: str = card.task.title.lower()
            priority: str = card.task.priority
            due_date: str = card.task.due_date

            matches_query: bool = not query or query in title
            matches_mode: bool = True
            if mode == "High":
                matches_mode = priority == "HIGH"
            elif mode == "Today":
                matches_mode = due_date == today_str

            if matches_query and matches_mode:
                if not card.winfo_ismapped():
                    card.pack(fill=tk.X, padx=8, pady=5)
            else:
                if card.winfo_ismapped():
                    card.pack_forget()

    def _setup_canvas_metric(self) -> None:
        """Construct progress metric canvas widget."""
        self.canvas: tk.Canvas = tk.Canvas(
            self, height=35, bg=config.FRAME_BG, highlightthickness=0
        )
        self.canvas.pack(fill=tk.X, padx=15, pady=(10, 5))
        self.canvas.bind("<Configure>", lambda _e: self.update_progress_bar())

    def update_progress_bar(self) -> None:
        """Redraw main completion bar with clear dynamic high-contrast text."""
        if self._timer_running:
            return

        self.total_cards = len(self.task_manager.tasks)
        self.done_cards = len(
            [t for t in self.task_manager.tasks if t.status == "Done"]
        )

        self.canvas.delete("all")
        width: int = self.canvas.winfo_width() or 880
        ratio: float = (
            self.done_cards / self.total_cards if self.total_cards > 0 else 0.0
        )
        fill_width: float = max(0.0, (width - 20) * ratio)

        self.canvas.create_rectangle(
            10, 5, width - 10, 30, outline="#313244", fill="#1E1E2E", width=1
        )

        if fill_width > 0:
            self.canvas.create_rectangle(
                10, 5, 10 + fill_width, 30, fill="#A6E3A1", outline=""
            )

        percent_str: str = (
            f"Board Completion: {int(ratio * 100)}% "
            f"({self.done_cards}/{self.total_cards} Tasks)"
        )

        text_color: str = "#11111B" if ratio > 0.4 else "#CDD6F4"

        self.canvas.create_text(
            width / 2, 17, text=percent_str, fill=text_color, font=("Arial", 9, "bold")
        )

    def _setup_board_columns(self) -> None:
        """Construct status column frame containers on the board layout."""
        board_container: tk.Frame = tk.Frame(self, bg=config.BG_COLOR)
        board_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        for col_name in self.columns:
            col_frame: tk.LabelFrame = tk.LabelFrame(
                board_container,
                text=f"  {col_name}  ",
                bg=config.FRAME_BG,
                fg=config.TEXT_COLOR,
                font=("Arial", 11, "bold"),
                bd=2,
                relief=tk.GROOVE,
            )
            col_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
            self.column_frames[col_name] = col_frame

    def _setup_input_panel(self) -> None:
        """Construct bottom input panel for adding cards and triggering dialogs."""
        panel: tk.Frame = tk.Frame(self, bg=config.FRAME_BG, pady=10, padx=10)
        panel.pack(fill=tk.X, side=tk.BOTTOM)

        row1: tk.Frame = tk.Frame(panel, bg=config.FRAME_BG)
        row1.pack(fill=tk.X, pady=2)

        tk.Label(
            row1,
            text="Title:",
            fg=config.TEXT_COLOR,
            bg=config.FRAME_BG,
            font=("Arial", 9, "bold"),
        ).pack(side=tk.LEFT, padx=(0, 2))

        self.entry_title: tk.Entry = tk.Entry(
            row1, width=15, bg="#313244", fg=config.TEXT_COLOR, insertbackground="white"
        )
        self.entry_title.pack(side=tk.LEFT, padx=5)

        tk.Label(
            row1,
            text="Due (YYYY-MM-DD):",
            fg=config.TEXT_COLOR,
            bg=config.FRAME_BG,
            font=("Arial", 9, "bold"),
        ).pack(side=tk.LEFT, padx=(5, 2))

        self.entry_due: tk.Entry = tk.Entry(
            row1, width=11, bg="#313244", fg=config.TEXT_COLOR, insertbackground="white"
        )
        self.entry_due.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        self.entry_due.pack(side=tk.LEFT, padx=5)

        tk.Label(
            row1,
            text="Tags:",
            fg=config.TEXT_COLOR,
            bg=config.FRAME_BG,
            font=("Arial", 9, "bold"),
        ).pack(side=tk.LEFT, padx=(5, 2))

        self.entry_tags: tk.Entry = tk.Entry(
            row1, width=12, bg="#313244", fg=config.TEXT_COLOR, insertbackground="white"
        )
        self.entry_tags.insert(0, "Feature")
        self.entry_tags.pack(side=tk.LEFT, padx=5)

        tk.Label(
            row1,
            text="Priority:",
            fg=config.TEXT_COLOR,
            bg=config.FRAME_BG,
            font=("Arial", 9, "bold"),
        ).pack(side=tk.LEFT, padx=(5, 2))

        self.priority_var: tk.IntVar = tk.IntVar(value=1)
        tk.Radiobutton(
            row1,
            text="Low",
            variable=self.priority_var,
            value=1,
            bg=config.FRAME_BG,
            fg=config.TEXT_COLOR,
            selectcolor=config.BG_COLOR,
        ).pack(side=tk.LEFT)

        tk.Radiobutton(
            row1,
            text="High",
            variable=self.priority_var,
            value=2,
            bg=config.FRAME_BG,
            fg=config.ACCENT_COLOR,
            selectcolor=config.BG_COLOR,
        ).pack(side=tk.LEFT)

        row2: tk.Frame = tk.Frame(panel, bg=config.FRAME_BG)
        row2.pack(fill=tk.X, pady=(6, 2))

        btn_add: tk.Button = tk.Button(
            row2,
            text="+ Add Card",
            bg=config.ACCENT_COLOR,
            fg="#11111B",
            font=("Arial", 9, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            command=self.add_task_card,
        )
        btn_add.pack(side=tk.LEFT, padx=2)

        btn_timer: tk.Button = tk.Button(
            row2,
            text="Focus Timer",
            bg="#FAB387",
            fg="#11111B",
            font=("Arial", 9, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            command=self.open_timer_dialog,
        )
        btn_timer.pack(side=tk.LEFT, padx=5)

        btn_analytics: tk.Button = tk.Button(
            row2,
            text="Analytics",
            bg="#89B4FA",
            fg="#11111B",
            font=("Arial", 9, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            command=lambda: AnalyticsWindow(self.parent, self),
        )
        btn_analytics.pack(side=tk.LEFT, padx=5)

        btn_clear_done: tk.Button = tk.Button(
            row2,
            text="Clear Done",
            bg="#F38BA8",
            fg="#11111B",
            font=("Arial", 9, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            command=self.clear_done_tasks,
        )
        btn_clear_done.pack(side=tk.LEFT, padx=5)

        self._apply_hover_effect(btn_add, config.ACCENT_COLOR, config.BTN_HOVER_ADD)
        self._apply_hover_effect(btn_timer, "#FAB387", config.BTN_HOVER_TIMER)
        self._apply_hover_effect(btn_analytics, "#89B4FA", "#B4BEFE")
        self._apply_hover_effect(btn_clear_done, "#F38BA8", config.BTN_HOVER_CLEAR)

    def _apply_hover_effect(
        self, widget: tk.Widget, default_bg: str, hover_bg: str
    ) -> None:
        """Apply hover color transitions to button widgets."""
        widget.bind(
            "<Enter>",
            lambda _e: widget.config(bg=hover_bg),  # type: ignore[call-arg]
        )
        widget.bind(
            "<Leave>",
            lambda _e: widget.config(bg=default_bg),  # type: ignore[call-arg]
        )

    def open_timer_dialog(self) -> None:
        """Open focus timer modal window."""
        FocusTimerDialog(self.parent, self)

    def start_focus_timer(self, minutes: int = 25) -> None:
        """Start a focus timer countdown worker thread."""
        if self._timer_running:
            messagebox.showwarning("Timer Running", "A focus timer is already active!")
            return

        self._timer_running = True
        total_seconds: int = minutes * 60
        EventLogger.log_event(
            "FOCUS_SESSION_STARTED", f"{minutes}m Session", {"duration_min": minutes}
        )

        def timer_worker() -> None:
            remaining: int = total_seconds
            while remaining > 0 and self._timer_running:
                mins, secs = divmod(remaining, 60)
                time_str: str = f"Focus Timer: {mins:02d}:{secs:02d} remaining"
                self.after(
                    0,
                    lambda t=time_str: self._draw_timer_canvas(t),  # type: ignore[misc]
                )
                time.sleep(1)
                remaining -= 1

            if self._timer_running:
                self._timer_running = False
                self.after(0, lambda: self._on_timer_completed(minutes))

        threading.Thread(target=timer_worker, daemon=True).start()

    def cancel_focus_timer(self) -> None:
        """Cancel current focus timer thread."""
        if self._timer_running:
            self._timer_running = False
            EventLogger.log_event("FOCUS_SESSION_CANCELLED", "Focus Session", {})
            self.update_progress_bar()
            messagebox.showinfo("Timer Cancelled", "Focus session was stopped.")

    def _draw_timer_canvas(self, text_str: str) -> None:
        """Render focus timer remaining time string on progress canvas."""
        self.canvas.delete("all")
        width: int = self.canvas.winfo_width() or 880
        self.canvas.create_rectangle(
            10, 5, width - 10, 30, outline="#FAB387", fill=config.FRAME_BG, width=2
        )
        self.canvas.create_text(
            width / 2, 17, text=text_str, fill="#FAB387", font=("Arial", 10, "bold")
        )

    def _on_timer_completed(self, minutes: int) -> None:
        """Handle focus timer expiration callback and send desktop notification."""
        self.update_progress_bar()
        EventLogger.log_event(
            "FOCUS_SESSION_COMPLETED", f"{minutes}m Session", {"duration_min": minutes}
        )
        msg: str = f"Great job! Your {minutes}-minute focus session is complete."
        send_notification(title="Focus Timer Expired", message=msg)
        messagebox.showinfo("Focus Complete", msg)

    def export_csv_async(self) -> None:
        """Export current task list to a CSV file in a background worker thread."""
        filepath: str = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
        )
        if not filepath:
            return

        snapshot: list[tuple[str, str, str, str, str]] = [
            (t.title, t.status, t.priority, t.due_date, ", ".join(t.tags))
            for t in self.task_manager.tasks
        ]

        def write_file_task(
            data: list[tuple[str, str, str, str, str]], path: str
        ) -> int:
            lines: list[str] = ["Title,Status,Priority,DueDate,Tags\n"]
            for title, status, priority, due_date, tags in data:
                clean_title: str = title.replace(",", " ")
                clean_tags: str = tags.replace(",", ";")
                lines.append(
                    f"{clean_title},{status},{priority},{due_date},{clean_tags}\n"
                )
            with open(path, "w", encoding="utf-8") as file:
                file.writelines(lines)
            return len(data)

        def on_complete(future: Any) -> None:
            try:
                count: int = future.result()
                msg: str = f"Successfully exported {count} tasks to:\n{filepath}"
                self.after(0, lambda: messagebox.showinfo("Export Success", msg))
                EventLogger.log_event("DATA_EXPORTED", filepath, {"count": count})
            except OSError as err:
                LOGGER.error("Background export failed: %s", err)
                err_msg: str = f"Failed export: {err}"
                self.after(0, lambda: messagebox.showerror("Export Error", err_msg))

        future: Any = THREAD_EXECUTOR.submit(write_file_task, snapshot, filepath)
        future.add_done_callback(on_complete)

    def _bind_keyboard_events(self) -> None:
        """Bind global keyboard shortcuts to quick focus entries."""
        self.parent.bind("<Control-n>", lambda _e: self.entry_title.focus_set())
        self.parent.bind("<Escape>", lambda _e: self.entry_title.delete(0, tk.END))
        self.parent.bind("<Control-f>", lambda _e: self.entry_search.focus_set())

    def load_board_data(self) -> None:
        """Load stored tasks from database, build card widgets, and check due dates."""
        try:
            tasks = self.task_manager.load_from_file()
            for task in tasks:
                if task.status in self.column_frames:
                    self._create_card_widget(
                        task.task_id,
                        task.title,
                        task.priority,
                        task.status,
                        task.due_date,
                        task.tags,
                        task.subtasks,
                    )

            due_tasks = self.task_manager.get_due_or_overdue_tasks()
            if due_tasks:
                titles = ", ".join([t.title for t in due_tasks[:3]])
                extra = f" (+{len(due_tasks) - 3} more)" if len(due_tasks) > 3 else ""
                send_notification(
                    title="Task Due Alert",
                    message=(
                        f"You have {len(due_tasks)} task(s) due or overdue: "
                        f"{titles}{extra}"
                    ),
                )

        except (sqlite3.Error, OSError, AttributeError, ValueError) as err:
            LOGGER.error("Failed to load task data from file: %s", err)
            messagebox.showerror(
                "Load Error", f"Could not load saved task data:\n{err}"
            )
        self.update_progress_bar()

    def open_edit_dialog(
        self,
        card: KanbanCard,
        title: str,
        priority_text: str,
        due_date: str,
        tags: list[str],
    ) -> None:
        """Open modal dialog to modify attributes of an existing task card."""
        dialog: tk.Toplevel = tk.Toplevel(self)
        dialog.title("Edit Task")
        dialog.geometry("340x380")
        dialog.configure(bg=config.FRAME_BG)
        dialog.transient(self)  # type: ignore[call-overload]
        dialog.grab_set()

        tk.Label(
            dialog,
            text="Edit Task Title:",
            fg=config.TEXT_COLOR,
            bg=config.FRAME_BG,
            font=("Arial", 9, "bold"),
        ).pack(anchor="w", padx=15, pady=(12, 2))

        entry: tk.Entry = tk.Entry(
            dialog, bg="#313244", fg=config.TEXT_COLOR, insertbackground="white"
        )
        entry.insert(0, title)
        entry.pack(fill=tk.X, padx=15, pady=2)

        tk.Label(
            dialog,
            text="Due Date (YYYY-MM-DD):",
            fg=config.TEXT_COLOR,
            bg=config.FRAME_BG,
            font=("Arial", 9, "bold"),
        ).pack(anchor="w", padx=15, pady=(6, 2))

        entry_due: tk.Entry = tk.Entry(
            dialog, bg="#313244", fg=config.TEXT_COLOR, insertbackground="white"
        )
        entry_due.insert(0, due_date)
        entry_due.pack(fill=tk.X, padx=15, pady=2)

        tk.Label(
            dialog,
            text="Tags (comma-separated):",
            fg=config.TEXT_COLOR,
            bg=config.FRAME_BG,
            font=("Arial", 9, "bold"),
        ).pack(anchor="w", padx=15, pady=(6, 2))

        entry_tags: tk.Entry = tk.Entry(
            dialog, bg="#313244", fg=config.TEXT_COLOR, insertbackground="white"
        )
        entry_tags.insert(0, ", ".join(tags))
        entry_tags.pack(fill=tk.X, padx=15, pady=2)

        tk.Label(
            dialog,
            text="Subtasks (one per line):",
            fg=config.TEXT_COLOR,
            bg=config.FRAME_BG,
            font=("Arial", 9, "bold"),
        ).pack(anchor="w", padx=15, pady=(6, 2))

        txt_subtasks: tk.Text = tk.Text(
            dialog,
            height=4,
            bg="#313244",
            fg=config.TEXT_COLOR,
            insertbackground="white",
            font=("Arial", 9),
        )
        if card.task.subtasks:
            sub_str = "\n".join([s.get("title", "") for s in card.task.subtasks])
            txt_subtasks.insert("1.0", sub_str)
        txt_subtasks.pack(fill=tk.X, padx=15, pady=2)

        prio_var: tk.IntVar = tk.IntVar(value=2 if priority_text == "HIGH" else 1)
        prio_frame: tk.Frame = tk.Frame(dialog, bg=config.FRAME_BG)
        prio_frame.pack(fill=tk.X, padx=15, pady=6)

        tk.Radiobutton(
            prio_frame,
            text="Low",
            variable=prio_var,
            value=1,
            bg=config.FRAME_BG,
            fg=config.TEXT_COLOR,
            selectcolor=config.BG_COLOR,
        ).pack(side=tk.LEFT)

        tk.Radiobutton(
            prio_frame,
            text="High",
            variable=prio_var,
            value=2,
            bg=config.FRAME_BG,
            fg=config.ACCENT_COLOR,
            selectcolor=config.BG_COLOR,
        ).pack(side=tk.LEFT)

        def save_changes() -> None:
            new_title: str = entry.get().strip()
            new_due: str = entry_due.get().strip()
            new_tags: list[str] = [
                t.strip() for t in entry_tags.get().split(",") if t.strip()
            ]

            raw_subtasks: str = txt_subtasks.get("1.0", tk.END).strip()
            existing_map = {
                s.get("title"): s.get("completed", False) for s in card.task.subtasks
            }
            new_subtasks: list[dict[str, Any]] = []
            if raw_subtasks:
                for line in raw_subtasks.split("\n"):
                    st_title = line.strip()
                    if st_title:
                        completed = existing_map.get(st_title, False)
                        new_subtasks.append({"title": st_title, "completed": completed})

            if not new_title:
                messagebox.showwarning(
                    "Validation Error", "Task title cannot be empty!"
                )
                return

            if new_due and not self._is_valid_date_format(new_due):
                messagebox.showerror(
                    "Invalid Date",
                    "Due date must be in YYYY-MM-DD format (e.g., 2026-10-15).",
                )
                return

            new_prio: str = "HIGH" if prio_var.get() == 2 else "LOW"
            card.task.title = new_title
            card.task.priority = new_prio
            card.task.due_date = new_due
            card.task.tags = new_tags
            card.task.subtasks = new_subtasks

            col_name: str = card.task.status
            card_id: str = card.task.task_id
            if card in self.all_cards:
                self.all_cards.remove(card)
            card.destroy()
            self._create_card_widget(
                card_id, new_title, new_prio, col_name, new_due, new_tags, new_subtasks
            )
            if self.save_board_state():
                dialog.destroy()

        tk.Button(
            dialog,
            text="Save Changes",
            bg=config.ACCENT_COLOR,
            fg="#11111B",
            font=("Arial", 9, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            command=save_changes,
        ).pack(pady=8)

    def move_card_vertical(self, card: KanbanCard, direction: int) -> None:
        """Shift task card vertically within its current column frame."""
        col_name: str = card.task.status
        col_cards: list[KanbanCard] = [
            c for c in self.all_cards if c.task.status == col_name
        ]

        if card not in col_cards:
            return

        idx: int = col_cards.index(card)
        new_idx: int = idx + direction

        if 0 <= new_idx < len(col_cards):
            idx_all: int = self.all_cards.index(col_cards[idx])
            new_idx_all: int = self.all_cards.index(col_cards[new_idx])
            self.all_cards[idx_all], self.all_cards[new_idx_all] = (
                self.all_cards[new_idx_all],
                self.all_cards[idx_all],
            )

            col_cards[idx], col_cards[new_idx] = col_cards[new_idx], col_cards[idx]
            for c in col_cards:
                c.pack_forget()
            for c in col_cards:
                c.pack(fill=tk.X, padx=8, pady=5)

            task_dict: dict[str, Any] = {t.task_id: t for t in self.task_manager.tasks}
            reordered_tasks: list[Any] = []
            for c in self.all_cards:
                if c.task.task_id in task_dict:
                    reordered_tasks.append(task_dict[c.task.task_id])

            for t in self.task_manager.tasks:
                if t not in reordered_tasks:
                    reordered_tasks.append(t)

            self.task_manager.tasks = reordered_tasks
            self.save_board_state()

    def move_card_horizontal(self, card: KanbanCard, direction: int) -> None:
        """Move card horizontally between adjacent column frames."""
        current_col: str = card.task.status
        try:
            curr_col_idx: int = self.columns.index(current_col)
        except ValueError:
            return

        new_col_idx: int = curr_col_idx + direction
        if not 0 <= new_col_idx < len(self.columns):
            return

        next_col: str = self.columns[new_col_idx]
        card.task.status = next_col
        if next_col == "Done":
            card.task.mark_completed()

        if not self.save_board_state():
            return

        if card in self.all_cards:
            self.all_cards.remove(card)
        card.destroy()

        self._create_card_widget(
            card.task.task_id,
            card.task.title,
            card.task.priority,
            next_col,
            card.task.due_date,
            card.task.tags,
            card.task.subtasks,
        )
        self.update_progress_bar()

        if next_col == "Done":
            EventLogger.log_event(
                "TASK_COMPLETED", card.task.title, {"priority": card.task.priority}
            )

    def _create_card_widget(
        self,
        task_id: str,
        title: str,
        priority_text: str,
        column_name: str,
        due_date: str = "",
        tags: list[str] | None = None,
        subtasks: list[dict[str, Any]] | None = None,
    ) -> None:
        """Instantiate card widget and append it to target column container."""
        task = next((t for t in self.task_manager.tasks if t.task_id == task_id), None)
        if not task:
            task = Task(
                task_id=task_id,
                title=title,
                priority=priority_text,
                status=column_name,
                due_date=due_date,
                tags=tags or [],
                subtasks=subtasks or [],
            )

        card: KanbanCard = KanbanCard(
            parent=self.column_frames[column_name], board=self, task=task
        )
        card.pack(fill=tk.X, padx=8, pady=5)

        is_overdue: bool = False
        if due_date and column_name != "Done":
            try:
                task_due = datetime.datetime.strptime(due_date, "%Y-%m-%d").date()
                if task_due < datetime.date.today():
                    is_overdue = True
            except ValueError:
                pass

        if is_overdue:
            overdue_bg = "#3B1F2B"
            card.config(
                bg=overdue_bg, highlightbackground="#F38BA8", highlightthickness=1
            )

            def apply_overdue_theme(widget: tk.Widget | tk.Toplevel) -> None:
                if not isinstance(widget, (tk.Button, tk.Checkbutton)):
                    try:
                        widget.config(bg=overdue_bg)  # type: ignore[call-arg]
                    except tk.TclError:
                        pass
                elif isinstance(widget, tk.Checkbutton):
                    try:
                        widget.config(
                            bg=overdue_bg,
                            activebackground=overdue_bg,
                            selectcolor="#5A2329",
                            activeforeground="#F38BA8",
                            fg=config.TEXT_COLOR,
                        )
                    except tk.TclError:
                        pass

                for child in widget.winfo_children():
                    apply_overdue_theme(child)

            apply_overdue_theme(card)

            if hasattr(card, "lbl_due"):
                card.lbl_due.config(bg="#5A2329", fg="#F38BA8")
        else:

            def style_normal_checkbuttons(widget: tk.Widget | tk.Toplevel) -> None:
                if isinstance(widget, tk.Checkbutton):
                    try:
                        widget.config(
                            bg=config.FRAME_BG,
                            activebackground=config.FRAME_BG,
                            selectcolor="#11111B",
                            activeforeground="#A6E3A1",
                            fg=config.TEXT_COLOR,
                        )
                    except tk.TclError:
                        pass
                for child in widget.winfo_children():
                    style_normal_checkbuttons(child)

            style_normal_checkbuttons(card)

        original_bd = card.cget("highlightthickness")
        original_color = card.cget("highlightbackground")

        def on_enter(_e: tk.Event) -> None:
            card.config(highlightbackground="#89B4FA", highlightthickness=1)

        def on_leave(_e: tk.Event) -> None:
            card.config(
                highlightbackground=original_color, highlightthickness=original_bd
            )

        def bind_hover_recursive(widget: tk.Widget | tk.Toplevel) -> None:
            """Recursively bind hover events across all child widgets in card."""
            widget.bind("<Enter>", on_enter, add="+")
            widget.bind("<Leave>", on_leave, add="+")
            for child in widget.winfo_children():
                bind_hover_recursive(child)

        bind_hover_recursive(card)

        self.all_cards.append(card)
        self.filter_tasks()

    def clear_done_tasks(self) -> None:
        """Purge completed tasks from management state and destroy active cards."""
        self.task_manager.clear_done()
        if not self.save_board_state():
            return

        done_frame: tk.LabelFrame = self.column_frames["Done"]
        for card in done_frame.winfo_children():
            if card in self.all_cards:
                self.all_cards.remove(card)
            card.destroy()

        self.update_progress_bar()

    def add_task_card(self) -> None:
        """Process user inputs from entry fields and instantiate a new task card."""
        title: str = self.entry_title.get().strip()
        due_date: str = self.entry_due.get().strip()
        tags_raw: str = self.entry_tags.get().strip()
        tags: list[str] = [t.strip() for t in tags_raw.split(",") if t.strip()]

        if not title:
            messagebox.showwarning("Validation Error", "Task title cannot be empty!")
            return

        if due_date and not self._is_valid_date_format(due_date):
            messagebox.showerror(
                "Invalid Date",
                "Due date must be in YYYY-MM-DD format (e.g., 2026-10-15).",
            )
            return

        priority_text: str = "HIGH" if self.priority_var.get() == 2 else "LOW"

        new_task = self.task_manager.add_task(
            title=title,
            priority=priority_text,
            status="To Do",
            due_date=due_date,
            tags=tags,
        )
        if not self.save_board_state():
            return

        self._create_card_widget(
            new_task.task_id,
            title,
            priority_text,
            "To Do",
            due_date,
            tags,
            new_task.subtasks,
        )
        self.update_progress_bar()
        EventLogger.log_event(
            "TASK_CREATED", title, {"priority": priority_text, "due_date": due_date}
        )
        self.entry_title.delete(0, tk.END)
