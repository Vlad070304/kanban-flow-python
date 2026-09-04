import tkinter as tk
from tkinter import messagebox
import config


class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        
        # Configure primary window settings
        self.root.title(config.WINDOW_TITLE)
        self.root.geometry(config.WINDOW_GEOMETRY)
        self.root.configure(bg=config.BG_COLOR)
        
        # Build UI Components
        self._build_menu()
        self._build_header()
        self._build_footer()

    def _build_menu(self):
        """Creates the top application navigation menu."""
        menubar = tk.Menu(self.root)

        # File Dropdown Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New Task", command=self._on_placeholder_click)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Help Dropdown Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about_dialog)
        menubar.add_cascade(label="Help", menu=help_menu)

        # Attach menu bar to root window
        self.root.config(menu=menubar)

    def _build_header(self):
        """Builds the top header banner frame."""
        # FIX: Changed py=12, px=10 to pady=12, padx=10
        header_frame = tk.Frame(self.root, bg=config.FRAME_BG, pady=12, padx=10)
        header_frame.pack(fill=tk.X, side=tk.TOP)

        title_lbl = tk.Label(
            header_frame,
            text="Kanban Board Suite",
            fg=config.TEXT_COLOR,
            bg=config.FRAME_BG,
            font=("Arial", 16, "bold")
        )
        title_lbl.pack(side=tk.LEFT)

        subtitle_lbl = tk.Label(
            header_frame,
            text="Organize & Track Tasks",
            fg=config.ACCENT_COLOR,
            bg=config.FRAME_BG,
            font=("Arial", 10, "italic")
        )
        subtitle_lbl.pack(side=tk.RIGHT, pady=3)

    def _build_footer(self):
        """Builds the bottom status bar frame."""
        footer_frame = tk.Frame(self.root, bg=config.FRAME_BG, pady=4, padx=10)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)

        status_lbl = tk.Label(
            footer_frame,
            text=f"Ready | Version {config.APP_VERSION}",
            fg=config.TEXT_COLOR,
            bg=config.FRAME_BG,
            font=("Arial", 9)
        )
        status_lbl.pack(side=tk.LEFT)

    def _show_about_dialog(self):
        messagebox.showinfo(
            "About Kanban Suite",
            f"{config.WINDOW_TITLE}\nVersion: {config.APP_VERSION}\n\nBuilt with Python & Tkinter."
        )

    def _on_placeholder_click(self):
        """Temporary handler for upcoming actions."""
        messagebox.showinfo("Notice", "Feature will be fully linked in upcoming board views.")