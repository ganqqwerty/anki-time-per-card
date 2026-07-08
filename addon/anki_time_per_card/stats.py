"""Review-log aggregation for today's average time per card."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

Milliseconds = int


@dataclass(frozen=True)
class DayBounds:
    """Local day bounds rendered for Anki's millisecond review-log ids."""

    start: datetime
    end: datetime

    @property
    def start_ms(self) -> Milliseconds:
        return int(self.start.timestamp() * 1000)

    @property
    def end_ms(self) -> Milliseconds:
        return int(self.end.timestamp() * 1000)


@dataclass(frozen=True)
class ReviewStats:
    """JSON-serializable metrics for the WebView."""

    date_label: str
    day_start_ms: Milliseconds
    day_end_ms: Milliseconds
    review_count: int
    distinct_card_count: int
    total_answer_time_ms: Milliseconds
    average_per_card_ms: float
    average_per_answer_ms: float

    def to_webview_state(self) -> dict[str, int | float | str]:
        return {
            "dateLabel": self.date_label,
            "dayStartMs": self.day_start_ms,
            "dayEndMs": self.day_end_ms,
            "reviewCount": self.review_count,
            "distinctCardCount": self.distinct_card_count,
            "totalAnswerTimeMs": self.total_answer_time_ms,
            "averagePerCardMs": self.average_per_card_ms,
            "averagePerAnswerMs": self.average_per_answer_ms,
        }


def local_day_bounds(now: datetime | None = None) -> DayBounds:
    """Return local midnight-to-midnight bounds for ``now``."""

    local_now = datetime.now().astimezone() if now is None else now.astimezone()
    start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    return DayBounds(start=start, end=start + timedelta(days=1))


def empty_review_stats(now: datetime | None = None) -> ReviewStats:
    bounds = local_day_bounds(now)
    return ReviewStats(
        date_label=bounds.start.date().isoformat(),
        day_start_ms=bounds.start_ms,
        day_end_ms=bounds.end_ms,
        review_count=0,
        distinct_card_count=0,
        total_answer_time_ms=0,
        average_per_card_ms=0.0,
        average_per_answer_ms=0.0,
    )


def today_review_stats(collection: Any, now: datetime | None = None) -> ReviewStats:
    """Compute today's review-time metrics from an Anki collection."""

    bounds = local_day_bounds(now)
    rows = collection.db.all(
        """
        select cid, time
        from revlog
        where id >= ? and id < ?
        """,
        bounds.start_ms,
        bounds.end_ms,
    )
    return review_stats_from_rows(rows, bounds)


def review_stats_from_rows(rows: list[Any] | tuple[Any, ...], bounds: DayBounds) -> ReviewStats:
    total_answer_time_ms = 0
    reviewed_card_ids: set[int] = set()

    for row in rows:
        cid = int(_row_value(row, key="cid", index=0))
        answer_time_ms = max(0, int(_row_value(row, key="time", index=1)))
        reviewed_card_ids.add(cid)
        total_answer_time_ms += answer_time_ms

    review_count = len(rows)
    distinct_card_count = len(reviewed_card_ids)
    average_per_card_ms = _safe_average(total_answer_time_ms, distinct_card_count)
    average_per_answer_ms = _safe_average(total_answer_time_ms, review_count)

    return ReviewStats(
        date_label=bounds.start.date().isoformat(),
        day_start_ms=bounds.start_ms,
        day_end_ms=bounds.end_ms,
        review_count=review_count,
        distinct_card_count=distinct_card_count,
        total_answer_time_ms=total_answer_time_ms,
        average_per_card_ms=average_per_card_ms,
        average_per_answer_ms=average_per_answer_ms,
    )


def _safe_average(total: int, count: int) -> float:
    if count <= 0:
        return 0.0
    return round(total / count, 3)


def _row_value(row: Any, *, key: str, index: int) -> Any:
    if isinstance(row, Mapping):
        return row[key]
    if hasattr(row, key):
        return getattr(row, key)
    return row[index]
