"""Live reviewer overlay for Anki's studied-today seconds-per-card value."""

from __future__ import annotations

import json
from contextlib import suppress
from dataclasses import dataclass
from typing import Any

from anki.consts import REVLOG_RESCHED
from anki.utils import ids2str

_OVERLAY_ID = "anki-time-per-card-overlay"
_REGISTERED = False


@dataclass(frozen=True)
class AverageSnapshot:
    cards: int
    milliseconds: int

    @property
    def seconds_per_card(self) -> int:
        if self.cards <= 0:
            return 0
        return round((self.milliseconds / 1000) / self.cards)

    @property
    def display_text(self) -> str:
        return f"{self.seconds_per_card}s/card"

    def to_payload(self) -> dict[str, int | str]:
        return {
            "cards": self.cards,
            "milliseconds": self.milliseconds,
            "secondsPerCard": self.seconds_per_card,
            "displayText": self.display_text,
        }


def register_hooks() -> None:
    """Register reviewer hooks once."""

    global _REGISTERED
    if _REGISTERED:
        return

    from aqt import gui_hooks

    gui_hooks.webview_will_set_content.append(_inject_overlay)
    gui_hooks.reviewer_did_show_question.append(_on_card_visible)
    gui_hooks.reviewer_did_show_answer.append(_on_card_visible)
    gui_hooks.reviewer_did_answer_card.append(_on_card_answered)
    _REGISTERED = True


def studied_today_average(collection: Any) -> AverageSnapshot:
    """Return Anki's active-deck studied-today seconds-per-card inputs."""

    active_deck_ids = collection.decks.active()
    if not active_deck_ids:
        return AverageSnapshot(cards=0, milliseconds=0)

    start_ms = (collection.sched.day_cutoff - 86400) * 1000
    row = collection.db.first(
        f"""
        select count(), coalesce(sum(time), 0)
        from revlog
        where type != ?
          and id > ?
          and cid in (select id from cards where did in {ids2str(active_deck_ids)})
        """,
        REVLOG_RESCHED,
        start_ms,
    )
    cards = int(row[0] or 0)
    milliseconds = int(row[1] or 0)
    return AverageSnapshot(cards=cards, milliseconds=milliseconds)


def _inject_overlay(web_content: Any, context: Any) -> None:
    if not _is_reviewer_context(context):
        return
    web_content.head += _overlay_style()
    web_content.body += _overlay_html()


def _on_card_visible(_card: Any) -> None:
    _update_reviewer_overlay()


def _on_card_answered(reviewer: Any, _card: Any, _ease: int) -> None:
    _update_reviewer_overlay(reviewer)


def _update_reviewer_overlay(reviewer: Any | None = None) -> None:
    resolved_reviewer = reviewer or _current_reviewer()
    if resolved_reviewer is None:
        return
    collection = getattr(getattr(resolved_reviewer, "mw", None), "col", None)
    web = getattr(resolved_reviewer, "web", None)
    if collection is None or web is None:
        return

    payload = json.dumps(studied_today_average(collection).to_payload())
    script = f"window.__ankiTimePerCardSetAverage && window.__ankiTimePerCardSetAverage({payload});"
    with suppress(Exception):
        web.eval(script)


def _current_reviewer() -> Any | None:
    with suppress(Exception):
        from aqt import mw

        return getattr(mw, "reviewer", None)
    return None


def _is_reviewer_context(context: Any) -> bool:
    with suppress(Exception):
        from aqt.reviewer import Reviewer

        return isinstance(context, Reviewer)
    return False


def _overlay_style() -> str:
    return """
<style>
#anki-time-per-card-overlay {
  position: fixed;
  top: 10px;
  right: 12px;
  z-index: 2147483647;
  padding: 4px 8px;
  border: 1px solid var(--border-subtle, rgba(128, 128, 128, 0.35));
  border-radius: 5px;
  background: var(--canvas-glass, rgba(255, 255, 255, 0.78));
  color: var(--fg, #222);
  font: 600 13px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  line-height: 1.2;
  pointer-events: none;
}
</style>
"""


def _overlay_html() -> str:
    return f"""
<div id="{_OVERLAY_ID}" aria-label="Average answer time today">0s/card</div>
<script>
(function() {{
  const overlay = document.getElementById("{_OVERLAY_ID}");
  window.__ankiTimePerCardSetAverage = function(payload) {{
    if (!overlay || !payload) return;
    overlay.textContent = payload.displayText || "0s/card";
    overlay.dataset.cards = String(payload.cards || 0);
    overlay.dataset.milliseconds = String(payload.milliseconds || 0);
    overlay.dataset.secondsPerCard = String(payload.secondsPerCard || 0);
  }};
}})();
</script>
"""
