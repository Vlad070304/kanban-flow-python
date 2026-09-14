# Kanban Task Manager & Productivity Suite

A desktop productivity application built with Python and Tkinter, featuring a drag-and-drop style Kanban board, built-in Pomodoro focus timer, CSV export capabilities, local JSON persistence, and integrated activity analytics.

---

## Features

- **Interactive Kanban Board**: Categorize tasks across custom status columns (`To Do`, `In Progress`, `Done`).
- **Focus Timer**: Dedicated Pomodoro session manager integrated directly into board state.
- **Analytics Dashboard**: Real-time visualization of task completion rates and focus session history.
- **Data Export & Persistence**: Auto-saves tasks to SQLite, stores activity logs locally, and supports JSON backups, CSV export, and task import.
- **Recurring Tasks**: Schedule daily, weekly, or monthly task occurrences; completing one advances it to the next due date.
- **Richer Analytics**: Tracks focus minutes and completed tasks by task ID, plus completion counts by priority.
- **Overdue Task Tracking**: Highlights past-due cards based on configured system dates.

---

## Architecture Breakdown

The project follows a clean, modular architecture separating UI components, core domain models, business logic services, and persistence layers:

---

## Installation & Setup

### Prerequisites

- Python 3.10 or higher installed.

### Setup Instructions

1. **Clone the repository:**
git clone https://github.com/Vlad070304/kanban-flow-python.git
cd task-manager-suite

1.1. Create and activate a virtual environment (optional but recommended):
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

2. Install dependencies:
pip install pyinstaller

3. Run the application:
python main.py

### Testing
The project includes unit test suites for models, services, and GUI components using Python's standard `unittest` framework.

Run all tests from the repository root:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

Run the headless release smoke test:

```powershell
python release_smoke_test.py
```

The smoke test uses temporary data and verifies SQLite initialization and
migrations, recurring-task persistence, JSON backup restore, CSV import, and
task-linked focus analytics. It does not open Tkinter windows, so it can run
on CI runners without a graphical display.

Before creating a release, run:

```powershell
python -m ruff check .
python -m ruff format --check .
python -m mypy
python -m unittest discover -s tests -p "test_*.py" -v
python release_smoke_test.py
python build.py
```

The final command requires PyInstaller and creates the standalone bundle in
the `dist/` directory.

### Data location

Application data is stored in the platform's user data directory:

- Windows: `%APPDATA%\KanbanTaskManager`
- macOS: `~/Library/Application Support/KanbanTaskManager`
- Linux: `$XDG_DATA_HOME/KanbanTaskManager` or `~/.local/share/KanbanTaskManager`

This directory contains the SQLite database, event log, and application error log.
Explicit database paths passed to `TaskManager` remain supported for tests and custom deployments.

### Keyboard Shortcuts & Navigation
## Keyboard Shortcuts & Navigation

| Action | Shortcut / Interaction |
| :--- | :--- |
| **New Task Title Focus** | `Tab` navigation through control entries |
| **Move Card Up/Down** | `▲` / `▼` buttons on KanbanCard |
| **Move Card Column** | `◄` / `►` buttons on KanbanCard |
| **Trigger Default Action** | `Enter` inside active dialog fields |
| **Close Modal Window** | `Esc` or `Cancel` button |
