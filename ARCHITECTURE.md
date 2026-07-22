# Architecture

## Runtime

Anki loads the add-on from a numeric package path during local development. Runtime imports are package-relative, and `aqt` hook registration is delayed until Anki imports the add-on.

The runtime modules are:

- `__init__.py`: import-safe bootstrap
- `reviewer_average.py`: reviewer WebView overlay injection and studied-today average calculation
- `daily_stats.py`: 30-day scheduler-day aggregation and weighted weekly comparisons
- `stats_screen.py`: responsive summary cards and SVG charts for Anki's Statistics screen

## Data Flow

1. Anki initializes the reviewer WebView.
2. The add-on injects a small fixed-position overlay into the main reviewer page.
3. Reviewer hooks fire when a question/answer is shown and after a card is answered.
4. Python queries `revlog` using Anki's studied-today formula for active decks.
5. Python updates the overlay text with the current `s/card` value.

The metric is total recorded review time divided by total answered-card rows, excluding reschedule rows, since Anki's scheduler day start.

When the Statistics screen loads, the add-on groups the active deck's `revlog` rows into scheduler days from the first review through today, retaining enough leading days for year-over-year comparison. The review log remains the single durable source of truth; the add-on does not create a second history store. It fills days without reviews as chart gaps, prepares week, month, year, and all-time views, and injects dependency-free SVG charts after Anki applies its page styling. Native radio controls switch the visible period without another database query.

## Tooling

`scripts/dev.py` is the single developer entrypoint. It discovers Anki's bundled Python, manages the local add-on symlink, and runs Python build and quality tools in the Anki environment.
