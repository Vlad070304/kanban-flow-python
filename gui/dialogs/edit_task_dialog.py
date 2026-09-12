"""Modal dialog module for editing task properties in the Kanban board."""

import tkinter as tk
from tkinter import messagebox
from typing import Any, cast

import config


class EditTaskDialog(tk.Toplevel):
    """Modal dialog for editing task card attributes."""

    def __init__(self, parent: tk.Widget, board: Any, card: Any) -> None:
        super().__init__(parent)
        self.board = board
        self.card = card

        self.title("Edit Task")
        self.geometry("340x380")
        self.configure(bg=config.FRAME_BG)
        self.transient(cast(tk.Wm, parent))
        self.grab_set()

        self._build_ui()

    def _build_ui(self) -> None:
        tk.Label(
            self,
            text="Edit Task Title:",
            fg=config.TEXT_COLOR,
            bg=config.FRAME_BG,
            font=("Arial", 9, "bold"),
        ).pack(anchor="w", padx=15, pady=(12, 2))

        self.entry_title = tk.Entry(
            self, bg="#313244", fg=config.TEXT_COLOR, insertbackground="white"
        )
        self.entry_title.insert(0, self.card.task.title)
        self.entry_title.pack(fill=tk.X, padx=15, pady=2)

        tk.Label(
            self,
            text="Due Date (YYYY-MM-DD):",
            fg=config.TEXT_COLOR,
            bg=config.FRAME_BG,
            font=("Arial", 9, "bold"),
        ).pack(anchor="w", padx=15, pady=(6, 2))

        self.entry_due = tk.Entry(
            self, bg="#313244", fg=config.TEXT_COLOR, insertbackground="white"
        )
        self.entry_due.insert(0, self.card.task.due_date)
        self.entry_due.pack(fill=tk.X, padx=15, pady=2)

        tk.Label(
            self,
            text="Tags (comma-separated):",
            fg=config.TEXT_COLOR,
            bg=config.FRAME_BG,
            font=("Arial", 9, "bold"),
        ).pack(anchor="w", padx=15, pady=(6, 2))

        self.entry_tags = tk.Entry(
            self, bg="#313244", fg=config.TEXT_COLOR, insertbackground="white"
        )
        self.entry_tags.insert(0, ", ".join(self.card.task.tags))
        self.entry_tags.pack(fill=tk.X, padx=15, pady=2)

        tk.Label(
            self,
            text="Subtasks (one per line):",
            fg=config.TEXT_COLOR,
            bg=config.FRAME_BG,
            font=("Arial", 9, "bold"),
        ).pack(anchor="w", padx=15, pady=(6, 2))

        self.txt_subtasks = tk.Text(
            self,
            height=4,
            bg="#313244",
            fg=config.TEXT_COLOR,
            insertbackground="white",
            font=("Arial", 9),
        )
        if self.card.task.subtasks:
            sub_str = "\n".join([s.get("title", "") for s in self.card.task.subtasks])
            self.txt_subtasks.insert("1.0", sub_str)
        self.txt_subtasks.pack(fill=tk.X, padx=15, pady=2)

        self.prio_var = tk.IntVar(value=2 if self.card.task.priority == "HIGH" else 1)
        prio_frame = tk.Frame(self, bg=config.FRAME_BG)
        prio_frame.pack(fill=tk.X, padx=15, pady=6)

        tk.Radiobutton(
            prio_frame,
            text="Low",
            variable=self.prio_var,
            value=1,
            bg=config.FRAME_BG,
            fg=config.TEXT_COLOR,
            selectcolor=config.BG_COLOR,
        ).pack(side=tk.LEFT)

        tk.Radiobutton(
            prio_frame,
            text="High",
            variable=self.prio_var,
            value=2,
            bg=config.FRAME_BG,
            fg=config.ACCENT_COLOR,
            selectcolor=config.BG_COLOR,
        ).pack(side=tk.LEFT)

        tk.Button(
            self,
            text="Save Changes",
            bg=config.ACCENT_COLOR,
            fg="#11111B",
            font=("Arial", 9, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            command=self._save_changes,
        ).pack(pady=8)

    def _save_changes(self) -> None:
        new_title = self.entry_title.get().strip()
        new_due = self.entry_due.get().strip()
        new_tags = [t.strip() for t in self.entry_tags.get().split(",") if t.strip()]

        raw_subtasks = self.txt_subtasks.get("1.0", tk.END).strip()
        existing_map = {
            s.get("title"): s.get("completed", False) for s in self.card.task.subtasks
        }
        new_subtasks = []
        if raw_subtasks:
            for line in raw_subtasks.split("\n"):
                st_title = line.strip()
                if st_title:
                    new_subtasks.append(
                        {
                            "title": st_title,
                            "completed": existing_map.get(st_title, False),
                        }
                    )

        if not new_title:
            messagebox.showwarning("Validation Error", "Task title cannot be empty!")
            return

        if new_due and not self.board.is_valid_date_format(new_due):
            messagebox.showerror(
                "Invalid Date",
                "Due date must be in YYYY-MM-DD format (e.g., 2026-10-15).",
            )
            return

        new_prio = "HIGH" if self.prio_var.get() == 2 else "LOW"
        self.card.task.title = new_title
        self.card.task.priority = new_prio
        self.card.task.due_date = new_due
        self.card.task.tags = new_tags
        self.card.task.subtasks = new_subtasks

        col_name = self.card.task.status
        card_id = self.card.task.task_id

        if self.card in self.board.all_cards:
            self.board.all_cards.remove(self.card)
        self.card.destroy()

        self.board.create_card_widget(
            card_id,
            new_title,
            new_prio,
            col_name,
            new_due,
            new_tags,
            new_subtasks,
        )
        if self.board.save_board_state():
            self.destroy()
