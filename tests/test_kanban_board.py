import json
import os
import unittest
import tkinter as tk
from gui.kanban_board import KanbanBoard


class TestKanbanBoard(unittest.TestCase):
    #Test suite for validating board logic and file serialization.

    def setUp(self):
        # Create a hidden Tk root window and clean test environment.
        self.root = tk.Tk()
        self.root.withdraw()
        self.test_file = "test_kanban_data.json"

        # Instantiate board frame and override default file path
        self.board = KanbanBoard(self.root)
        self.board.DATA_FILE = self.test_file

    def tearDown(self):
        # Clean up created test JSON files and destroy Tk window.
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        self.root.destroy()

    def test_add_task_card(self):
        # Test adding a card populates the 'To Do' column correctly.
        self.board.entry_title.insert(0, "Test Unit Task")
        self.board.add_task_card()

        todo_frame = self.board.column_frames["To Do"]
        cards = todo_frame.winfo_children()

        self.assertEqual(len(cards), 1)
        self.assertEqual(self.board.total_cards, 1)

    def test_save_and_load_board_data(self):
        # Test serializing cards to JSON and restoring board state.
        self.board.entry_title.insert(0, "Persistent Task")
        self.board.add_task_card()
        self.board.save_board_data()

        self.assertTrue(os.path.exists(self.test_file))

        with open(self.test_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "Persistent Task")
        self.assertEqual(data[0]["status"], "To Do")

    def test_clear_done_tasks(self):
        # Test clearing completed tasks empties the 'Done' column.
        self.board._create_card_widget("Finished Task", "LOW", "Done")
        self.board.update_progress_bar()

        self.assertEqual(self.board.done_cards, 1)

        self.board.clear_done_tasks()

        done_cards = self.board.column_frames["Done"].winfo_children()
        self.assertEqual(len(done_cards), 0)
        self.assertEqual(self.board.done_cards, 0)


if __name__ == "__main__":
    unittest.main()