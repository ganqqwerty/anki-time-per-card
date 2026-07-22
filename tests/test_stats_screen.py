from __future__ import annotations

import unittest

from addon.anki_time_per_card.daily_stats import DailyAverage, HistorySnapshot
from addon.anki_time_per_card.stats_screen import _history_range, _injection_script, _statistics_html


class StatisticsHtmlTest(unittest.TestCase):
    def setUp(self) -> None:
        previous = [DailyAverage(f"2026-07-{day:02d}", 10, 20_000) for day in range(1, 8)]
        recent = [DailyAverage(f"2026-07-{day:02d}", 10, 10_000) for day in range(8, 15)]
        self.snapshot = HistorySnapshot(tuple(previous + recent))

    def test_renders_summary_and_both_progress_charts(self) -> None:
        markup = _statistics_html(self.snapshot)

        self.assertIn('id="anki-time-per-card-stats"', markup)
        self.assertIn("50.0% faster", markup)
        self.assertIn("Seconds per card", markup)
        self.assertIn("Review volume", markup)
        self.assertEqual(markup.count('type="radio"'), 4)
        self.assertIn("Last week", markup)
        self.assertIn("Last month", markup)
        self.assertIn("Last year", markup)
        self.assertIn("All time", markup)
        self.assertIn('value="month" checked', markup)
        self.assertEqual(markup.count("<svg"), 8)
        self.assertIn("July 14, 2026: 1.00s/card, 10 reviews", markup)

    def test_injection_replaces_an_existing_panel(self) -> None:
        script = _injection_script(self.snapshot)

        self.assertIn("previous.remove()", script)
        self.assertIn('document.querySelector("main") || document.body', script)
        self.assertIn("insertAdjacentHTML", script)
        self.assertIn('section.addEventListener("change"', script)
        self.assertIn("__ankiTimePerCardStatsPeriod", script)

    def test_empty_period_is_not_presented_as_zero_second_progress(self) -> None:
        empty = HistorySnapshot(tuple(DailyAverage(f"2026-07-{day:02d}", 0, 0) for day in range(1, 15)))

        markup = _statistics_html(empty)

        self.assertEqual(markup.count("No reviews in this period"), 8)
        self.assertIn("Not enough data", markup)
        self.assertIn('<strong class="">—</strong>', markup)

    def test_multi_year_range_includes_both_years(self) -> None:
        snapshot = HistorySnapshot(
            (
                DailyAverage("2025-07-21", 1, 1_000),
                DailyAverage("2026-07-20", 1, 1_000),
            )
        )

        separator = " \N{EN DASH} "
        self.assertEqual(_history_range(snapshot), f"Jul 21, 2025{separator}Jul 20, 2026")


if __name__ == "__main__":
    unittest.main()
