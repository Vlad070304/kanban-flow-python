"""
tests/test_kanban_board.py
Unit tests for the KanbanBoard GUI controller.
"""

import os
import unittest
import tkinter as tk

from gui.kanban_board import KanbanBoard


class TestKanbanBoard(unittest.TestCase):
    """Tests for KanbanBoard UI instantiation and board updates."""

    TEST_FILE = "test_board_data.json"

    def setUp(self) -> None:
        """Sets up Tk container and KanbanBoard instance before each test."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.board = KanbanBoard(self.root)

    def tearDown(self) -> None:
        """Destroys Tk container and removes temporary test file."""
        self.root.destroy()
        if os.path.exists(self.TEST_FILE):
            os.remove(self.TEST_FILE)

    def test_add_task_card(self) -> None:
        """Verifies adding a task updates manager and UI card state."""
        self.board.task_manager.add_task("Test GUI Task", "HIGH", "To Do")
        self.board.load_board_data()
        self.assertEqual(len(self.board.task_manager.tasks), 1)

    def test_save_and_load_board_data(self) -> None:
        """Verifies manager save produces target storage file."""
        self.board.task_manager.add_task("Persistent Task", "LOW", "To Do")
        self.board.task_manager.save_to_file()
        self.assertTrue(os.path.exists(self.board.task_manager.filepath))

    def test_clear_done_tasks(self) -> None:
        """Verifies clearing completed tasks removes them from state."""
        self.board.task_manager.add_task("Finished Task", "LOW", "Done")
        self.board.task_manager.clear_done()
        self.assertEqual(len(self.board.task_manager.tasks), 0)


if __name__ == "__main__":
    unittest.main()
