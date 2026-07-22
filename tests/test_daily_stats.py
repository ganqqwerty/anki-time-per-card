from __future__ import annotations

import unittest
from dataclasses import dataclass
from typing import Any

from addon.anki_time_per_card.daily_stats import (
    DAY_MILLISECONDS,
    DailyAverage,
    HistorySnapshot,
    all_time_average_history,
    daily_average_history,
)


class _FakeDatabase:
    def __init__(self, rows: list[tuple[int, int, int]]) -> None:
        self.rows = rows
        self.query = ""
        self.args: tuple[Any, ...] = ()

    def all(self, query: str, *args: Any) -> list[tuple[int, int, int]]:
        self.query = query
        self.args = args
        return self.rows


class _FakeDecks:
    def __init__(self, deck_ids: list[int]) -> None:
        self.deck_ids = deck_ids

    def active(self) -> list[int]:
        return self.deck_ids


@dataclass
class _FakeScheduler:
    day_cutoff: int


class _FakeCollection:
    def __init__(self, rows: list[tuple[int, int, int]], deck_ids: list[int]) -> None:
        self.sched = _FakeScheduler(day_cutoff=1_725_120_000)
        self.decks = _FakeDecks(deck_ids)
        self.db = _FakeDatabase(rows)


class DailyAverageHistoryTest(unittest.TestCase):
    def test_fills_empty_days_and_aggregates_review_time(self) -> None:
        collection = _FakeCollection(rows=[(0, 2, 4_000), (2, 4, 10_000)], deck_ids=[1, 2])

        snapshot = daily_average_history(collection, days=3)

        self.assertEqual([day.cards for day in snapshot.days], [2, 0, 4])
        self.assertEqual([day.seconds_per_card for day in snapshot.days], [2.0, 0.0, 2.5])
        self.assertEqual(len({day.day for day in snapshot.days}), 3)
        self.assertIn("type != ?", collection.db.query)
        self.assertIn("did in (1,2)", collection.db.query)
        self.assertEqual(collection.db.args[1], DAY_MILLISECONDS)
        self.assertEqual(collection.db.args[3], collection.db.args[0])

    def test_does_not_query_when_no_deck_is_active(self) -> None:
        collection = _FakeCollection(rows=[], deck_ids=[])

        snapshot = daily_average_history(collection, days=2)

        self.assertEqual([day.cards for day in snapshot.days], [0, 0])
        self.assertEqual(collection.db.query, "")

    def test_rejects_non_positive_history_length(self) -> None:
        collection = _FakeCollection(rows=[], deck_ids=[1])

        with self.assertRaisesRegex(ValueError, "positive"):
            daily_average_history(collection, days=0)

    def test_all_time_history_maps_days_ago_into_chronological_days(self) -> None:
        collection = _FakeCollection(rows=[(0, 4, 10_000), (2, 2, 4_000)], deck_ids=[1])

        snapshot = all_time_average_history(collection, minimum_days=5)

        self.assertEqual([day.cards for day in snapshot.days], [0, 0, 2, 0, 4])
        self.assertEqual([day.seconds_per_card for day in snapshot.days], [0.0, 0.0, 2.0, 0.0, 2.5])
        self.assertIn("? - 1 - id", collection.db.query)
        self.assertEqual(collection.db.args[1], DAY_MILLISECONDS)


class HistorySnapshotTest(unittest.TestCase):
    def test_compares_weighted_seven_day_windows(self) -> None:
        previous = [DailyAverage(f"2026-07-{day:02d}", 10, 20_000) for day in range(1, 8)]
        recent = [DailyAverage(f"2026-07-{day:02d}", 10, 10_000) for day in range(8, 15)]
        snapshot = HistorySnapshot(tuple(previous + recent))

        self.assertEqual(snapshot.previous_seconds_per_card, 2.0)
        self.assertEqual(snapshot.recent_seconds_per_card, 1.0)
        self.assertEqual(snapshot.trend_percent, 50.0)
        self.assertEqual(snapshot.total_cards, 140)
        self.assertEqual(snapshot.reviewed_days, 14)
        self.assertEqual(snapshot.average_seconds_per_card, 1.5)


if __name__ == "__main__":
    unittest.main()
