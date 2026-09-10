"""Widget module representing an individual task card inside Kanban columns."""

import tkinter as tk
from typing import Any

import config
from models.task import Task


class KanbanCard(tk.Frame):
    """Card widget displaying task properties, subtasks, and action controls."""

    def __init__(self, parent: tk.Widget, board: Any, task: Task) -> None:
        """Initialize KanbanCard instance."""
        super().__init__(
            parent,
            bg=config.CARD_BG,
            bd=1,
            relief=tk.RAISED,
            padx=6,
            pady=6
        )
        self.parent: tk.Widget = parent
        self.board: Any = board
        self.task: Task = task

        self._setup_ui()
        self._bind_card_events()

    def _setup_ui(self) -> None:
        """Construct inner widgets for the card layout."""
        header_frame: tk.Frame = tk.Frame(self, bg=config.CARD_BG)
        header_frame.pack(fill=tk.X, expand=True)

        high_prio_color: str = getattr(config, "HIGH_PRIO_COLOR", "#F38BA8")
        low_prio_color: str = getattr(config, "LOW_PRIO_COLOR", "#89B4FA")

        prio_color: str = (
            high_prio_color
            if self.task.priority == "HIGH"
            else low_prio_color
        )

        lbl_priority: tk.Label = tk.Label(
            header_frame,
            text=f"[{self.task.priority}]",
            fg=prio_color,
            bg=config.CARD_BG,
            font=("Arial", 8, "bold")
        )
        lbl_priority.pack(side=tk.LEFT)

        lbl_title: tk.Label = tk.Label(
            header_frame,
            text=self.task.title,
            fg=config.TEXT_COLOR,
            bg=config.CARD_BG,
            font=("Arial", 10, "bold"),
            anchor="w",
            wraplength=180,
            justify=tk.LEFT
        )
        lbl_title.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))

        if self.task.due_date:
            lbl_due: tk.Label = tk.Label(
                self,
                text=f"Due: {self.task.due_date}",
                fg="#CDD6F4",
                bg=config.CARD_BG,
                font=("Arial", 8)
            )
            lbl_due.pack(anchor="w", pady=(2, 0))

        if self.task.tags:
            tags_frame: tk.Frame = tk.Frame(self, bg=config.CARD_BG)
            tags_frame.pack(fill=tk.X, pady=(2, 0))
            for tag in self.task.tags:
                lbl_tag: tk.Label = tk.Label(
                    tags_frame,
                    text=f"#{tag}",
                    fg=config.ACCENT_COLOR,
                    bg="#313244",
                    font=("Arial", 7, "bold"),
                    padx=3,
                    pady=1
                )
                lbl_tag.pack(side=tk.LEFT, padx=(0, 2))

        if self.task.subtasks:
            subtask_frame: tk.Frame = tk.Frame(self, bg=config.CARD_BG)
            subtask_frame.pack(fill=tk.X, pady=(4, 0))
            for idx, subtask in enumerate(self.task.subtasks):
                var = tk.BooleanVar(value=subtask.get("completed", False))
                chk = tk.Checkbutton(
                    subtask_frame,
                    text=subtask.get("title", ""),
                    variable=var,
                    bg=config.CARD_BG,
                    fg=config.TEXT_COLOR,
                    selectcolor=config.BG_COLOR,
                    activebackground=config.CARD_BG,
                    font=("Arial", 8),
                    command=lambda i=idx, v=var: self._toggle_subtask(i, v)
                )
                chk.pack(anchor="w")

        controls_frame: tk.Frame = tk.Frame(self, bg=config.CARD_BG)
        controls_frame.pack(fill=tk.X, pady=(6, 0))

        btn_left: tk.Button = tk.Button(
            controls_frame,
            text="◄",
            bg="#313244",
            fg=config.TEXT_COLOR,
            font=("Arial", 7),
            relief=tk.FLAT,
            command=lambda: self.board.move_card_horizontal(self, -1)
        )
        btn_left.pack(side=tk.LEFT, padx=1)

        btn_up: tk.Button = tk.Button(
            controls_frame,
            text="▲",
            bg="#313244",
            fg=config.TEXT_COLOR,
            font=("Arial", 7),
            relief=tk.FLAT,
            command=lambda: self.board.move_card_vertical(self, -1)
        )
        btn_up.pack(side=tk.LEFT, padx=1)

        btn_down: tk.Button = tk.Button(
            controls_frame,
            text="▼",
            bg="#313244",
            fg=config.TEXT_COLOR,
            font=("Arial", 7),
            relief=tk.FLAT,
            command=lambda: self.board.move_card_vertical(self, 1)
        )
        btn_down.pack(side=tk.LEFT, padx=1)

        btn_right: tk.Button = tk.Button(
            controls_frame,
            text="►",
            bg="#313244",
            fg=config.TEXT_COLOR,
            font=("Arial", 7),
            relief=tk.FLAT,
            command=lambda: self.board.move_card_horizontal(self, 1)
        )
        btn_right.pack(side=tk.LEFT, padx=1)

        btn_edit: tk.Button = tk.Button(
            controls_frame,
            text="Edit",
            bg=config.ACCENT_COLOR,
            fg="#11111B",
            font=("Arial", 7, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            command=self._trigger_edit
        )
        btn_edit.pack(side=tk.RIGHT, padx=1)

    def _bind_card_events(self) -> None:
        """Bind double-click and right-click actions to card frame and labels."""
        for widget in (self, *self.winfo_children()):
            if not isinstance(widget, (tk.Button, tk.Checkbutton)):
                widget.bind("<Double-Button-1>", lambda _e: self._trigger_edit())
                widget.bind("<Button-3>", self._show_context_menu)

    def _show_context_menu(self, event: tk.Event) -> None:
        """Display right-click context menu for editing options."""
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Edit Task", command=self._trigger_edit)
        menu.add_command(
            label="Move Left",
            command=lambda: self.board.move_card_horizontal(self, -1)
        )
        menu.add_command(
            label="Move Right",
            command=lambda: self.board.move_card_horizontal(self, 1)
        )
        menu.post(event.x_root, event.y_root)

    def _trigger_edit(self) -> None:
        """Pass task parameters to board edit dialog."""
        self.board.open_edit_dialog(
            self,
            self.task.title,
            self.task.priority,
            self.task.due_date,
            self.task.tags
        )

    def _toggle_subtask(self, index: int, var: tk.BooleanVar) -> None:
        """Update subtask completion state and persist board state."""
        if 0 <= index < len(self.task.subtasks):
            self.task.subtasks[index]["completed"] = var.get()
            self.board.save_board_state()
