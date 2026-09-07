"""
gui/main_window.py
Main application window constructing the menu hierarchy and layout frames.
"""

import tkinter as tk

import config
from gui.analytics import AnalyticsWindow
from gui.kanban_board import KanbanBoard


class MainWindow(tk.Tk):
    """Primary application frame hosting navigation and component views."""

    def __init__(self, root=None):
        """Initializes main Tk window settings and UI structure."""
        if root is not None:
            self.root = root
        else:
            super().__init__()
            self.root = self

        self.root.title("Kanban Task Manager & Productivity Suite")
        self.root.geometry("900x650")
        self.root.configure(bg=config.BG_COLOR)

        self.kanban_board = KanbanBoard(self.root)
        self.kanban_board.pack(fill=tk.BOTH, expand=True)

        self._setup_menu()

    def _setup_menu(self):
        """Builds top window menu bar with File, View, and Help options."""
        menubar = tk.Menu(self.root)

        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(
            label="New Task",
            command=self.kanban_board.entry_title.focus_set
        )
        file_menu.add_command(
            label="Export to CSV",
            command=self.kanban_board.export_csv_async
        )
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # View Menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(
            label="Open Analytics & Logs",
            command=self.open_analytics
        )
        menubar.add_cascade(label="View", menu=view_menu)

        self.root.config(menu=menubar)

    def open_analytics(self):
        """Instantiates and displays the Analytics and Log Viewer window."""
        AnalyticsWindow(self.root, self.kanban_board)
