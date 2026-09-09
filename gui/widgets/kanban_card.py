"""
gui/widgets/kanban_card.py
Custom Tkinter card widget representing individual tasks on the Kanban board.
"""

import datetime
import tkinter as tk
from typing import Any, List, Optional

import config


class KanbanCard(tk.Frame):
    """Custom Frame widget rendering task metadata, badges, and control buttons."""

    def __init__(
        self,
        parent: tk.Widget,
        board: Any,
        task_id: str,
        title: str,
        priority: str,
        column_name: str,
        due_date: str = "",
        tags: Optional[List[str]] = None
    ) -> None:
        self.board = board
        self.task_id: str = task_id
        self.task_title: str = title
        self.task_priority: str = priority
        self.column_name: str = column_name
        self.task_due_date: str = due_date
        self.tags: List[str] = tags if tags else []

        # Evaluate overdue status dynamically
        self.is_overdue: bool = self._check_if_overdue()

        # Dynamic border highlight: red for overdue, standard frame border otherwise
        border_color: str = "#F38BA8" if self.is_overdue else config.FRAME_BG
        border_width: int = 2 if self.is_overdue else 1

        super().__init__(
            parent,
            bg="#313244",
            bd=border_width,
            relief=tk.SOLID,
            highlightbackground=border_color,
            highlightthickness=border_width
        )

        self._build_card_ui()

    def _check_if_overdue(self) -> bool:
        # Evaluates if task due date is strictly prior to today and not completed
        if not self.task_due_date or self.column_name == "Done":
            return False
        try:
            due: datetime.date = datetime.datetime.strptime(
                self.task_due_date, "%Y-%m-%d"
            ).date()
            return due < datetime.date.today()
        except ValueError:
            return False

    def _build_card_ui(self) -> None:
        # Title Header with Click-to-Advance
        title_frame: tk.Frame = tk.Frame(self, bg="#313244")
        title_frame.pack(fill=tk.X, padx=6, pady=(6, 2))

        lbl_title: tk.Label = tk.Label(
            title_frame,
            text=self.task_title,
            fg=config.TEXT_COLOR,
            bg="#313244",
            font=("Arial", 10, "bold"),
            anchor="w",
            wraplength=180,
            justify=tk.LEFT,
            cursor="hand2"
        )
        lbl_title.pack(side=tk.LEFT, fill=tk.X, expand=True)
        lbl_title.bind(
            "<Button-1>", lambda e: self.board.advance_card_status(self)
        )

        # Metadata Row (Priority, Overdue Alert, Due Date)
        meta_frame: tk.Frame = tk.Frame(self, bg="#313244")
        meta_frame.pack(fill=tk.X, padx=6, pady=2)

        prio_color: str = (
            config.ACCENT_COLOR if self.task_priority == "HIGH" else "#A6ADC8"
        )
        lbl_prio: tk.Label = tk.Label(
            meta_frame,
            text=f"[{self.task_priority}]",
            fg=prio_color,
            bg="#313244",
            font=("Arial", 8, "bold")
        )
        lbl_prio.pack(side=tk.LEFT)

        # Add visual red overdue badge if task is past due
        if self.is_overdue:
            lbl_overdue: tk.Label = tk.Label(
                meta_frame,
                text="[OVERDUE]",
                fg="#F38BA8",
                bg="#313244",
                font=("Arial", 8, "bold")
            )
            lbl_overdue.pack(side=tk.LEFT, padx=(4, 0))

        if self.task_due_date:
            due_color: str = "#F38BA8" if self.is_overdue else "#A6ADC8"
            lbl_due: tk.Label = tk.Label(
                meta_frame,
                text=f"Due: {self.task_due_date}",
                fg=due_color,
                bg="#313244",
                font=("Arial", 8)
            )
            lbl_due.pack(side=tk.RIGHT)

        # Tags Row
        if self.tags:
            tags_frame: tk.Frame = tk.Frame(self, bg="#313244")
            tags_frame.pack(fill=tk.X, padx=6, pady=(0, 2))
            tags_str: str = " ".join([f"#{t}" for t in self.tags])
            lbl_tags: tk.Label = tk.Label(
                tags_frame,
                text=tags_str,
                fg="#89B4FA",
                bg="#313244",
                font=("Arial", 8, "italic")
            )
            lbl_tags.pack(side=tk.LEFT)

        # Controls Row (Shift up/down, Edit, Move left/right)
        btn_frame: tk.Frame = tk.Frame(self, bg="#313244")
        btn_frame.pack(fill=tk.X, padx=4, pady=(2, 4))

        # Vertical Reordering
        btn_up: tk.Button = tk.Button(
            btn_frame,
            text="▲",
            bg="#45475A",
            fg=config.TEXT_COLOR,
            font=("Arial", 7),
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            command=lambda: self.board.move_card_vertical(self, -1)
        )
        btn_up.pack(side=tk.LEFT, padx=1)

        btn_down: tk.Button = tk.Button(
            btn_frame,
            text="▼",
            bg="#45475A",
            fg=config.TEXT_COLOR,
            font=("Arial", 7),
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            command=lambda: self.board.move_card_vertical(self, 1)
        )
        btn_down.pack(side=tk.LEFT, padx=1)

        # Edit Dialog Trigger
        btn_edit: tk.Button = tk.Button(
            btn_frame,
            text="Edit",
            bg="#45475A",
            fg=config.TEXT_COLOR,
            font=("Arial", 7, "bold"),
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            command=lambda: self.board.open_edit_dialog(
                self,
                self.task_title,
                self.task_priority,
                self.task_due_date,
                self.tags
            )
        )
        btn_edit.pack(side=tk.LEFT, padx=4)

        # Horizontal Column Navigation
        btn_right: tk.Button = tk.Button(
            btn_frame,
            text="►",
            bg="#45475A",
            fg=config.TEXT_COLOR,
            font=("Arial", 7),
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            command=lambda: self.board.move_card_horizontal(self, 1)
        )
        btn_right.pack(side=tk.RIGHT, padx=1)

        btn_left: tk.Button = tk.Button(
            btn_frame,
            text="◄",
            bg="#45475A",
            fg=config.TEXT_COLOR,
            font=("Arial", 7),
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            command=lambda: self.board.move_card_horizontal(self, -1)
        )
        btn_left.pack(side=tk.RIGHT, padx=1)
