"""Service handling cross-platform desktop notifications via plyer."""

import logging

LOGGER: logging.Logger = logging.getLogger(__name__)

try:
    from plyer import notification

    _PLYER_AVAILABLE = True
except ImportError:
    _PLYER_AVAILABLE = False


def send_notification(title: str, message: str) -> None:
    """Trigger a native desktop notification if plyer is available."""
    if _PLYER_AVAILABLE:
        try:
            notification.notify(
                title=title, message=message, app_name="Task Manager Suite", timeout=6
            )
        except Exception as err:  # pylint: disable=broad-exception-caught
            LOGGER.error("Failed to send desktop notification: %s", err)
    else:
        LOGGER.warning("plyer package not installed. Skipping desktop notification.")
