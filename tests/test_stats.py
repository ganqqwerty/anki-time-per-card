from __future__ import annotations

from datetime import UTC, datetime

from addon.anki_time_per_card.stats import (
    DayBounds,
    local_day_bounds,
    review_stats_from_rows,
    today_review_stats,
)


class FakeDb:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def all(self, sql: str, *args):
        self.calls.append((sql, args))
        return self.rows


class FakeCollection:
    def __init__(self, rows):
        self.db = FakeDb(rows)


def test_local_day_bounds_are_midnight_to_midnight() -> None:
    bounds = local_day_bounds(datetime(2026, 7, 8, 14, 30, tzinfo=UTC))

    assert bounds.start.hour == 0
    assert bounds.start.minute == 0
    assert bounds.end - bounds.start
    assert bounds.end.date().toordinal() == bounds.start.date().toordinal() + 1


def test_review_stats_from_rows_averages_by_distinct_card() -> None:
    bounds = DayBounds(
        start=datetime(2026, 7, 8, tzinfo=UTC),
        end=datetime(2026, 7, 9, tzinfo=UTC),
    )

    stats = review_stats_from_rows([(101, 3000), (101, 9000), (202, 3000)], bounds)

    assert stats.review_count == 3
    assert stats.distinct_card_count == 2
    assert stats.total_answer_time_ms == 15000
    assert stats.average_per_card_ms == 7500
    assert stats.average_per_answer_ms == 5000
    assert stats.to_webview_state()["averagePerCardMs"] == 7500


def test_review_stats_clamps_negative_answer_times() -> None:
    bounds = DayBounds(
        start=datetime(2026, 7, 8, tzinfo=UTC),
        end=datetime(2026, 7, 9, tzinfo=UTC),
    )

    stats = review_stats_from_rows([{"cid": 1, "time": -20}, {"cid": 2, "time": 1000}], bounds)

    assert stats.total_answer_time_ms == 1000
    assert stats.average_per_card_ms == 500


def test_today_review_stats_queries_revlog_with_day_bounds() -> None:
    collection = FakeCollection([(1, 1000), (2, 3000)])
    now = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)

    stats = today_review_stats(collection, now)

    assert stats.review_count == 2
    assert collection.db.calls
    sql, args = collection.db.calls[0]
    assert "from revlog" in sql
    assert args == (stats.day_start_ms, stats.day_end_ms)


def test_empty_rows_return_zero_averages() -> None:
    bounds = DayBounds(
        start=datetime(2026, 7, 8, tzinfo=UTC),
        end=datetime(2026, 7, 9, tzinfo=UTC),
    )

    stats = review_stats_from_rows([], bounds)

    assert stats.review_count == 0
    assert stats.distinct_card_count == 0
    assert stats.average_per_card_ms == 0
    assert stats.average_per_answer_ms == 0
