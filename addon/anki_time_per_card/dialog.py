"""Anki WebView dialog for today's review-time stats."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .stats import ReviewStats, today_review_stats
from .webview_shell import render_webview_content

_BUNDLE_DIR = Path(__file__).parent / "web"
_BUNDLE_JS = _BUNDLE_DIR / "time_per_card.js"
_BUNDLE_CSS = _BUNDLE_DIR / "time_per_card.css"
_ACTIVE_DIALOG: Any | None = None


class TimePerCardDialog:
    """Factory wrapper replaced with a real QDialog subclass at runtime."""


def _create_dialog_class():
    from aqt.qt import QDialog, QVBoxLayout
    from aqt.webview import AnkiWebView

    class _TimePerCardDialog(QDialog):
        def __init__(self, parent: Any, stats: ReviewStats | None = None) -> None:
            super().__init__(parent)
            self.setWindowTitle("Average Time Per Card Today")
            self.setMinimumWidth(720)
            self.setMinimumHeight(440)

            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)

            self._webview = AnkiWebView(parent=self)
            self._webview.requiresCol = False
            body, head = _render_dialog_content(stats or today_review_stats(parent.col))
            self._webview.stdHtml(body=body, head=head, context=self)
            layout.addWidget(self._webview)

        def run_js(self, script: str, callback: Any = None) -> None:
            if callback is None:
                self._webview.eval(script)
                return
            self._webview.page().runJavaScript(script, callback)

    return _TimePerCardDialog


def _render_dialog_content(stats: ReviewStats) -> tuple[str, str]:
    return render_webview_content(
        initial_state_name="__INITIAL_STATE__",
        initial_state=stats.to_webview_state(),
        bundle_js=_BUNDLE_JS,
        bundle_css=_BUNDLE_CSS,
        scope="time-per-card",
    )


def show_stats_dialog(parent: Any | None = None) -> Any | None:
    """Open the stats dialog and keep it alive for Anki's Qt lifetime rules."""

    from aqt import mw
    from aqt.utils import showWarning

    resolved_parent = parent or mw
    if resolved_parent is None or getattr(resolved_parent, "col", None) is None:
        showWarning("Open an Anki profile before viewing today's card time.")
        return None

    dialog_class = _create_dialog_class()
    dialog = dialog_class(resolved_parent)
    dialog.show()
    dialog.raise_()
    dialog.activateWindow()

    global _ACTIVE_DIALOG
    _ACTIVE_DIALOG = dialog
    return dialog
