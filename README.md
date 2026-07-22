# Anki Time Per Card

Anki Time Per Card shows a live studied-today average during review and a 30-day pace history on Anki's Statistics screen.

The number matches Anki's own studied-today calculation: non-reschedule review log rows for the active deck since Anki's scheduler day start, using total recorded review time divided by review count.

The Statistics screen derives daily averages from the same durable review log, so existing history appears immediately. Radio buttons switch between the last week, last month, last year, and all recorded history. Each fixed period includes a review-weighted comparison with the preceding period, a daily seconds-per-card trend, and daily review volume. Lower time-per-card values indicate a faster review pace.

## Quick Start

```bash
python3 scripts/dev.py setup
python3 scripts/dev.py build
python3 scripts/dev.py link-addon
python3 scripts/dev.py run-anki
```

In Anki, review cards normally. The average appears in the top-right corner of the reviewer. Open **Statistics** to see the current deck's 30-day progress charts.

## Common Commands

```bash
python3 scripts/dev.py check
python3 scripts/dev.py test
python3 scripts/dev.py info
```

The Python commands run through Anki's bundled Python so tooling sees the same `anki` and `aqt` packages used by the add-on at runtime.
