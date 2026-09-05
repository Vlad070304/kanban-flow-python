# Kanban Board and Productivity Suite

A desktop task management application built in Python using Tkinter. Features include visual completion metrics, focus timers, CSV exports, persistent JSON storage, and a dark interface.

---

## Features

* **Visual Progress Tracking:** Real-time percentage progress bar calculated directly from active board tasks.
* **Persistent Storage:** Automatically saves tasks to `kanban_data.json`.
* **Focus Timer:** Built-in focus countdown timer using background daemon threads.
* **CSV Export:** Asynchronously exports board tasks to CSV format.
* **Keyboard Shortcuts:**
  * `Ctrl + N`: Focus task title input field.
  * `Esc`: Clear input field contents.
* **Clear Completed:** One-click cleanup option to clear all tasks from the Done column.

---

## Installation and Setup

### Prerequisites

* Python 3.10 or higher installed on your system.

### Running the Application

1. Clone or download the repository:
   ```bash
   git clone [https://github.com/your-username/kanban-flow-python.git](https://github.com/your-username/kanban-flow-python.git)
   cd kanban-flow-python