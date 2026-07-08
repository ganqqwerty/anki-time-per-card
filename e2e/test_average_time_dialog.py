from __future__ import annotations

from e2e.conftest import import_runtime_addon_module
from e2e.helpers import wait_for_js, wait_for_selector


def test_average_time_dialog_renders_today_average(anki_mw) -> None:
    stats_module = import_runtime_addon_module(".stats")
    dialog_module = import_runtime_addon_module(".dialog")
    bounds = stats_module.local_day_bounds()
    base_id = bounds.start_ms + 10_000
    rows = [
        (base_id + 1, 101, -1, 3, 1, 0, 2500, 3000, 0),
        (base_id + 2, 101, -1, 3, 1, 0, 2500, 9000, 0),
        (base_id + 3, 202, -1, 3, 1, 0, 2500, 3000, 0),
    ]

    anki_mw.col.db.execute("delete from revlog where id >= ? and id < ?", bounds.start_ms, bounds.end_ms)
    anki_mw.col.db.executemany("insert into revlog values (?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)

    dialog = dialog_module.show_stats_dialog(anki_mw)
    assert dialog is not None
    try:
        wait_for_selector(dialog, '[data-testid="average-per-card"]', timeout=10.0)
        average = wait_for_js(
            dialog,
            'document.querySelector("[data-testid=\\"average-per-card\\"]").textContent.trim()',
            timeout=5.0,
        )
        cards = wait_for_js(
            dialog,
            'document.querySelector("[data-testid=\\"distinct-card-count\\"]").textContent.trim()',
            timeout=5.0,
        )
        reviews = wait_for_js(
            dialog,
            'document.querySelector("[data-testid=\\"review-count\\"]").textContent.trim()',
            timeout=5.0,
        )

        assert average == "7.5s"
        assert cards == "2"
        assert reviews == "3"
    finally:
        dialog.close()
