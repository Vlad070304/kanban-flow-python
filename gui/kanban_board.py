import json
import os
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox
import config


class KanbanBoard(tk.Frame):
    DATA_FILE = "kanban_data.json"

    def __init__(self, parent):
        # Initializes board state, UI structure, and loads saved task data.
        super().__init__(parent, bg=config.BG_COLOR)
        self.parent = parent
        self.columns = ["To Do", "In Progress", "Done"]
        self.column_frames = {}

        self.total_cards = 0
        self.done_cards = 0

        self._setup_canvas_metric()
        self._setup_board_columns()
        self._setup_input_panel()
        self._bind_keyboard_events()

        self.load_board_data()

    def _setup_canvas_metric(self):
        # Creates dynamic Tkinter Canvas progress bar widget.
        self.canvas = tk.Canvas(
            self,
            height=35,
            bg=config.FRAME_BG,
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.X, padx=15, pady=(10, 5))
        self.canvas.bind("<Configure>", self._on_canvas_resize)

    def _on_canvas_resize(self, _event):
        # Event handler to recalculate canvas render on window resize.
        self.update_progress_bar()

    def update_progress_bar(self):
        # Recalculates card counts and updates the progress bar visually.
        total = 0
        done = 0
        for col_name, frame in self.column_frames.items():
            count = len(frame.winfo_children())
            total += count
            if col_name == "Done":
                done += count

        self.total_cards = total
        self.done_cards = done

        self.canvas.delete("all")
        width = self.canvas.winfo_width()
        if width <= 1:
            width = 880

        ratio = (self.done_cards / self.total_cards) if self.total_cards > 0 else 0.0
        fill_width = max(10, (width - 20) * ratio)

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
        percent_str = (
            f"Board Completion: {int(ratio * 100)}% "
            f"({self.done_cards}/{self.total_cards} Tasks)"
        )
        self.canvas.create_text(
            width / 2, 17,
            text=percent_str,
            fill=config.TEXT_COLOR,
            font=("Arial", 9, "bold")
        )

    def _setup_board_columns(self):
        # Renders column frames side-by-side.
        board_container = tk.Frame(self, bg=config.BG_COLOR)
        board_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        for col_name in self.columns:
            col_frame = tk.LabelFrame(
                board_container,
                text=f"  {col_name}  ",
                bg=config.FRAME_BG,
                fg=config.TEXT_COLOR,
                font=("Arial", 11, "bold"),
                bd=2,
                relief=tk.GROOVE
            )
            col_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
            self.column_frames[col_name] = col_frame

    def _setup_input_panel(self):
        # Renders input controls panel at the bottom.
        panel = tk.Frame(self, bg=config.FRAME_BG, pady=10, padx=10)
        panel.pack(fill=tk.X, side=tk.BOTTOM)

        tk.Label(
            panel,
            text="Task Title:",
            fg=config.TEXT_COLOR,
            bg=config.FRAME_BG,
            font=("Arial", 9, "bold")
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.entry_title = tk.Entry(
            panel, width=18, bg="#313244", fg=config.TEXT_COLOR, insertbackground="white"
        )
        self.entry_title.pack(side=tk.LEFT, padx=5)

        tk.Label(
            panel,
            text="Priority:",
            fg=config.TEXT_COLOR,
            bg=config.FRAME_BG,
            font=("Arial", 9, "bold")
        ).pack(side=tk.LEFT, padx=(5, 5))

        self.priority_var = tk.IntVar(value=1)
        tk.Radiobutton(
            panel, text="Low", variable=self.priority_var, value=1,
            bg=config.FRAME_BG, fg=config.TEXT_COLOR, selectcolor=config.BG_COLOR
        ).pack(side=tk.LEFT)

        tk.Radiobutton(
            panel, text="High", variable=self.priority_var, value=2,
            bg=config.FRAME_BG, fg=config.ACCENT_COLOR, selectcolor=config.BG_COLOR
        ).pack(side=tk.LEFT)

        btn_add = tk.Button(
            panel,
            text="+ Add Card",
            bg=config.ACCENT_COLOR,
            fg="#11111B",
            font=("Arial", 9, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            command=self.add_task_card
        )
        btn_add.pack(side=tk.LEFT, padx=5)

        btn_timer = tk.Button(
            panel,
            text="Start 10s Focus",
            bg="#FAB387",
            fg="#11111B",
            font=("Arial", 9, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            command=self._on_timer_button_click
        )
        btn_timer.pack(side=tk.LEFT, padx=5)

        btn_clear_done = tk.Button(
            panel,
            text="Clear Done",
            bg="#F38BA8",
            fg="#11111B",
            font=("Arial", 9, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            command=self.clear_done_tasks
        )
        btn_clear_done.pack(side=tk.LEFT, padx=5)

        # Attach interactive hover effects
        self._apply_hover_effect(btn_add, config.ACCENT_COLOR, config.BTN_HOVER_ADD)
        self._apply_hover_effect(btn_timer, "#FAB387", config.BTN_HOVER_TIMER)
        self._apply_hover_effect(btn_clear_done, "#F38BA8", config.BTN_HOVER_CLEAR)

    def _apply_hover_effect(self, widget: tk.Widget, default_bg: str, hover_bg: str):
        # Dynamically alters widget background color on mouse hover events.
        widget.bind("<Enter>", lambda e: widget.config(bg=hover_bg))
        widget.bind("<Leave>", lambda e: widget.config(bg=default_bg))

    def _on_timer_button_click(self):
        # Handler for focus timer trigger button.
        self.start_focus_timer(10)

    def _bind_keyboard_events(self):
        # Binds global app key shortcuts.
        self.parent.bind("<Control-n>", self._on_focus_shortcut)
        self.parent.bind("<Escape>", self._on_clear_shortcut)

    def _on_focus_shortcut(self, _event):
        # Sets focus to the title input entry widget.
        self.entry_title.focus_set()

    def _on_clear_shortcut(self, _event):
        # Clears text from title entry widget.
        self.entry_title.delete(0, tk.END)

    def save_board_data(self):
        # Serializes board state into local JSON file.
        data = []
        for col_name, frame in self.column_frames.items():
            for card in frame.winfo_children():
                labels = card.winfo_children()
                if len(labels) >= 2:
                    title = labels[0].cget("text")
                    is_high = "HIGH" in labels[1].cget("text")
                    data.append({
                        "title": title,
                        "status": col_name,
                        "priority": "HIGH" if is_high else "LOW"
                    })
        try:
            with open(self.DATA_FILE, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)
        except (IOError, TypeError) as err:
            print(f"Error saving data: {err}")

    def load_board_data(self):
        # Populates board components from saved JSON file.
        if not os.path.exists(self.DATA_FILE):
            return

        try:
            with open(self.DATA_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)

            for item in data:
                title = item.get("title", "")
                status = item.get("status", "To Do")
                priority = item.get("priority", "LOW")
                if title and status in self.column_frames:
                    self._create_card_widget(title, priority, status)

            self.update_progress_bar()
        except (IOError, json.JSONDecodeError) as err:
            print(f"Error loading data: {err}")

    def _create_card_widget(self, title: str, priority_text: str, column_name: str):
        # Creates card frame element in designated column.
        priority_color = (
            config.ACCENT_COLOR if priority_text == "HIGH" else config.TEXT_COLOR
        )

        card = tk.Frame(
            self.column_frames[column_name], bg=config.CARD_BG, bd=1, relief=tk.RAISED
        )
        card.pack(fill=tk.X, padx=8, pady=5)
        card.column_name = column_name

        lbl_title = tk.Label(
            card, text=title, fg=config.TEXT_COLOR, bg=config.CARD_BG,
            font=("Arial", 10, "bold"), anchor="w"
        )
        lbl_title.pack(fill=tk.X, padx=8, pady=(6, 2))

        lbl_priority = tk.Label(
            card, text=f"Priority: {priority_text} | Click to Move ->",
            fg=priority_color, bg=config.CARD_BG,
            font=("Arial", 8, "italic"), anchor="w"
        )
        lbl_priority.pack(fill=tk.X, padx=8, pady=(0, 6))

        for widget in (card, lbl_title, lbl_priority):
            widget.bind("<Button-1>", lambda e, c=card: self._advance_card_status(c))

    def clear_done_tasks(self):
        # Removes all tasks in the 'Done' column and saves changes.
        done_frame = self.column_frames["Done"]
        for card in done_frame.winfo_children():
            card.destroy()

        self.update_progress_bar()
        self.save_board_data()

    def start_focus_timer(self, duration_sec: int):
        # Spawns background timer thread.
        def timer_worker():
            time.sleep(duration_sec)
            self.after(
                0,
                lambda: messagebox.showinfo(
                    "Focus Session", f"🎉 Focus timer of {duration_sec}s completed!"
                )
            )

        thread = threading.Thread(target=timer_worker, daemon=True)
        thread.start()

    def export_csv_async(self):
        # Prompts dialog and writes board contents to CSV asynchronously.
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if not filepath:
            return

        def export_worker():
            try:
                lines = ["Title,Status,Priority\n"]
                for col_name, frame in self.column_frames.items():
                    for card in frame.winfo_children():
                        labels = card.winfo_children()
                        if len(labels) >= 2:
                            title = labels[0].cget("text").replace(",", " ")
                            is_high = "HIGH" in labels[1].cget("text")
                            priority_str = "HIGH" if is_high else "LOW"
                            lines.append(f"{title},{col_name},{priority_str}\n")

                with open(filepath, "w", encoding="utf-8") as file:
                    file.writelines(lines)

                self.after(
                    0,
                    lambda: messagebox.showinfo(
                        "Export Success", f"Board exported to:\n{filepath}"
                    )
                )
            except IOError as err:
                self.after(
                    0,
                    lambda: messagebox.showerror(
                        "Export Error", f"Failed to export CSV: {err}"
                    )
                )

        threading.Thread(target=export_worker, daemon=True).start()

    def add_task_card(self):
        # Validates entry, renders task card, and persists data.
        title = self.entry_title.get().strip()

        if not title:
            messagebox.showwarning("Validation Error", "Task title cannot be empty!")
            return

        priority_text = "HIGH" if self.priority_var.get() == 2 else "LOW"

        self._create_card_widget(title, priority_text, "To Do")
        self.update_progress_bar()
        self.save_board_data()
        self.entry_title.delete(0, tk.END)

    def _advance_card_status(self, card):
        # Advances task card column or removes it, updating persistent state.
        title = card.winfo_children()[0].cget("text")
        priority_info = card.winfo_children()[1].cget("text")
        is_high = "HIGH" in priority_info

        current_col = card.column_name
        next_col = None

        if current_col == "To Do":
            next_col = "In Progress"
        elif current_col == "In Progress":
            next_col = "Done"
        elif current_col == "Done":
            card.destroy()
            self.update_progress_bar()
            self.save_board_data()
            return

        if not next_col:
            return

        card.destroy()

        priority_text = "HIGH" if is_high else "LOW"
        self._create_card_widget(title, priority_text, next_col)
        self.update_progress_bar()
        self.save_board_data()