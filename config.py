"""Application configuration and styling constants."""

APP_VERSION = "1.1.0"
WINDOW_TITLE = "Kanban Task Manager & Productivity Suite"
WINDOW_GEOMETRY = "950x650"

THEMES = {
    "dark": {
        "BG_COLOR": "#1E1E2E",
        "FRAME_BG": "#181825",
        "CARD_BG": "#313244",
        "TEXT_COLOR": "#CDD6F4",
        "ACCENT_COLOR": "#89B4FA",
        "INPUT_BG": "#313244",
        "BORDER_COLOR": "#45475A",
    },
    "light": {
        "BG_COLOR": "#EFF1F5",
        "FRAME_BG": "#E6E9EF",
        "CARD_BG": "#FFFFFF",
        "TEXT_COLOR": "#4C4F69",
        "ACCENT_COLOR": "#1E66F5",
        "INPUT_BG": "#FFFFFF",
        "BORDER_COLOR": "#BCC0CC",
    },
}

THEME_NAME = "dark"
BG_COLOR: str
FRAME_BG: str
CARD_BG: str
TEXT_COLOR: str
ACCENT_COLOR: str
INPUT_BG: str
BORDER_COLOR: str


def set_theme(name: str) -> None:
    """Update exported palette values for the selected UI theme."""
    if name not in THEMES:
        raise ValueError(f"Unknown theme: {name}")
    globals().update(THEMES[name])
    global THEME_NAME
    THEME_NAME = name


set_theme(THEME_NAME)

# Task Priority Colors
HIGH_PRIO_COLOR = "#F38BA8"
LOW_PRIO_COLOR = "#89B4FA"

# Interactive Hover States
BTN_HOVER_ADD = "#74C7EC"
BTN_HOVER_TIMER = "#F9E2AF"
BTN_HOVER_CLEAR = "#F5E0DC"
