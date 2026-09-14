"""Headless tests for Kanban board filtering, movement, and persistence."""

import datetime
import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from gui.kanban_board import KanbanBoard
from models.task import Task
from services.task_manager import TaskManager


class FakeVariable:
    """Minimal StringVar replacement for headless board interaction tests."""

    def __init__(self, value: str) -> None:
        self.value = value

    def get(self) -> str:
        """Return the current fake variable value."""
        return self.value

    def set(self, value: str) -> None:
        """Set the fake variable value."""
        self.value = value


class FakeButton:
    """Minimal button replacement for filter style tests."""

    def __init__(self) -> None:
        self.configured: dict[str, str] = {}

    def config(self, **kwargs: str) -> None:
        """Record widget configuration values."""
        self.configured.update(kwargs)


class FakeCard:
    """Minimal card replacement exposing the board filtering contract."""

    def __init__(self, task: Task) -> None:
        self.task = task
        self.visible = False
        self.destroyed = False

    def winfo_exists(self) -> bool:
        """Report that the fake card still exists."""
        return True

    def winfo_ismapped(self) -> bool:
        """Report whether the fake card is visible."""
        return self.visible

    def pack(self, **_kwargs: object) -> None:
        """Mark the fake card as visible."""
        self.visible = True

    def pack_forget(self) -> None:
        """Mark the fake card as hidden."""
        self.visible = False

    def destroy(self) -> None:
        """Destroy the fake card without requiring Tk."""
        self.visible = False
        self.destroyed = True


class TestKanbanBoardInteractions(unittest.TestCase):
    """Headless tests for search/filter and card movement interactions."""

    def test_search_matches_task_tags(self) -> None:
        """Typing a tag filters cards in real time."""
        board = KanbanBoard.__new__(KanbanBoard)
        board.search_var = FakeVariable("urgent")
        board.filter_mode = FakeVariable("All")
        card = FakeCard(Task("Prepare release", tags=["urgent"]))
        board.all_cards = [card]

        board.filter_tasks()

        self.assertTrue(card.visible)

    def test_move_card_to_column_updates_task_and_rebuilds(self) -> None:
        """Dropping a card in another column persists its new status."""
        board = KanbanBoard.__new__(KanbanBoard)
        board.columns = ["To Do", "In Progress", "Done"]
        board.save_board_state = Mock(return_value=True)
        board.rebuild_board_cards = Mock()
        card = FakeCard(Task("Ship feature", status="To Do"))

        board.move_card_to_column(card, "In Progress")

        self.assertEqual(card.task.status, "In Progress")
        board.save_board_state.assert_called_once_with()
        board.rebuild_board_cards.assert_called_once_with()

    def test_move_card_to_column_persists_with_task_manager(self) -> None:
        """Verifies a board move is persisted and available after reload."""
        with tempfile.TemporaryDirectory() as directory:
            db_path = os.path.join(directory, "tasks.db")
            manager = TaskManager(db_path=db_path)
            task = manager.add_task("Ship feature")
            board = KanbanBoard.__new__(KanbanBoard)
            board.columns = ["To Do", "In Progress", "Done"]
            board.task_manager = manager
            board.save_board_state = manager.save_to_file
            board.rebuild_board_cards = Mock()
            card = FakeCard(task)

            board.move_card_to_column(card, "In Progress")

            reloaded = TaskManager(db_path=db_path).load_from_file()

        self.assertEqual(reloaded[0].status, "In Progress")
        board.rebuild_board_cards.assert_called_once_with()

    def test_date_validation_accepts_only_real_iso_dates(self) -> None:
        """Rejects malformed and impossible due dates."""
        board = KanbanBoard.__new__(KanbanBoard)

        self.assertTrue(board.is_valid_date_format("2026-09-14"))
        self.assertFalse(board.is_valid_date_format("2026-9-14"))
        self.assertFalse(board.is_valid_date_format("2026-02-30"))

    def test_filter_mode_and_search_filter_cards(self) -> None:
        """Filters cards by priority, date, and search text."""
        board = KanbanBoard.__new__(KanbanBoard)
        board.search_var = FakeVariable("")
        board.filter_mode = FakeVariable("All")
        board.filter_buttons = {}
        high = FakeCard(Task("Ship release", priority="HIGH", due_date="2026-09-14"))
        low = FakeCard(Task("Write docs", priority="LOW", due_date="2026-09-15"))
        board.all_cards = [high, low]
        today = datetime.date(2026, 9, 14)

        with patch("gui.kanban_board.datetime.date") as date_mock:
            date_mock.today.return_value = today
            board.set_filter_mode("Today")
        self.assertTrue(high.visible)
        self.assertFalse(low.visible)

        board.search_var.set("docs")
        board.set_filter_mode("All")
        self.assertFalse(high.visible)
        self.assertTrue(low.visible)

    def test_filter_button_styles_mark_active_mode(self) -> None:
        """Highlights the active filter mode and resets other buttons."""
        board = KanbanBoard.__new__(KanbanBoard)
        board.filter_mode = FakeVariable("High")
        board.filter_buttons = {"All": FakeButton(), "High": FakeButton()}

        board.update_filter_button_styles()

        self.assertEqual(board.filter_buttons["High"].configured["fg"], "#11111B")
        self.assertEqual(
            board.filter_buttons["All"].configured["fg"],
            "#CDD6F4",
        )

    def test_move_card_horizontally_completes_task(self) -> None:
        """Moving a card to Done marks it complete and rebuilds its widget."""
        board = KanbanBoard.__new__(KanbanBoard)
        board.columns = ["To Do", "In Progress", "Done"]
        board.save_board_state = Mock(return_value=True)
        board.create_card_widget = Mock()
        card = FakeCard(Task("Finish feature", status="In Progress"))
        board.all_cards = [card]

        with patch("gui.kanban_board.EventLogger.log_event") as log_event:
            board.move_card_horizontal(card, 1)

        self.assertEqual(card.task.status, "Done")
        self.assertTrue(card.task.subtasks == [])
        self.assertTrue(card.destroyed)
        board.create_card_widget.assert_called_once()
        log_event.assert_called_once()


if __name__ == "__main__":
    unittest.main()
