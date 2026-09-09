"""
tests/test_kanban_board.py
Unit test suite verifying KanbanBoard integration and UI actions.
"""

import tkinter as tk
import unittest
from unittest.mock import MagicMock, patch

from gui.kanban_board import KanbanBoard


class TestKanbanBoard(unittest.TestCase):
    """Tests board data loading, card creation, and clear functionality."""

    @classmethod
    def setUpClass(cls) -> None:
        """Sets up root Tk instance."""
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls) -> None:
        """Destroys root Tk instance."""
        cls.root.destroy()

    def setUp(self) -> None:
        """Standard setUp signature without extra arguments."""
        with patch(
            "services.task_manager.TaskManager.load_from_file",
            return_value=[]
        ):
            self.board = KanbanBoard(self.root)

    @patch("services.task_manager.TaskManager.save_to_file")
    def test_add_task_card(self, mock_save: MagicMock) -> None:
        """Verifies adding a task updates manager and UI card state."""
        mock_save.return_value = True
        self.board.entry_title.insert(0, "Test Task Title")
        self.board.entry_due.delete(0, tk.END)
        self.board.entry_due.insert(0, "2026-10-15")

        self.board.add_task_card()

        self.assertEqual(len(self.board.all_cards), 1)
        self.assertEqual(self.board.all_cards[0].task_title, "Test Task Title")

    @patch("services.task_manager.TaskManager.save_to_file")
    def test_clear_done_tasks(self, mock_save: MagicMock) -> None:
        """Verifies clearing completed tasks removes card widgets."""
        mock_save.return_value = True
        # pylint: disable=protected-access
        self.board._create_card_widget(
            "task-99", "Finished Task", "LOW", "Done", "2026-10-01", []
        )
        self.assertEqual(len(self.board.all_cards), 1)

        self.board.clear_done_tasks()
        self.assertEqual(len(self.board.all_cards), 0)

    @patch("services.task_manager.TaskManager.save_to_file")
    @patch("services.task_manager.TaskManager.load_from_file")
    def test_save_and_load_board_data(
        self, mock_load: MagicMock, mock_save: MagicMock
    ) -> None:
        """Verifies saving triggers storage file write."""
        mock_save.return_value = True
        mock_load.return_value = []

        # pylint: disable=protected-access
        success = self.board._safe_save()
        self.assertTrue(success)
        mock_save.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
