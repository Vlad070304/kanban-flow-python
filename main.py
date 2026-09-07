"""
main.py
Application entry point initializing the main window interface and menu components.
"""

import tkinter as tk
from gui.main_window import MainWindow


def main():
    """Instantiates and launches the main application loop."""
    root = tk.Tk()
    _app = MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
