# Kanban Task Manager & Productivity Suite

A desktop productivity application built with Python and Tkinter, featuring a drag-and-drop style Kanban board, built-in Pomodoro focus timer, CSV export capabilities, local JSON persistence, and integrated activity analytics.

---

## Features

- **Interactive Kanban Board**: Categorize tasks across custom status columns (`To Do`, `In Progress`, `Done`).
- **Focus Timer**: Dedicated Pomodoro session manager integrated directly into board state.
- **Analytics Dashboard**: Real-time visualization of task completion rates and focus session history.
- **Data Export & Persistence**: Auto-saves locally to JSON and supports exporting task lists to CSV.
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
# The project includes unit test suites for models, services, and GUI components using Python's standard unittest framework.
# Run all tests from the root directory with verbose output:
python -m unittest discover -s tests -p "test_*.py" -v

### Keyboard Shortcuts & Navigation
## Keyboard Shortcuts & Navigation

| Action | Shortcut / Interaction |
| :--- | :--- |
| **New Task Title Focus** | `Tab` navigation through control entries |
| **Move Card Up/Down** | `▲` / `▼` buttons on KanbanCard |
| **Move Card Column** | `◄` / `►` buttons on KanbanCard |
| **Trigger Default Action** | `Enter` inside active dialog fields |
| **Close Modal Window** | `Esc` or `Cancel` button |

