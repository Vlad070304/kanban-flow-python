import tkinter as tk
from tkinter import messagebox
import config


class KanbanBoard(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=config.BG_COLOR)
        self.parent = parent
        self.columns = ["To Do", "In Progress", "Done"]
        self.column_frames = {}
        
        # Build board layout and bottom input controls
        self._setup_board_columns()
        self._setup_input_panel()

    def _setup_board_columns(self):
        """Creates 3 visual column frames side-by-side."""
        board_container = tk.Frame(self, bg=config.BG_COLOR)
        board_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        for col_name in self.columns:
            # Column Frame Wrapper
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
            
            # Save reference to frame for card injection
            self.column_frames[col_name] = col_frame

    def _setup_input_panel(self):
        #Creates user input panel at the bottom for creating new cards.
        panel = tk.Frame(self, bg=config.FRAME_BG, pady=10, padx=10)
        panel.pack(fill=tk.X, side=tk.BOTTOM)

        # Title Input
        tk.Label(
            panel, 
            text="Task Title:", 
            fg=config.TEXT_COLOR, 
            bg=config.FRAME_BG,
            font=("Arial", 9, "bold")
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.entry_title = tk.Entry(panel, width=25, bg="#313244", fg=config.TEXT_COLOR, insertbackground="white")
        self.entry_title.pack(side=tk.LEFT, padx=5)

        # Priority Radio Buttons
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

        # Add Task Button
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

    def add_task_card(self):
        """Validates input and dynamically renders a card frame into 'To Do'."""
        title = self.entry_title.get().strip()
        
        # Validation Check
        if not title:
            messagebox.showwarning("Validation Error", "Task title cannot be empty!")
            return

        priority_text = "HIGH" if self.priority_var.get() == 2 else "LOW"
        priority_color = config.ACCENT_COLOR if priority_text == "HIGH" else config.TEXT_COLOR

        # Create Task Card Frame inside 'To Do' Column
        card = tk.Frame(self.column_frames["To Do"], bg=config.CARD_BG, bd=1, relief=tk.RAISED)
        card.pack(fill=tk.X, padx=8, pady=5)

        # Card Title
        tk.Label(
            card, 
            text=title, 
            fg=config.TEXT_COLOR, 
            bg=config.CARD_BG, 
            font=("Arial", 10, "bold"),
            anchor="w"
        ).pack(fill=tk.X, padx=8, pady=(6, 2))

        # Card Priority Badge
        tk.Label(
            card, 
            text=f"Priority: {priority_text}", 
            fg=priority_color, 
            bg=config.CARD_BG, 
            font=("Arial", 8, "italic"),
            anchor="w"
        ).pack(fill=tk.X, padx=8, pady=(0, 6))

        # Clear Input Box
        self.entry_title.delete(0, tk.END)