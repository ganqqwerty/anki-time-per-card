"""Tools menu integration."""

from __future__ import annotations

from typing import Any

_ACTION_OBJECT_NAME = "anki_time_per_card_average_today"
_HOOK_REGISTERED = False


def register_hooks() -> None:
    """Register Anki hooks once."""

    global _HOOK_REGISTERED
    if _HOOK_REGISTERED:
        return

    from aqt import gui_hooks

    gui_hooks.profile_did_open.append(_install_tools_menu_action)
    _HOOK_REGISTERED = True


def _install_tools_menu_action(*_args: Any) -> None:
    from aqt import mw
    from aqt.qt import QAction

    if mw is None or getattr(mw, "form", None) is None:
        return
    menu = mw.form.menuTools
    for action in menu.actions():
        if action.objectName() == _ACTION_OBJECT_NAME:
            return

    action = QAction("Average Time Per Card Today", mw)
    action.setObjectName(_ACTION_OBJECT_NAME)
    action.triggered.connect(lambda _checked=False: _show_dialog())
    menu.addAction(action)


def _show_dialog() -> None:
    from .dialog import show_stats_dialog

    show_stats_dialog()
