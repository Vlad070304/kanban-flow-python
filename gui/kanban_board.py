"""
gui/kanban_board.py
Kanban board component handling task rendering, TaskManager integration,
card editing dialogs, asynchronous focus timers, background thread exports,
and event logging with robust error handling and logging.
"""

import concurrent.futures
import logging
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Any, Dict, List, Optional, Tuple

import config
from gui.analytics import AnalyticsWindow
from services.event_logger import EventLogger
from services.task_manager import TaskManager

# Configure built-in logging module to track background and I/O failures silently
logging.basicConfig(
    filename="app_error.log",
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
LOGGER: logging.Logger = logging.getLogger(__name__)

# Thread pool executor for background I/O operations
THREAD_EXECUTOR: concurrent.futures.ThreadPoolExecutor = (
    concurrent.futures.ThreadPoolExecutor(max_workers=2)
)


class FocusTimerDialog(tk.Toplevel):
    """Modal dialog providing Pomodoro presets and custom focus session controls."""

    def __init__(self, parent: tk.Widget, board_ref: Any) -> None:
        """Initializes dialog components and sets up modal focus."""
        super().__init__(parent)
        self.board: Any = board_ref

        self.title("Focus Timer & Pomodoro")
        self.geometry("340x240")
        self.configure(bg=config.FRAME_BG)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self) -> None:
        """Constructs dialog controls and preset selection buttons."""
        tk.Label(
            self,
            text="Pomodoro & Focus Timer",
            fg=config.TEXT_COLOR,
            bg=config.FRAME_BG,
            font=("Arial", 12, "bold")
        ).pack(pady=(15, 5))

        tk.Label(
            self,
            text="Select a preset or enter custom minutes:",
            fg=config.TEXT_COLOR,
            bg=config.FRAME_BG,
            font=("Arial", 9)
        ).pack(pady=(0, 10))

        preset_frame: tk.Frame = tk.Frame(self, bg=config.FRAME_BG)
        preset_frame.pack(fill=tk.X, padx=20, pady=5)

        btn_25: tk.Button = tk.Button(
            preset_frame, text="25m Focus", bg=config.ACCENT_COLOR, fg="#11111B",
            font=("Arial", 9, "bold"), relief=tk.FLAT, cursor="hand2",
            command=lambda: self._start_session(25)
        )
        btn_25.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        btn_15: tk.Button = tk.Button(
            preset_frame, text="15m Break", bg="#89B4FA", fg="#11111B",
            font=("Arial", 9, "bold"), relief=tk.FLAT, cursor="hand2",
            command=lambda: self._start_session(15)
        )
        btn_15.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        btn_5: tk.Button = tk.Button(
            preset_frame, text="5m Rest", bg="#A6E3A1", fg="#11111B",
            font=("Arial", 9, "bold"), relief=tk.FLAT, cursor="hand2",
            command=lambda: self._start_session(5)
        )
        btn_5.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        custom_frame: tk.Frame = tk.Frame(self, bg=config.FRAME_BG)
        custom_frame.pack(fill=tk.X, padx=20, pady=12)

        tk.Label(
            custom_frame, text="Custom (mins):", fg=config.TEXT_COLOR,
            bg=config.FRAME_BG, font=("Arial", 9, "bold")
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.custom_entry: tk.Entry = tk.Entry(
            custom_frame, width=8, bg="#313244", fg=config.TEXT_COLOR,
            insertbackground="white"
        )
        self.custom_entry.insert(0, "10")
        self.custom_entry.pack(side=tk.LEFT, padx=5)

        btn_custom: tk.Button = tk.Button(
            custom_frame, text="Start", bg="#FAB387", fg="#11111B",
            font=("Arial", 9, "bold"), relief=tk.FLAT, cursor="hand2",
            command=self._start_custom
        )
        btn_custom.pack(side=tk.LEFT, padx=5)

        if getattr(self.board, "_timer_running", False):
            btn_stop: tk.Button = tk.Button(
                self, text="Stop Current Session", bg="#F38BA8", fg="#11111B",
                font=("Arial", 9, "bold"), relief=tk.FLAT, cursor="hand2",
                command=self._stop_session
            )
            btn_stop.pack(pady=5)

    def _start_session(self, minutes: int) -> None:
        """Dispatches active target minutes to board manager and closes modal."""
        self.board.start_focus_timer(minutes)
        self.destroy()

    def _start_custom(self) -> None:
        """Validates entry value and triggers background focus timer."""
        val: str = self.custom_entry.get().strip()
        if val.isdigit() and int(val) > 0:
            self._start_session(int(val))
        else:
            messagebox.showwarning(
                "Invalid Input", "Please enter a valid positive integer."
            )

    def _stop_session(self) -> None:
        """Triggers timer cancellation on active board component."""
        self.board.cancel_focus_timer()
        self.destroy()


class KanbanBoard(tk.Frame):
    """Main Kanban board frame managing task views and background tasks."""

    DATA_FILE: str = "kanban_data.json"

    def __init__(self, parent: tk.Widget) -> None:
        """Initializes board layout, state, and loads stored task data."""
        super().__init__(parent, bg=config.BG_COLOR)
        self.parent: tk.Widget = parent
        self.columns: List[str] = ["To Do", "In Progress", "Done"]
        self.column_frames: Dict[str, tk.LabelFrame] = {}

        self.task_manager: TaskManager = TaskManager(self.DATA_FILE)

        self.total_cards: int = 0
        self.done_cards: int = 0
        self._timer_running: bool = False

        self._setup_canvas_metric()
        self._setup_board_columns()
        self._setup_input_panel()
        self._bind_keyboard_events()

        self.load_board_data()

    def _safe_save(self) -> bool:
        """Persists task data, logging failures silently and alerting via dialog."""
        try:
            self.task_manager.save_to_file()
            return True
        except (IOError, OSError, PermissionError) as err:
            LOGGER.error("Error saving task data: %s", err)
            messagebox.showerror(
                "Save Error",
                f"Failed to save data changes:\n{err}"
            )
            return False

    def _setup_canvas_metric(self) -> None:
        """Creates dynamic Tkinter Canvas progress bar widget."""
        self.canvas: tk.Canvas = tk.Canvas(
            self,
            height=35,
            bg=config.FRAME_BG,
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.X, padx=15, pady=(10, 5))
        self.canvas.bind("<Configure>", self._on_canvas_resize)

    def _on_canvas_resize(self, _event: tk.Event) -> None:
        """Event handler to recalculate canvas render on window resize."""
        self.update_progress_bar()

    def update_progress_bar(self) -> None:
        """Recalculates card counts and renders progress state if idle."""
        if self._timer_running:
            return

        self.total_cards = len(self.task_manager.tasks)
        self.done_cards = len(
            [t for t in self.task_manager.tasks if t.status == "Done"]
        )

        self.canvas.delete("all")
        width: int = self.canvas.winfo_width() or 880

        ratio: float = (
            (self.done_cards / self.total_cards)
            if self.total_cards > 0 else 0.0
        )
        fill_width: float = max(10.0, (width - 20) * ratio)

        self.canvas.create_rectangle(
            10, 5, width - 10, 30,
            outline=config.TEXT_COLOR,
            fill=config.BG_COLOR,
            width=1
        )
        self.canvas.create_rectangle(
            10, 5, fill_width, 30,
            fill="#A6E3A1",
            outline=""
        )
        percent_str: str = (
            f"Board Completion: {int(ratio * 100)}% "
            f"({self.done_cards}/{self.total_cards} Tasks)"
        )
        self.canvas.create_text(
            width / 2, 17,
            text=percent_str,
            fill=config.TEXT_COLOR,
            font=("Arial", 9, "bold")
        )

    def _setup_board_columns(self) -> None:
        """Renders column frames side-by-side."""
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
                relief=tk.GROOVE
            )
            col_frame.pack(
                side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5
            )
            self.column_frames[col_name] = col_frame

    def _setup_input_panel(self) -> None:
        """Renders input controls panel at the bottom."""
        panel: tk.Frame = tk.Frame(self, bg=config.FRAME_BG, pady=10, padx=10)
        panel.pack(fill=tk.X, side=tk.BOTTOM)

        tk.Label(
            panel, text="Task Title:", fg=config.TEXT_COLOR, bg=config.FRAME_BG,
            font=("Arial", 9, "bold")
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.entry_title: tk.Entry = tk.Entry(
            panel, width=18, bg="#313244", fg=config.TEXT_COLOR,
            insertbackground="white"
        )
        self.entry_title.pack(side=tk.LEFT, padx=5)

        tk.Label(
            panel, text="Priority:", fg=config.TEXT_COLOR, bg=config.FRAME_BG,
            font=("Arial", 9, "bold")
        ).pack(side=tk.LEFT, padx=(5, 5))

        self.priority_var: tk.IntVar = tk.IntVar(value=1)
        tk.Radiobutton(
            panel, text="Low", variable=self.priority_var, value=1,
            bg=config.FRAME_BG, fg=config.TEXT_COLOR, selectcolor=config.BG_COLOR
        ).pack(side=tk.LEFT)

        tk.Radiobutton(
            panel, text="High", variable=self.priority_var, value=2,
            bg=config.FRAME_BG, fg=config.ACCENT_COLOR,
            selectcolor=config.BG_COLOR
        ).pack(side=tk.LEFT)

        btn_add: tk.Button = tk.Button(
            panel, text="+ Add Card", bg=config.ACCENT_COLOR, fg="#11111B",
            font=("Arial", 9, "bold"), relief=tk.FLAT, cursor="hand2",
            command=self.add_task_card
        )
        btn_add.pack(side=tk.LEFT, padx=5)

        btn_timer: tk.Button = tk.Button(
            panel, text="Focus Timer", bg="#FAB387", fg="#11111B",
            font=("Arial", 9, "bold"), relief=tk.FLAT, cursor="hand2",
            command=self.open_timer_dialog
        )
        btn_timer.pack(side=tk.LEFT, padx=5)

        btn_analytics: tk.Button = tk.Button(
            panel, text="Analytics", bg="#89B4FA", fg="#11111B",
            font=("Arial", 9, "bold"), relief=tk.FLAT, cursor="hand2",
            command=lambda: AnalyticsWindow(self.parent, self)
        )
        btn_analytics.pack(side=tk.LEFT, padx=5)

        btn_clear_done: tk.Button = tk.Button(
            panel, text="Clear Done", bg="#F38BA8", fg="#11111B",
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
        """Dynamically alters widget background color on mouse hover events."""
        widget.bind("<Enter>", lambda e: widget.config(bg=hover_bg))
        widget.bind("<Leave>", lambda e: widget.config(bg=default_bg))

    def open_timer_dialog(self) -> None:
        """Instantiates and displays top-level modal timer dialog."""
        FocusTimerDialog(self.parent, self)

    def start_focus_timer(self, minutes: int = 25) -> None:
        """Spawns thread worker and streams live countdown state to main UI."""
        if self._timer_running:
            messagebox.showwarning(
                "Timer Running", "A focus timer is already active!"
            )
            return

        self._timer_running = True
        total_seconds: int = minutes * 60
        EventLogger.log_event(
            "FOCUS_SESSION_STARTED",
            f"{minutes}m Session",
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
        """Aborts active timer session and resets board display."""
        if self._timer_running:
            self._timer_running = False
            EventLogger.log_event(
                "FOCUS_SESSION_CANCELLED", "Focus Session", {}
            )
            self.update_progress_bar()
            messagebox.showinfo("Timer Cancelled", "Focus session was stopped.")

    def _draw_timer_canvas(self, text_str: str) -> None:
        """Renders live countdown bar on top of board header canvas."""
        self.canvas.delete("all")
        width: int = self.canvas.winfo_width() or 880

        self.canvas.create_rectangle(
            10, 5, width - 10, 30,
            outline="#FAB387", fill=config.FRAME_BG, width=2
        )
        self.canvas.create_text(
            width / 2, 17, text=text_str, fill="#FAB387",
            font=("Arial", 10, "bold")
        )

    def _on_timer_completed(self, minutes: int) -> None:
        """Triggers when session thread completes cleanly without cancel."""
        self.update_progress_bar()
        EventLogger.log_event(
            "FOCUS_SESSION_COMPLETED",
            f"{minutes}m Session",
            {"duration_min": minutes}
        )
        msg: str = (
            f"Great job! Your {minutes}-minute focus session is complete."
        )
        messagebox.showinfo("Focus Complete", msg)

    def export_csv_async(self) -> None:
        """Executes file export asynchronously using thread pool."""
        filepath: str = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if not filepath:
            return

        snapshot: List[Tuple[str, str, str]] = [
            (t.title, t.status, t.priority) for t in self.task_manager.tasks
        ]

        def write_file_task(
            data: List[Tuple[str, str, str]], path: str
        ) -> int:
            lines: List[str] = ["Title,Status,Priority\n"]
            for title, status, priority in data:
                clean_title: str = title.replace(",", " ")
                lines.append(f"{clean_title},{status},{priority}\n")

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
        """Binds global app key shortcuts."""
        self.parent.bind(
            "<Control-n>", lambda e: self.entry_title.focus_set()
        )
        self.parent.bind(
            "<Escape>", lambda e: self.entry_title.delete(0, tk.END)
        )

    def load_board_data(self) -> None:
        """Populates board components from TaskManager state."""
        try:
            tasks = self.task_manager.load_from_file()
            for task in tasks:
                if task.status in self.column_frames:
                    self._create_card_widget(
                        task.task_id, task.title, task.priority, task.status
                    )
        except (IOError, OSError, PermissionError) as err:
            LOGGER.error("Failed to load task data from file: %s", err)
            messagebox.showerror(
                "Load Error", f"Could not load saved task data:\n{err}"
            )
        self.update_progress_bar()

    def _open_edit_dialog(
        self, card: tk.Widget, title: str, priority_text: str
    ) -> None:
        """Opens top-level modal dialog to modify card title and priority."""
        dialog: tk.Toplevel = tk.Toplevel(self)
        dialog.title("Edit Task")
        dialog.geometry("320x170")
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

        prio_var: tk.IntVar = tk.IntVar(
            value=2 if priority_text == "HIGH" else 1
        )
        prio_frame: tk.Frame = tk.Frame(dialog, bg=config.FRAME_BG)
        prio_frame.pack(fill=tk.X, padx=15, pady=5)

        tk.Radiobutton(
            prio_frame, text="Low Priority", variable=prio_var, value=1,
            bg=config.FRAME_BG, fg=config.TEXT_COLOR,
            selectcolor=config.BG_COLOR
        ).pack(side=tk.LEFT)

        tk.Radiobutton(
            prio_frame, text="High Priority", variable=prio_var, value=2,
            bg=config.FRAME_BG, fg=config.ACCENT_COLOR,
            selectcolor=config.BG_COLOR
        ).pack(side=tk.LEFT)

        def save_changes() -> None:
            new_title: str = entry.get().strip()
            if new_title:
                new_prio: str = "HIGH" if prio_var.get() == 2 else "LOW"

                for t in self.task_manager.tasks:
                    if t.task_id == card.task_id:
                        t.title = new_title
                        t.priority = new_prio
                        break

                col_name: str = card.column_name
                card_id: str = card.task_id
                card.destroy()
                self._create_card_widget(
                    card_id, new_title, new_prio, col_name
                )
                if self._safe_save():
                    dialog.destroy()

        tk.Button(
            dialog, text="Save Changes", bg=config.ACCENT_COLOR, fg="#11111B",
            font=("Arial", 9, "bold"), relief=tk.FLAT, cursor="hand2",
            command=save_changes
        ).pack(pady=10)

    def _create_card_widget(
        self,
        task_id: str,
        title: str,
        priority_text: str,
        column_name: str
    ) -> None:
        """Creates card frame element in designated column with clicks."""
        priority_color: str = (
            config.ACCENT_COLOR if priority_text == "HIGH"
            else config.TEXT_COLOR
        )

        card: tk.Frame = tk.Frame(
            self.column_frames[column_name], bg=config.CARD_BG, bd=1,
            relief=tk.RAISED
        )
        card.pack(fill=tk.X, padx=8, pady=5)
        card.column_name = column_name
        card.task_id = task_id

        lbl_title: tk.Label = tk.Label(
            card, text=title, fg=config.TEXT_COLOR, bg=config.CARD_BG,
            font=("Arial", 10, "bold"), anchor="w"
        )
        lbl_title.pack(fill=tk.X, padx=8, pady=(6, 2))

        lbl_priority: tk.Label = tk.Label(
            card, text=f"Priority: {priority_text} | Click to Move ->",
            fg=priority_color, bg=config.CARD_BG,
            font=("Arial", 8, "italic"), anchor="w"
        )
        lbl_priority.pack(fill=tk.X, padx=8, pady=(0, 6))

        card.click_after_id = None

        def handle_single_click(
            _event: tk.Event, target_card: tk.Widget
        ) -> None:
            if target_card.click_after_id is not None:
                self.after_cancel(target_card.click_after_id)

            target_card.click_after_id = self.after(
                250, lambda: self._advance_card_status(target_card)
            )

        def handle_double_click(
            _event: tk.Event,
            target_card: tk.Widget,
            t_title: str,
            t_priority: str
        ) -> None:
            if target_card.click_after_id is not None:
                self.after_cancel(target_card.click_after_id)
                target_card.click_after_id = None

            self._open_edit_dialog(target_card, t_title, t_priority)

        for widget in (card, lbl_title, lbl_priority):
            widget.bind(
                "<Button-1>", lambda e, c=card: handle_single_click(e, c)
            )
            widget.bind(
                "<Double-Button-1>",
                lambda e, c=card, t=title, p=priority_text: (
                    handle_double_click(e, c, t, p)
                )
            )

    def clear_done_tasks(self) -> None:
        """Removes all tasks in the 'Done' column and updates UI."""
        self.task_manager.clear_done()
        if not self._safe_save():
            return

        done_frame: tk.LabelFrame = self.column_frames["Done"]
        for card in done_frame.winfo_children():
            card.destroy()

        self.update_progress_bar()

    def add_task_card(self) -> None:
        """Validates entry, persists data, renders card, and logs event."""
        title: str = self.entry_title.get().strip()

        if not title:
            messagebox.showwarning(
                "Validation Error", "Task title cannot be empty!"
            )
            return

        priority_text: str = (
            "HIGH" if self.priority_var.get() == 2 else "LOW"
        )

        new_task = self.task_manager.add_task(title, priority_text, "To Do")
        if not self._safe_save():
            return

        self._create_card_widget(
            new_task.task_id, title, priority_text, "To Do"
        )
        self.update_progress_bar()

        EventLogger.log_event(
            "TASK_CREATED", title, {"priority": priority_text}
        )
        self.entry_title.delete(0, tk.END)

    def _advance_card_status(self, card: tk.Widget) -> None:
        """Advances task card column or removes it, updating state."""
        title: str = card.winfo_children()[0].cget("text")
        priority_info: str = card.winfo_children()[1].cget("text")
        is_high: bool = "HIGH" in priority_info
        priority_text: str = "HIGH" if is_high else "LOW"

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
        card.destroy()

        self._create_card_widget(task_id, title, priority_text, next_col)
        self.update_progress_bar()

        if next_col == "Done":
            EventLogger.log_event(
                "TASK_COMPLETED", title, {"priority": priority_text}
            )
