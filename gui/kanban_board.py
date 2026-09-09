"""
gui/kanban_board.py
Main Kanban board container coordinating task columns, filtering,
task manager integration, and focus timers.
"""

import concurrent.futures
import datetime
import logging
import re
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Any, Dict, List, Optional, Tuple

import config
from gui.analytics import AnalyticsWindow
from gui.dialogs import FocusTimerDialog
from gui.widgets import KanbanCard
from services.event_logger import EventLogger
from services.task_manager import TaskManager

logging.basicConfig(
    filename="app_error.log",
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
LOGGER: logging.Logger = logging.getLogger(__name__)

THREAD_EXECUTOR: concurrent.futures.ThreadPoolExecutor = (
    concurrent.futures.ThreadPoolExecutor(max_workers=2)
)


class KanbanBoard(tk.Frame):
    """Main Kanban board frame managing task views and background tasks."""

    DATA_FILE: str = "kanban_data.json"

    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent, bg=config.BG_COLOR)
        self.parent: tk.Widget = parent
        self.columns: List[str] = ["To Do", "In Progress", "Done"]
        self.column_frames: Dict[str, tk.LabelFrame] = {}
        self.all_cards: List[KanbanCard] = []
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
        # Validate YYYY-MM-DD pattern via regex and verify actual calendar validity
        pattern = r"^\d{4}-\d{2}-\d{2}$"
        if not re.match(pattern, date_str):
            return False
        try:
            datetime.datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def _safe_save(self) -> bool:
        """Saves current state to storage safely handling I/O errors."""
        try:
            self.task_manager.save_to_file()
            return True
        except (IOError, OSError, PermissionError) as err:
            LOGGER.error("Error saving task data: %s", err)
            messagebox.showerror(
                "Save Error", f"Failed to save data changes:\n{err}"
            )
            return False

    def _setup_filter_toolbar(self) -> None:
        """Builds search and filter controls toolbar."""
        toolbar: tk.Frame = tk.Frame(self, bg=config.FRAME_BG, padx=15, pady=8)
        toolbar.pack(fill=tk.X, padx=15, pady=(10, 0))

        tk.Label(
            toolbar, text="Search:", fg=config.TEXT_COLOR, bg=config.FRAME_BG,
            font=("Arial", 9, "bold")
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.search_var: tk.StringVar = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.filter_tasks())

        self.entry_search: tk.Entry = tk.Entry(
            toolbar, textvariable=self.search_var, width=20,
            bg="#313244", fg=config.TEXT_COLOR, insertbackground="white"
        )
        self.entry_search.pack(side=tk.LEFT, padx=(0, 15))

        tk.Label(
            toolbar, text="Filter:", fg=config.TEXT_COLOR, bg=config.FRAME_BG,
            font=("Arial", 9, "bold")
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.filter_mode: tk.StringVar = tk.StringVar(value="All")

        btn_all: tk.Button = tk.Button(
            toolbar, text="All", bg="#313244", fg=config.TEXT_COLOR,
            font=("Arial", 8, "bold"), relief=tk.FLAT, cursor="hand2",
            command=lambda: self.set_filter_mode("All")
        )
        btn_all.pack(side=tk.LEFT, padx=2)

        btn_high: tk.Button = tk.Button(
            toolbar, text="High Priority", bg="#313244", fg=config.TEXT_COLOR,
            font=("Arial", 8, "bold"), relief=tk.FLAT, cursor="hand2",
            command=lambda: self.set_filter_mode("High")
        )
        btn_high.pack(side=tk.LEFT, padx=2)

        btn_today: tk.Button = tk.Button(
            toolbar, text="Due Today", bg="#313244", fg=config.TEXT_COLOR,
            font=("Arial", 8, "bold"), relief=tk.FLAT, cursor="hand2",
            command=lambda: self.set_filter_mode("Today")
        )
        btn_today.pack(side=tk.LEFT, padx=2)

        self.filter_buttons: Dict[str, tk.Button] = {
            "All": btn_all, "High": btn_high, "Today": btn_today
        }
        self._update_filter_button_styles()

    def set_filter_mode(self, mode: str) -> None:
        """Sets active filter mode and updates card visibility."""
        self.filter_mode.set(mode)
        self._update_filter_button_styles()
        self.filter_tasks()

    def _update_filter_button_styles(self) -> None:
        """Updates background highlight colors on filter buttons."""
        active_mode: str = self.filter_mode.get()
        for mode, btn in self.filter_buttons.items():
            if mode == active_mode:
                btn.config(bg=config.ACCENT_COLOR, fg="#11111B")
            else:
                btn.config(bg="#313244", fg=config.TEXT_COLOR)

    def filter_tasks(self) -> None:
        """Filters visible task cards based on search query and priority/due filter."""
        query: str = self.search_var.get().strip().lower()
        mode: str = self.filter_mode.get()
        today_str: str = datetime.date.today().strftime("%Y-%m-%d")

        for card in self.all_cards:
            if not card.winfo_exists():
                continue

            title: str = card.task_title.lower()
            priority: str = card.task_priority
            due_date: str = card.task_due_date

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
        """Initializes top progress metric display canvas."""
        self.canvas: tk.Canvas = tk.Canvas(
            self, height=35, bg=config.FRAME_BG, highlightthickness=0
        )
        self.canvas.pack(fill=tk.X, padx=15, pady=(10, 5))
        self.canvas.bind("<Configure>", lambda e: self.update_progress_bar())

    def update_progress_bar(self) -> None:
        """Redraws completion percentage metric on the canvas bar."""
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
        fill_width: float = max(10.0, (width - 20) * ratio)

        self.canvas.create_rectangle(
            10, 5, width - 10, 30, outline=config.TEXT_COLOR,
            fill=config.BG_COLOR, width=1
        )
        self.canvas.create_rectangle(
            10, 5, fill_width, 30, fill="#A6E3A1", outline=""
        )
        percent_str: str = (
            f"Board Completion: {int(ratio * 100)}% "
            f"({self.done_cards}/{self.total_cards} Tasks)"
        )
        self.canvas.create_text(
            width / 2, 17, text=percent_str, fill=config.TEXT_COLOR,
            font=("Arial", 9, "bold")
        )

    def _setup_board_columns(self) -> None:
        """Constructs Kanban column frames."""
        board_container: tk.Frame = tk.Frame(self, bg=config.BG_COLOR)
        board_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        for col_name in self.columns:
            col_frame: tk.LabelFrame = tk.LabelFrame(
                board_container, text=f"  {col_name}  ", bg=config.FRAME_BG,
                fg=config.TEXT_COLOR, font=("Arial", 11, "bold"), bd=2,
                relief=tk.GROOVE
            )
            col_frame.pack(
                side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5
            )
            self.column_frames[col_name] = col_frame

    def _setup_input_panel(self) -> None:
        """Builds task creation input toolbar at bottom."""
        panel: tk.Frame = tk.Frame(self, bg=config.FRAME_BG, pady=10, padx=10)
        panel.pack(fill=tk.X, side=tk.BOTTOM)

        row1: tk.Frame = tk.Frame(panel, bg=config.FRAME_BG)
        row1.pack(fill=tk.X, pady=2)

        tk.Label(
            row1, text="Title:", fg=config.TEXT_COLOR, bg=config.FRAME_BG,
            font=("Arial", 9, "bold")
        ).pack(side=tk.LEFT, padx=(0, 2))

        self.entry_title: tk.Entry = tk.Entry(
            row1, width=15, bg="#313244", fg=config.TEXT_COLOR,
            insertbackground="white"
        )
        self.entry_title.pack(side=tk.LEFT, padx=5)

        tk.Label(
            row1, text="Due (YYYY-MM-DD):", fg=config.TEXT_COLOR,
            bg=config.FRAME_BG, font=("Arial", 9, "bold")
        ).pack(side=tk.LEFT, padx=(5, 2))

        self.entry_due: tk.Entry = tk.Entry(
            row1, width=11, bg="#313244", fg=config.TEXT_COLOR,
            insertbackground="white"
        )
        self.entry_due.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        self.entry_due.pack(side=tk.LEFT, padx=5)

        tk.Label(
            row1, text="Tags:", fg=config.TEXT_COLOR, bg=config.FRAME_BG,
            font=("Arial", 9, "bold")
        ).pack(side=tk.LEFT, padx=(5, 2))

        self.entry_tags: tk.Entry = tk.Entry(
            row1, width=12, bg="#313244", fg=config.TEXT_COLOR,
            insertbackground="white"
        )
        self.entry_tags.insert(0, "Feature")
        self.entry_tags.pack(side=tk.LEFT, padx=5)

        tk.Label(
            row1, text="Priority:", fg=config.TEXT_COLOR, bg=config.FRAME_BG,
            font=("Arial", 9, "bold")
        ).pack(side=tk.LEFT, padx=(5, 2))

        self.priority_var: tk.IntVar = tk.IntVar(value=1)
        tk.Radiobutton(
            row1, text="Low", variable=self.priority_var, value=1,
            bg=config.FRAME_BG, fg=config.TEXT_COLOR, selectcolor=config.BG_COLOR
        ).pack(side=tk.LEFT)

        tk.Radiobutton(
            row1, text="High", variable=self.priority_var, value=2,
            bg=config.FRAME_BG, fg=config.ACCENT_COLOR,
            selectcolor=config.BG_COLOR
        ).pack(side=tk.LEFT)

        row2: tk.Frame = tk.Frame(panel, bg=config.FRAME_BG)
        row2.pack(fill=tk.X, pady=(6, 2))

        btn_add: tk.Button = tk.Button(
            row2, text="+ Add Card", bg=config.ACCENT_COLOR, fg="#11111B",
            font=("Arial", 9, "bold"), relief=tk.FLAT, cursor="hand2",
            command=self.add_task_card
        )
        btn_add.pack(side=tk.LEFT, padx=2)

        btn_timer: tk.Button = tk.Button(
            row2, text="Focus Timer", bg="#FAB387", fg="#11111B",
            font=("Arial", 9, "bold"), relief=tk.FLAT, cursor="hand2",
            command=self.open_timer_dialog
        )
        btn_timer.pack(side=tk.LEFT, padx=5)

        btn_analytics: tk.Button = tk.Button(
            row2, text="Analytics", bg="#89B4FA", fg="#11111B",
            font=("Arial", 9, "bold"), relief=tk.FLAT, cursor="hand2",
            command=lambda: AnalyticsWindow(self.parent, self)
        )
        btn_analytics.pack(side=tk.LEFT, padx=5)

        btn_clear_done: tk.Button = tk.Button(
            row2, text="Clear Done", bg="#F38BA8", fg="#11111B",
            font=("Arial", 9, "bold"), relief=tk.FLAT, cursor="hand2",
            command=self.clear_done_tasks
        )
        btn_clear_done.pack(side=tk.LEFT, padx=5)

        self._apply_hover_effect(
            btn_add, config.ACCENT_COLOR, config.BTN_HOVER_ADD
        )
        self._apply_hover_effect(
            btn_timer, "#FAB387", config.BTN_HOVER_TIMER
        )
        self._apply_hover_effect(
            btn_analytics, "#89B4FA", "#B4BEFE"
        )
        self._apply_hover_effect(
            btn_clear_done, "#F38BA8", config.BTN_HOVER_CLEAR
        )

    def _apply_hover_effect(
        self, widget: tk.Widget, default_bg: str, hover_bg: str
    ) -> None:
        """Applies hover mouseover background transitions on buttons."""
        widget.bind("<Enter>", lambda e: widget.config(bg=hover_bg))
        widget.bind("<Leave>", lambda e: widget.config(bg=default_bg))

    def open_timer_dialog(self) -> None:
        """Opens modal dialog for setting up focus session."""
        FocusTimerDialog(self.parent, self)

    def start_focus_timer(self, minutes: int = 25) -> None:
        """Starts asynchronous focus timer countdown on separate thread."""
        if self._timer_running:
            messagebox.showwarning(
                "Timer Running", "A focus timer is already active!"
            )
            return

        self._timer_running = True
        total_seconds: int = minutes * 60
        EventLogger.log_event(
            "FOCUS_SESSION_STARTED", f"{minutes}m Session",
            {"duration_min": minutes}
        )

        def timer_worker() -> None:
            remaining: int = total_seconds
            while remaining > 0 and self._timer_running:
                mins, secs = divmod(remaining, 60)
                time_str: str = f"Focus Timer: {mins:02d}:{secs:02d} remaining"
                self.after(0, lambda t=time_str: self._draw_timer_canvas(t))
                time.sleep(1)
                remaining -= 1

            if self._timer_running:
                self._timer_running = False
                self.after(0, lambda: self._on_timer_completed(minutes))

        threading.Thread(target=timer_worker, daemon=True).start()

    def cancel_focus_timer(self) -> None:
        """Cancels running focus timer."""
        if self._timer_running:
            self._timer_running = False
            EventLogger.log_event(
                "FOCUS_SESSION_CANCELLED", "Focus Session", {}
            )
            self.update_progress_bar()
            messagebox.showinfo("Timer Cancelled", "Focus session was stopped.")

    def _draw_timer_canvas(self, text_str: str) -> None:
        """Renders focus timer countdown inside top canvas area."""
        self.canvas.delete("all")
        width: int = self.canvas.winfo_width() or 880
        self.canvas.create_rectangle(
            10, 5, width - 10, 30, outline="#FAB387",
            fill=config.FRAME_BG, width=2
        )
        self.canvas.create_text(
            width / 2, 17, text=text_str, fill="#FAB387",
            font=("Arial", 10, "bold")
        )

    def _on_timer_completed(self, minutes: int) -> None:
        """Handles timer completion UI updates and popup alerts."""
        self.update_progress_bar()
        EventLogger.log_event(
            "FOCUS_SESSION_COMPLETED", f"{minutes}m Session",
            {"duration_min": minutes}
        )
        msg: str = (
            f"Great job! Your {minutes}-minute focus session is complete."
        )
        messagebox.showinfo("Focus Complete", msg)

    def export_csv_async(self) -> None:
        """Exports board tasks asynchronously to target CSV file using ThreadPoolExecutor."""
        filepath: str = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if not filepath:
            return

        snapshot: List[Tuple[str, str, str, str, str]] = [
            (t.title, t.status, t.priority, t.due_date, ", ".join(t.tags))
            for t in self.task_manager.tasks
        ]

        def write_file_task(
            data: List[Tuple[str, str, str, str, str]], path: str
        ) -> int:
            lines: List[str] = ["Title,Status,Priority,DueDate,Tags\n"]
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
                msg: str = (
                    f"Successfully exported {count} tasks to:\n{filepath}"
                )
                self.after(
                    0, lambda: messagebox.showinfo("Export Success", msg)
                )
                EventLogger.log_event(
                    "DATA_EXPORTED", filepath, {"count": count}
                )
            except (IOError, OSError, PermissionError) as err:
                LOGGER.error("Background export failed: %s", err)
                err_msg: str = f"Failed export: {err}"
                self.after(
                    0, lambda: messagebox.showerror("Export Error", err_msg)
                )

        future: Any = THREAD_EXECUTOR.submit(
            write_file_task, snapshot, filepath
        )
        future.add_done_callback(on_complete)

    def _bind_keyboard_events(self) -> None:
        """Binds global shortcuts for task focus and creation."""
        self.parent.bind(
            "<Control-n>", lambda e: self.entry_title.focus_set()
        )
        self.parent.bind(
            "<Escape>", lambda e: self.entry_title.delete(0, tk.END)
        )
        self.parent.bind(
            "<Control-f>", lambda e: self.entry_search.focus_set()
        )

    def load_board_data(self) -> None:
        """Loads saved tasks from file and instantiates task card widgets."""
        try:
            tasks = self.task_manager.load_from_file()
            for task in tasks:
                if task.status in self.column_frames:
                    self._create_card_widget(
                        task.task_id, task.title, task.priority,
                        task.status, task.due_date, task.tags
                    )
        except (IOError, OSError, PermissionError) as err:
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
        tags: List[str]
    ) -> None:
        """Opens task card edit dialog."""
        dialog: tk.Toplevel = tk.Toplevel(self)
        dialog.title("Edit Task")
        dialog.geometry("320x260")
        dialog.configure(bg=config.FRAME_BG)
        dialog.transient(self)
        dialog.grab_set()

        tk.Label(
            dialog, text="Edit Task Title:", fg=config.TEXT_COLOR,
            bg=config.FRAME_BG, font=("Arial", 9, "bold")
        ).pack(anchor="w", padx=15, pady=(15, 2))

        entry: tk.Entry = tk.Entry(
            dialog, bg="#313244", fg=config.TEXT_COLOR,
            insertbackground="white"
        )
        entry.insert(0, title)
        entry.pack(fill=tk.X, padx=15, pady=2)

        tk.Label(
            dialog, text="Due Date (YYYY-MM-DD):", fg=config.TEXT_COLOR,
            bg=config.FRAME_BG, font=("Arial", 9, "bold")
        ).pack(anchor="w", padx=15, pady=(8, 2))

        entry_due: tk.Entry = tk.Entry(
            dialog, bg="#313244", fg=config.TEXT_COLOR,
            insertbackground="white"
        )
        entry_due.insert(0, due_date)
        entry_due.pack(fill=tk.X, padx=15, pady=2)

        tk.Label(
            dialog, text="Tags (comma-separated):", fg=config.TEXT_COLOR,
            bg=config.FRAME_BG, font=("Arial", 9, "bold")
        ).pack(anchor="w", padx=15, pady=(8, 2))

        entry_tags: tk.Entry = tk.Entry(
            dialog, bg="#313244", fg=config.TEXT_COLOR,
            insertbackground="white"
        )
        entry_tags.insert(0, ", ".join(tags))
        entry_tags.pack(fill=tk.X, padx=15, pady=2)

        prio_var: tk.IntVar = tk.IntVar(
            value=2 if priority_text == "HIGH" else 1
        )
        prio_frame: tk.Frame = tk.Frame(dialog, bg=config.FRAME_BG)
        prio_frame.pack(fill=tk.X, padx=15, pady=8)

        tk.Radiobutton(
            prio_frame, text="Low", variable=prio_var, value=1,
            bg=config.FRAME_BG, fg=config.TEXT_COLOR, selectcolor=config.BG_COLOR
        ).pack(side=tk.LEFT)

        tk.Radiobutton(
            prio_frame, text="High", variable=prio_var, value=2,
            bg=config.FRAME_BG, fg=config.ACCENT_COLOR,
            selectcolor=config.BG_COLOR
        ).pack(side=tk.LEFT)

        def save_changes() -> None:
            new_title: str = entry.get().strip()
            new_due: str = entry_due.get().strip()
            new_tags: List[str] = [
                t.strip() for t in entry_tags.get().split(",") if t.strip()
            ]

            if not new_title:
                messagebox.showwarning(
                    "Validation Error", "Task title cannot be empty!"
                )
                return

            if new_due and not self._is_valid_date_format(new_due):
                messagebox.showerror(
                    "Invalid Date",
                    "Due date must be in YYYY-MM-DD format (e.g., 2026-10-15)."
                )
                return

            new_prio: str = "HIGH" if prio_var.get() == 2 else "LOW"
            for t in self.task_manager.tasks:
                if t.task_id == card.task_id:
                    t.title = new_title
                    t.priority = new_prio
                    t.due_date = new_due
                    t.tags = new_tags
                    break

            col_name: str = card.column_name
            card_id: str = card.task_id
            if card in self.all_cards:
                self.all_cards.remove(card)
            card.destroy()
            self._create_card_widget(
                card_id, new_title, new_prio, col_name, new_due, new_tags
            )
            if self._safe_save():
                dialog.destroy()

        tk.Button(
            dialog, text="Save Changes", bg=config.ACCENT_COLOR, fg="#11111B",
            font=("Arial", 9, "bold"), relief=tk.FLAT, cursor="hand2",
            command=save_changes
        ).pack(pady=10)

    def move_card_vertical(self, card: KanbanCard, direction: int) -> None:
        """Moves a card up (-1) or down (+1) within its current column list."""
        col_name: str = card.column_name
        col_cards: List[KanbanCard] = [
            c for c in self.all_cards if c.column_name == col_name
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

            task_dict: Dict[str, Any] = {
                t.task_id: t for t in self.task_manager.tasks
            }
            reordered_tasks: List[Any] = []
            for c in self.all_cards:
                if c.task_id in task_dict:
                    reordered_tasks.append(task_dict[c.task_id])

            for t in self.task_manager.tasks:
                if t not in reordered_tasks:
                    reordered_tasks.append(t)

            self.task_manager.tasks = reordered_tasks
            self._safe_save()

    def move_card_horizontal(self, card: KanbanCard, direction: int) -> None:
        """Moves a card left (-1) or right (+1) between Kanban columns."""
        current_col: str = card.column_name
        try:
            curr_col_idx: int = self.columns.index(current_col)
        except ValueError:
            return

        new_col_idx: int = curr_col_idx + direction
        if not 0 <= new_col_idx < len(self.columns):
            return

        next_col: str = self.columns[new_col_idx]
        title: str = card.task_title
        priority_text: str = card.task_priority
        due_date: str = card.task_due_date
        task_id: str = card.task_id

        matching_task = next(
            (t for t in self.task_manager.tasks if t.task_id == task_id),
            None
        )
        tags: List[str] = matching_task.tags if matching_task else []

        for t in self.task_manager.tasks:
            if t.task_id == task_id:
                t.status = next_col
                if next_col == "Done":
                    t.mark_completed()
                break

        if not self._safe_save():
            return

        if card in self.all_cards:
            self.all_cards.remove(card)
        card.destroy()

        self._create_card_widget(
            task_id, title, priority_text, next_col, due_date, tags
        )
        self.update_progress_bar()

        if next_col == "Done":
            EventLogger.log_event(
                "TASK_COMPLETED", title, {"priority": priority_text}
            )

    def _create_card_widget(
        self,
        task_id: str,
        title: str,
        priority_text: str,
        column_name: str,
        due_date: str = "",
        tags: Optional[List[str]] = None
    ) -> None:
        """Instantiates and renders individual task card frame widget."""
        card: KanbanCard = KanbanCard(
            self.column_frames[column_name],
            self,
            task_id,
            title,
            priority_text,
            column_name,
            due_date,
            tags
        )
        card.pack(fill=tk.X, padx=8, pady=5)
        self.all_cards.append(card)
        self.filter_tasks()

    def clear_done_tasks(self) -> None:
        """Removes all completed tasks in Done state."""
        self.task_manager.clear_done()
        if not self._safe_save():
            return

        done_frame: tk.LabelFrame = self.column_frames["Done"]
        for card in done_frame.winfo_children():
            if card in self.all_cards:
                self.all_cards.remove(card)
            card.destroy()

        self.update_progress_bar()

    def add_task_card(self) -> None:
        """Reads input fields and creates new task card."""
        title: str = self.entry_title.get().strip()
        due_date: str = self.entry_due.get().strip()
        tags_raw: str = self.entry_tags.get().strip()
        tags: List[str] = [t.strip() for t in tags_raw.split(",") if t.strip()]

        if not title:
            messagebox.showwarning(
                "Validation Error", "Task title cannot be empty!"
            )
            return

        if due_date and not self._is_valid_date_format(due_date):
            messagebox.showerror(
                "Invalid Date",
                "Due date must be in YYYY-MM-DD format (e.g., 2026-10-15)."
            )
            return

        priority_text: str = "HIGH" if self.priority_var.get() == 2 else "LOW"

        new_task = self.task_manager.add_task(
            title=title, priority=priority_text, status="To Do",
            due_date=due_date, tags=tags
        )
        if not self._safe_save():
            return

        self._create_card_widget(
            new_task.task_id, title, priority_text, "To Do", due_date, tags
        )
        self.update_progress_bar()
        EventLogger.log_event(
            "TASK_CREATED", title,
            {"priority": priority_text, "due_date": due_date}
        )
        self.entry_title.delete(0, tk.END)

    def advance_card_status(self, card: KanbanCard) -> None:
        """Advances card to next Kanban column on single click."""
        if not card.winfo_exists():
            return
        title: str = card.task_title
        priority_text: str = card.task_priority

        matching_task = next(
            (t for t in self.task_manager.tasks if t.task_id == card.task_id),
            None
        )
        due_date: str = matching_task.due_date if matching_task else ""
        tags: List[str] = matching_task.tags if matching_task else []

        current_col: str = card.column_name
        next_col: Optional[str] = None

        if current_col == "To Do":
            next_col = "In Progress"
        elif current_col == "In Progress":
            next_col = "Done"
        elif current_col == "Done":
            self.task_manager.remove_task(card.task_id)
            if not self._safe_save():
                return
            if card in self.all_cards:
                self.all_cards.remove(card)
            card.destroy()
            self.update_progress_bar()
            return

        if not next_col:
            return

        for t in self.task_manager.tasks:
            if t.task_id == card.task_id:
                t.status = next_col
                if next_col == "Done":
                    t.mark_completed()
                break

        if not self._safe_save():
            return

        task_id: str = card.task_id
        if card in self.all_cards:
            self.all_cards.remove(card)
        card.destroy()

        self._create_card_widget(
            task_id, title, priority_text, next_col, due_date, tags
        )
        self.update_progress_bar()

        if next_col == "Done":
            EventLogger.log_event(
                "TASK_COMPLETED", title, {"priority": priority_text}
            )
