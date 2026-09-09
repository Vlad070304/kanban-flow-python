"""
gui/widgets/kanban_card.py
Custom Card Frame component for rendering individual task items.
"""

import datetime
import tkinter as tk
from typing import Any, List, Optional

import config


class KanbanCard(tk.Frame):
    """Custom Frame widget rendering a single task card in a Kanban column."""

    def __init__(
        self,
        parent: tk.Widget,
        board: Any,
        task_id: str,
        title: str,
        priority_text: str,
        column_name: str,
        due_date: str = "",
        tags: Optional[List[str]] = None
    ) -> None:
        super().__init__(parent, bg=config.CARD_BG, bd=1, relief=tk.RAISED)
        self.board: Any = board
        self.task_id: str = task_id
        self.task_title: str = title
        self.task_priority: str = priority_text
        self.column_name: str = column_name
        self.task_due_date: str = due_date
        self.task_tags: List[str] = tags if tags is not None else []
        self.click_after_id: Optional[str] = None

        self._build_card()

    def _build_card(self) -> None:
        """Constructs and binds events for card UI elements."""
        card_header: tk.Frame = tk.Frame(self, bg=config.CARD_BG)
        card_header.pack(fill=tk.X, padx=8, pady=(6, 1))

        lbl_title: tk.Label = tk.Label(
            card_header, text=self.task_title, fg=config.TEXT_COLOR,
            bg=config.CARD_BG, font=("Arial", 10, "bold"), anchor="w"
        )
        lbl_title.pack(side=tk.LEFT, fill=tk.X, expand=True)

        btn_right: tk.Button = tk.Button(
            card_header, text="►", bg=config.CARD_BG, fg=config.TEXT_COLOR,
            font=("Arial", 7), relief=tk.FLAT, bd=0, cursor="hand2",
            command=lambda: self.board.move_card_horizontal(self, 1)
        )
        btn_right.pack(side=tk.RIGHT, padx=2)

        btn_left: tk.Button = tk.Button(
            card_header, text="◄", bg=config.CARD_BG, fg=config.TEXT_COLOR,
            font=("Arial", 7), relief=tk.FLAT, bd=0, cursor="hand2",
            command=lambda: self.board.move_card_horizontal(self, -1)
        )
        btn_left.pack(side=tk.RIGHT, padx=2)

        btn_down: tk.Button = tk.Button(
            card_header, text="▼", bg=config.CARD_BG, fg=config.TEXT_COLOR,
            font=("Arial", 7), relief=tk.FLAT, bd=0, cursor="hand2",
            command=lambda: self.board.move_card_vertical(self, 1)
        )
        btn_down.pack(side=tk.RIGHT, padx=2)

        btn_up: tk.Button = tk.Button(
            card_header, text="▲", bg=config.CARD_BG, fg=config.TEXT_COLOR,
            font=("Arial", 7), relief=tk.FLAT, bd=0, cursor="hand2",
            command=lambda: self.board.move_card_vertical(self, -1)
        )
        btn_up.pack(side=tk.RIGHT, padx=2)

        due_color: str = config.TEXT_COLOR
        if self.task_due_date and self.column_name != "Done":
            try:
                d_date = datetime.datetime.strptime(
                    self.task_due_date, "%Y-%m-%d"
                ).date()
                today = datetime.date.today()
                if d_date < today:
                    due_color = "#F38BA8"
                elif d_date == today:
                    due_color = "#FAB387"
            except ValueError:
                pass

        meta_text: str = f"Prio: {self.task_priority}"
        if self.task_due_date:
            meta_text += f" | Due: {self.task_due_date}"
        if self.task_tags:
            meta_text += f" | Tags: {', '.join(self.task_tags)}"

        lbl_meta: tk.Label = tk.Label(
            self, text=meta_text, fg=due_color, bg=config.CARD_BG,
            font=("Arial", 8, "italic"), anchor="w"
        )
        lbl_meta.pack(fill=tk.X, padx=8, pady=(0, 2))

        lbl_action: tk.Label = tk.Label(
            self, text="Click to advance status ->", fg=config.TEXT_COLOR,
            bg=config.CARD_BG, font=("Arial", 7, "italic"), anchor="w"
        )
        lbl_action.pack(fill=tk.X, padx=8, pady=(0, 6))

        clickable_widgets = (self, lbl_title, lbl_meta, lbl_action, card_header)
        for widget in clickable_widgets:
            widget.bind("<Button-1>", self._handle_single_click)
            widget.bind("<Double-Button-1>", self._handle_double_click)

    def _handle_single_click(self, _event: tk.Event) -> None:
        """Schedules status advancement on single click."""
        if self.click_after_id is not None:
            self.after_cancel(self.click_after_id)
        self.click_after_id = self.after(
            250, lambda: self.board.advance_card_status(self)
        )

    def _handle_double_click(self, _event: tk.Event) -> None:
        """Cancels single click timer and opens edit dialog on double click."""
        if self.click_after_id is not None:
            self.after_cancel(self.click_after_id)
            self.click_after_id = None
        self.board.open_edit_dialog(
            self,
            self.task_title,
            self.task_priority,
            self.task_due_date,
            self.task_tags
        )
