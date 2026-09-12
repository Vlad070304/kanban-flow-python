"""
gui/dialogs/focus_timer_dialog.py
Modal dialog component for setting up and controlling Pomodoro focus sessions.
"""

import tkinter as tk
from tkinter import messagebox
from typing import Any

import config


class FocusTimerDialog(tk.Toplevel):
    """Modal dialog providing Pomodoro presets and custom focus session controls."""

    def __init__(self, parent: tk.Widget, board_ref: Any) -> None:
        super().__init__(parent)
        self.board: Any = board_ref
        self.title("Focus Timer & Pomodoro")
        self.geometry("340x240")
        self.configure(bg=config.FRAME_BG)
        self.resizable(False, False)
        self.transient(parent)  # type: ignore[call-overload]
        self.grab_set()
        self._build_ui()

    def _build_ui(self) -> None:
        """Constructs the layout for focus timer dialog controls."""
        tk.Label(
            self,
            text="Pomodoro & Focus Timer",
            fg=config.TEXT_COLOR,
            bg=config.FRAME_BG,
            font=("Arial", 12, "bold"),
        ).pack(pady=(15, 5))
        tk.Label(
            self,
            text="Select a preset or enter custom minutes:",
            fg=config.TEXT_COLOR,
            bg=config.FRAME_BG,
            font=("Arial", 9),
        ).pack(pady=(0, 10))

        preset_frame: tk.Frame = tk.Frame(self, bg=config.FRAME_BG)
        preset_frame.pack(fill=tk.X, padx=20, pady=5)

        btn_25: tk.Button = tk.Button(
            preset_frame,
            text="25m Focus",
            bg=config.ACCENT_COLOR,
            fg="#11111B",
            font=("Arial", 9, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            command=lambda: self._start_session(25),
        )
        btn_25.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        btn_15: tk.Button = tk.Button(
            preset_frame,
            text="15m Break",
            bg="#89B4FA",
            fg="#11111B",
            font=("Arial", 9, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            command=lambda: self._start_session(15),
        )
        btn_15.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        btn_5: tk.Button = tk.Button(
            preset_frame,
            text="5m Rest",
            bg="#A6E3A1",
            fg="#11111B",
            font=("Arial", 9, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            command=lambda: self._start_session(5),
        )
        btn_5.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        custom_frame: tk.Frame = tk.Frame(self, bg=config.FRAME_BG)
        custom_frame.pack(fill=tk.X, padx=20, pady=12)

        tk.Label(
            custom_frame,
            text="Custom (mins):",
            fg=config.TEXT_COLOR,
            bg=config.FRAME_BG,
            font=("Arial", 9, "bold"),
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.custom_entry: tk.Entry = tk.Entry(
            custom_frame,
            width=8,
            bg="#313244",
            fg=config.TEXT_COLOR,
            insertbackground="white",
        )
        self.custom_entry.insert(0, "10")
        self.custom_entry.pack(side=tk.LEFT, padx=5)

        btn_custom: tk.Button = tk.Button(
            custom_frame,
            text="Start",
            bg="#FAB387",
            fg="#11111B",
            font=("Arial", 9, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            command=self._start_custom,
        )
        btn_custom.pack(side=tk.LEFT, padx=5)

        if getattr(self.board, "_timer_running", False):
            btn_stop: tk.Button = tk.Button(
                self,
                text="Stop Current Session",
                bg="#F38BA8",
                fg="#11111B",
                font=("Arial", 9, "bold"),
                relief=tk.FLAT,
                cursor="hand2",
                command=self._stop_session,
            )
            btn_stop.pack(pady=5)

    def _start_session(self, minutes: int) -> None:
        """Starts a focus session with specified minutes."""
        self.board.start_focus_timer(minutes)
        self.destroy()

    def _start_custom(self) -> None:
        """Validates and starts a custom minute focus session."""
        val: str = self.custom_entry.get().strip()
        if val.isdigit() and int(val) > 0:
            self._start_session(int(val))
        else:
            messagebox.showwarning(
                "Invalid Input", "Please enter a valid positive integer."
            )

    def _stop_session(self) -> None:
        """Stops the active focus session."""
        self.board.cancel_focus_timer()
        self.destroy()
