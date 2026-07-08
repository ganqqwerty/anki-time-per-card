# Anki Time Per Card

Anki Time Per Card is a small local Anki add-on that shows one live number during review: Anki's studied-today average answer time for the active deck, rendered as `s/card`.

The number matches Anki's own studied-today calculation: non-reschedule review log rows for the active deck since Anki's scheduler day start, using total recorded review time divided by review count.

## Quick Start

```bash
python3 scripts/dev.py setup
python3 scripts/dev.py build
python3 scripts/dev.py link-addon
python3 scripts/dev.py run-anki
```

In Anki, review cards normally. The average appears in the top-right corner of the reviewer.

## Common Commands

```bash
python3 scripts/dev.py check
python3 scripts/dev.py info
```

The Python commands run through Anki's bundled Python so tooling sees the same `anki` and `aqt` packages used by the add-on at runtime.
