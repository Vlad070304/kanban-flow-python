import unittest
from unittest.mock import Mock

from gui.kanban_board import KanbanBoard
from models.task import Task


class FakeVariable:
    """Minimal StringVar replacement for headless board interaction tests."""

    def __init__(self, value: str) -> None:
        self.value = value

    def get(self) -> str:
        return self.value


class FakeCard:
    """Minimal card replacement exposing the board filtering contract."""

    def __init__(self, task: Task) -> None:
        self.task = task
        self.visible = False

    def winfo_exists(self) -> bool:
        return True

    def winfo_ismapped(self) -> bool:
        return self.visible

    def pack(self, **_kwargs: object) -> None:
        self.visible = True

    def pack_forget(self) -> None:
        self.visible = False


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
        board._rebuild_board_cards = Mock()
        card = FakeCard(Task("Ship feature", status="To Do"))

        board.move_card_to_column(card, "In Progress")

        self.assertEqual(card.task.status, "In Progress")
        board.save_board_state.assert_called_once_with()
        board._rebuild_board_cards.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
