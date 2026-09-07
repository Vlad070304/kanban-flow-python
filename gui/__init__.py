"""
gui package initializer.
Exposes core GUI components for clean imports across the application.
"""

from gui.analytics import AnalyticsWindow
from gui.kanban_board import KanbanBoard
from gui.main_window import MainWindow

__all__ = ["AnalyticsWindow", "KanbanBoard", "MainWindow"]
