# Architecture

## Runtime

Anki loads the add-on from a numeric package path during local development. The add-on code therefore uses package-relative imports and keeps `aqt` imports behind Anki-only entrypoints.

The runtime modules are:

- `__init__.py`: import-safe bootstrap
- `menu.py`: Tools menu registration
- `stats.py`: `revlog` aggregation
- `dialog.py`: Anki WebView dialog
- `webview_shell.py`: HTML, CSS, JS, and initial-state assembly

## Data Flow

1. The user opens `Tools -> Average Time Per Card Today`.
2. Python queries today's local `revlog` rows from `mw.col`.
3. Python embeds the stats into `window.__INITIAL_STATE__`.
4. Svelte renders the average per distinct card, total answer time, review count, card count, and average per answer.

The primary metric is total review time divided by distinct `revlog.cid` values for today's local calendar day.

## Tooling

`scripts/dev.py` is the single developer entrypoint. It discovers Anki's bundled Python, manages the local add-on symlink, runs Python tools in the Anki environment, and runs frontend tools in `webview_ui/`.
