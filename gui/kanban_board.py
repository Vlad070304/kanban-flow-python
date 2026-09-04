import tkinter as tk
from tkinter import messagebox
import config


class KanbanBoard(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=config.BG_COLOR)
        self.parent = parent
        self.columns = ["To Do", "In Progress", "Done"]
        self.column_frames = {}
        
        # Track task cards for dynamic progress calculation
        self.total_cards = 0
        self.done_cards = 0
        
        # Build UI Sections
        self._setup_canvas_metric()
        self._setup_board_columns()
        self._setup_input_panel()
        self._bind_keyboard_events()

    def _setup_canvas_metric(self):
        # Creates a dynamic Tkinter Canvas progress bar at the top
        self.canvas = tk.Canvas(
            self, 
            height=35, 
            bg=config.FRAME_BG, 
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.X, padx=15, pady=(10, 5))
        
        # Recalculate canvas progress bar when window is resized
        self.canvas.bind("<Configure>", lambda e: self.update_progress_bar())

    def update_progress_bar(self):
        # Draws dynamic shapes and text on the Canvas based on completion ratio
        self.canvas.delete("all")
        width = self.canvas.winfo_width()
        if width <= 1:
            width = 880  # Default fallback width before render
            
        ratio = (self.done_cards / self.total_cards) if self.total_cards > 0 else 0.0
        fill_width = max(10, (width - 20) * ratio)

        # Draw outer background box
        self.canvas.create_rectangle(
            10, 5, width - 10, 30, 
            outline=config.TEXT_COLOR, 
            fill=config.BG_COLOR,
            width=1
        )
        # Draw filled progress bar
        self.canvas.create_rectangle(
            10, 5, fill_width, 30, 
            fill="#A6E3A1", 
            outline=""
        )
        # Draw progress text over canvas
        percent_str = f"Board Completion: {int(ratio * 100)}% ({self.done_cards}/{self.total_cards} Tasks)"
        self.canvas.create_text(
            width / 2, 17, 
            text=percent_str, 
            fill=config.TEXT_COLOR, 
            font=("Arial", 9, "bold")
        )

    def _setup_board_columns(self):
        # Creates 3 visual column frames side-by-side
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
        # Creates user input panel at the bottom
        panel = tk.Frame(self, bg=config.FRAME_BG, pady=10, padx=10)
        panel.pack(fill=tk.X, side=tk.BOTTOM)

        tk.Label(
            panel, 
            text="Task Title:", 
            fg=config.TEXT_COLOR, 
            bg=config.FRAME_BG,
            font=("Arial", 9, "bold")
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.entry_title = tk.Entry(panel, width=25, bg="#313244", fg=config.TEXT_COLOR, insertbackground="white")
        self.entry_title.pack(side=tk.LEFT, padx=5)

        tk.Label(
            panel, 
            text="Priority:", 
            fg=config.TEXT_COLOR, 
            bg=config.FRAME_BG,
            font=("Arial", 9, "bold")
        ).pack(side=tk.LEFT, padx=(15, 5))

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
            command=self.add_task_card
        )
        btn_add.pack(side=tk.LEFT, padx=15)

    def _bind_keyboard_events(self):
        # Binds global app key events for quicker navigation
        self.parent.bind("<Control-n>", lambda e: self.entry_title.focus_set())
        self.parent.bind("<Escape>", lambda e: self.entry_title.delete(0, tk.END))

    def add_task_card(self):
        # Validates input and dynamically renders a card with click event handlers
        title = self.entry_title.get().strip()
        
        if not title:
            messagebox.showwarning("Validation Error", "Task title cannot be empty!")
            return

        priority_text = "HIGH" if self.priority_var.get() == 2 else "LOW"
        priority_color = config.ACCENT_COLOR if priority_text == "HIGH" else config.TEXT_COLOR

        # Create Card Widget inside 'To Do'
        card = tk.Frame(self.column_frames["To Do"], bg=config.CARD_BG, bd=1, relief=tk.RAISED)
        card.pack(fill=tk.X, padx=8, pady=5)
        card.column_name = "To Do"

        lbl_title = tk.Label(
            card, text=title, fg=config.TEXT_COLOR, bg=config.CARD_BG, 
            font=("Arial", 10, "bold"), anchor="w"
        )
        lbl_title.pack(fill=tk.X, padx=8, pady=(6, 2))

        lbl_priority = tk.Label(
            card, text=f"Priority: {priority_text} | Click to Move ->", fg=priority_color, bg=config.CARD_BG, 
            font=("Arial", 8, "italic"), anchor="w"
        )
        lbl_priority.pack(fill=tk.X, padx=8, pady=(0, 6))

        # Event Binding: Bind Mouse Click to advance card status
        for widget in (card, lbl_title, lbl_priority):
            widget.bind("<Button-1>", lambda e, c=card: self._advance_card_status(c))

        # Update metrics
        self.total_cards += 1
        self.update_progress_bar()
        self.entry_title.delete(0, tk.END)

    def _advance_card_status(self, card):
        # Moves a task card across columns on click by extracting data and re-rendering
        title = card.winfo_children()[0].cget("text")
        priority_info = card.winfo_children()[1].cget("text")
        is_high = "HIGH" in priority_info

        current_col = card.column_name
        next_col = None
        
        if current_col == "To Do":
            next_col = "In Progress"
        elif current_col == "In Progress":
            next_col = "Done"
            self.done_cards += 1
        elif current_col == "Done":
            card.destroy()
            self.total_cards -= 1
            self.done_cards -= 1
            self.update_progress_bar()
            return

        # Safeguard if next_col was not assigned
        if not next_col:
            return

        # Destroy old card widget
        card.destroy()

        # Build new card in destination column
        new_card = tk.Frame(self.column_frames[next_col], bg=config.CARD_BG, bd=1, relief=tk.RAISED)
        new_card.pack(fill=tk.X, padx=8, pady=5)
        new_card.column_name = next_col

        priority_text = "HIGH" if is_high else "LOW"
        priority_color = config.ACCENT_COLOR if is_high else config.TEXT_COLOR

        lbl_title = tk.Label(
            new_card, text=title, fg=config.TEXT_COLOR, bg=config.CARD_BG, 
            font=("Arial", 10, "bold"), anchor="w"
        )
        lbl_title.pack(fill=tk.X, padx=8, pady=(6, 2))

        lbl_priority = tk.Label(
            new_card, text=f"Priority: {priority_text} | Click to Move ->", fg=priority_color, bg=config.CARD_BG, 
            font=("Arial", 8, "italic"), anchor="w"
        )
        lbl_priority.pack(fill=tk.X, padx=8, pady=(0, 6))

        # Re-bind click event to the new card
        for widget in (new_card, lbl_title, lbl_priority):
            widget.bind("<Button-1>", lambda e, c=new_card: self._advance_card_status(c))

        self.update_progress_bar()