import tkinter as tk
from gui.main_window import MainWindow


def main():
    # Initialize main Tkinter application instance
    root = tk.Tk()
    
    # Pass root window to MainWindow layout controller
    app = MainWindow(root)
    
    # Start event loop
    root.mainloop()


if __name__ == "__main__":
    main()