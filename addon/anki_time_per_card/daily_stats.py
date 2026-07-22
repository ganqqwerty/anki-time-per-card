"""Daily review-time history derived from Anki's durable review log."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from anki.consts import REVLOG_RESCHED
from anki.utils import ids2str

DAY_SECONDS = 86_400
DAY_MILLISECONDS = DAY_SECONDS * 1_000
DEFAULT_HISTORY_DAYS = 30


@dataclass(frozen=True)
class DailyAverage:
    day: str
    cards: int
    milliseconds: int

    @property
    def seconds_per_card(self) -> float:
        if self.cards <= 0:
            return 0.0
        return round((self.milliseconds / 1_000) / self.cards, 2)

    def to_payload(self) -> dict[str, str | int | float]:
        return {
            "day": self.day,
            "cards": self.cards,
            "milliseconds": self.milliseconds,
            "secondsPerCard": self.seconds_per_card,
        }


@dataclass(frozen=True)
class HistorySnapshot:
    days: tuple[DailyAverage, ...]

    @property
    def today(self) -> DailyAverage:
        return self.days[-1]

    @property
    def total_cards(self) -> int:
        return sum(day.cards for day in self.days)

    @property
    def reviewed_days(self) -> int:
        return sum(day.cards > 0 for day in self.days)

    @property
    def average_seconds_per_card(self) -> float:
        return _weighted_average(self.days)

    @property
    def recent_seconds_per_card(self) -> float:
        return _weighted_average(self.days[-7:])

    @property
    def previous_seconds_per_card(self) -> float:
        return _weighted_average(self.days[-14:-7])

    @property
    def trend_percent(self) -> float | None:
        recent = HistorySnapshot(self.days[-7:])
        previous = HistorySnapshot(self.days[-14:-7])
        return recent.trend_against(previous)

    def trend_against(self, previous: HistorySnapshot) -> float | None:
        current_average = self.average_seconds_per_card
        previous_average = previous.average_seconds_per_card
        if current_average <= 0 or previous_average <= 0:
            return None
        return round(((previous_average - current_average) / previous_average) * 100, 1)

    def to_payload(self) -> dict[str, Any]:
        return {
            "days": [day.to_payload() for day in self.days],
            "summary": {
                "todaySecondsPerCard": self.today.seconds_per_card,
                "todayCards": self.today.cards,
                "recentSecondsPerCard": self.recent_seconds_per_card,
                "previousSecondsPerCard": self.previous_seconds_per_card,
                "trendPercent": self.trend_percent,
                "totalCards": self.total_cards,
            },
        }


def daily_average_history(collection: Any, days: int = DEFAULT_HISTORY_DAYS) -> HistorySnapshot:
    """Return per-scheduler-day average review time for the active deck."""

    if days <= 0:
        raise ValueError("days must be positive")

    day_cutoff_seconds = int(collection.sched.day_cutoff)
    today_start_seconds = day_cutoff_seconds - DAY_SECONDS
    history_start_seconds = today_start_seconds - ((days - 1) * DAY_SECONDS)
    history_start_ms = history_start_seconds * 1_000
    day_cutoff_ms = day_cutoff_seconds * 1_000

    totals_by_index: dict[int, tuple[int, int]] = {}
    active_deck_ids = collection.decks.active()
    if active_deck_ids:
        rows = collection.db.all(
            f"""
            select cast((id - ?) / ? as integer), count(), coalesce(sum(time), 0)
            from revlog
            where type != ?
              and id >= ?
              and id < ?
              and cid in (select id from cards where did in {ids2str(active_deck_ids)})
            group by 1
            order by 1
            """,
            history_start_ms,
            DAY_MILLISECONDS,
            REVLOG_RESCHED,
            history_start_ms,
            day_cutoff_ms,
        )
        for row in rows:
            day_index = int(row[0])
            if 0 <= day_index < days:
                totals_by_index[day_index] = (int(row[1] or 0), int(row[2] or 0))

    return _history_from_totals(history_start_seconds, days, totals_by_index)


def all_time_average_history(collection: Any, minimum_days: int = 1) -> HistorySnapshot:
    """Return all daily averages, with enough leading days for period comparisons."""

    if minimum_days <= 0:
        raise ValueError("minimum_days must be positive")

    day_cutoff_seconds = int(collection.sched.day_cutoff)
    day_cutoff_ms = day_cutoff_seconds * 1_000
    totals_by_days_ago: dict[int, tuple[int, int]] = {}
    active_deck_ids = collection.decks.active()
    if active_deck_ids:
        rows = collection.db.all(
            f"""
            select cast((? - 1 - id) / ? as integer), count(), coalesce(sum(time), 0)
            from revlog
            where type != ?
              and id < ?
              and cid in (select id from cards where did in {ids2str(active_deck_ids)})
            group by 1
            order by 1
            """,
            day_cutoff_ms,
            DAY_MILLISECONDS,
            REVLOG_RESCHED,
            day_cutoff_ms,
        )
        for row in rows:
            days_ago = int(row[0])
            if days_ago >= 0:
                totals_by_days_ago[days_ago] = (int(row[1] or 0), int(row[2] or 0))

    history_days = max(minimum_days, max(totals_by_days_ago, default=0) + 1)
    today_start_seconds = day_cutoff_seconds - DAY_SECONDS
    history_start_seconds = today_start_seconds - ((history_days - 1) * DAY_SECONDS)
    totals_by_index = {
        history_days - days_ago - 1: totals
        for days_ago, totals in totals_by_days_ago.items()
        if days_ago < history_days
    }
    return _history_from_totals(history_start_seconds, history_days, totals_by_index)


def _history_from_totals(
    history_start_seconds: int, days: int, totals_by_index: dict[int, tuple[int, int]]
) -> HistorySnapshot:
    daily_averages = []
    for day_index in range(days):
        day_start_seconds = history_start_seconds + (day_index * DAY_SECONDS)
        day_key = datetime.fromtimestamp(day_start_seconds).date().isoformat()
        cards, milliseconds = totals_by_index.get(day_index, (0, 0))
        daily_averages.append(DailyAverage(day=day_key, cards=cards, milliseconds=milliseconds))

    return HistorySnapshot(days=tuple(daily_averages))


def _weighted_average(days: tuple[DailyAverage, ...]) -> float:
    cards = sum(day.cards for day in days)
    if cards <= 0:
        return 0.0
    milliseconds = sum(day.milliseconds for day in days)
    return round((milliseconds / 1_000) / cards, 2)
