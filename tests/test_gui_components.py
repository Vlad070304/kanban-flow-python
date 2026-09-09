"""
tests/test_gui_components.py
Unit test suite for GUI components including KanbanCard and FocusTimerDialog.
"""

import tkinter as tk
import unittest
from unittest.mock import MagicMock, patch

import config
from gui.dialogs import FocusTimerDialog
from gui.widgets import KanbanCard


class TestKanbanCardWidget(unittest.TestCase):
    """Test suite evaluating KanbanCard instantiation, status updates, and overdue logic."""

    @classmethod
    def setUpClass(cls) -> None:
        """Sets up a hidden Tkinter root window for widget rendering tests."""
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls) -> None:
        """Destroys the Tkinter root window after tests complete."""
        cls.root.destroy()

    def setUp(self) -> None:
        """Prepares a mock board instance before each test method runs."""
        self.mock_board = MagicMock()

    def test_card_initialization_standard_task(self) -> None:
        """Verifies card creation with regular future due date."""
        card = KanbanCard(
            parent=self.root,
            board=self.mock_board,
            task_id="task-101",
            title="Implement Unit Tests",
            priority="HIGH",
            column_name="To Do",
            due_date="2099-12-31",
            tags=["Testing", "Python"]
        )

        self.assertEqual(card.task_id, "task-101")
        self.assertEqual(card.task_title, "Implement Unit Tests")
        self.assertEqual(card.task_priority, "HIGH")
        self.assertFalse(card.is_overdue)
        self.assertEqual(card.cget("highlightbackground"), config.FRAME_BG)
        card.destroy()

    def test_card_overdue_detection_and_styling(self) -> None:
        """Verifies past due date triggers overdue flag and red border."""
        past_date = "2020-01-01"
        card = KanbanCard(
            parent=self.root,
            board=self.mock_board,
            task_id="task-102",
            title="Overdue Feature",
            priority="LOW",
            column_name="In Progress",
            due_date=past_date,
            tags=["Bug"]
        )

        self.assertTrue(card.is_overdue)
        self.assertEqual(card.cget("highlightbackground"), "#F38BA8")
        self.assertEqual(card.cget("highlightthickness"), 2)
        card.destroy()

    def test_completed_overdue_task_not_flagged(self) -> None:
        """Verifies past due tasks in Done column are not marked overdue."""
        past_date = "2020-01-01"
        card = KanbanCard(
            parent=self.root,
            board=self.mock_board,
            task_id="task-103",
            title="Completed Past Task",
            priority="HIGH",
            column_name="Done",
            due_date=past_date,
            tags=["Done"]
        )

        self.assertFalse(card.is_overdue)
        self.assertNotEqual(card.cget("highlightbackground"), "#F38BA8")
        card.destroy()

    def test_card_vertical_move_callback(self) -> None:
        """Verifies vertical reorder buttons invoke correct board delegate methods."""
        card = KanbanCard(
            parent=self.root,
            board=self.mock_board,
            task_id="task-104",
            title="Reorder Test",
            priority="LOW",
            column_name="To Do"
        )

        self.mock_board.move_card_vertical.assert_not_called()
        self.mock_board.move_card_vertical(card, -1)
        self.mock_board.move_card_vertical.assert_called_with(card, -1)
        card.destroy()


class TestFocusTimerDialog(unittest.TestCase):
    """Test suite verifying FocusTimerDialog setup and configuration delegation."""

    @classmethod
    def setUpClass(cls) -> None:
        """Sets up a hidden Tkinter root window for dialog tests."""
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls) -> None:
        """Destroys the Tkinter root window after tests complete."""
        cls.root.destroy()

    def setUp(self) -> None:
        """Prepares a mock board instance before each test method runs."""
        self.mock_board = MagicMock()

    def _find_widget_by_type(self, root_widget: tk.Widget, widget_type: type) -> tk.Widget:
        """Recursively finds child widgets matching a given class type."""
        for child in root_widget.winfo_children():
            if isinstance(child, widget_type):
                return child
            res = self._find_widget_by_type(child, widget_type)
            if res:
                return res
        return None

    def _find_button_by_text(self, root_widget: tk.Widget, text: str) -> tk.Button:
        """Recursively searches for a Button widget matching specified text."""
        for child in root_widget.winfo_children():
            if isinstance(child, tk.Button) and child.cget("text") == text:
                return child
            res = self._find_button_by_text(child, text)
            if res:
                return res
        return None

    @patch("tkinter.Toplevel.grab_set")
    def test_timer_start_delegation(self, _mock_grab: MagicMock) -> None:
        """Tests that initiating the timer delegates duration to board.start_focus_timer."""
        dialog = FocusTimerDialog(self.root, self.mock_board)

        spinbox = self._find_widget_by_type(dialog, tk.Spinbox)
        self.assertIsNotNone(spinbox)
        spinbox.delete(0, tk.END)
        spinbox.insert(0, "45")

        start_btn = self._find_button_by_text(dialog, "Start Session")
        self.assertIsNotNone(start_btn)
        start_btn.invoke()

        self.mock_board.start_focus_timer.assert_called_once_with(45)

    @patch("tkinter.Toplevel.grab_set")
    def test_timer_cancel_delegation(self, _mock_grab: MagicMock) -> None:
        """Tests that clicking cancel delegates to board.cancel_focus_timer."""
        dialog = FocusTimerDialog(self.root, self.mock_board)

        cancel_btn = self._find_button_by_text(dialog, "Cancel")
        self.assertIsNotNone(cancel_btn)
        cancel_btn.invoke()

        self.mock_board.cancel_focus_timer.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
