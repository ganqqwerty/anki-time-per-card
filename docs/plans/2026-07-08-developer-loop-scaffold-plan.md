# Developer Loop Scaffold Implementation Plan

## Goal

Build a small Anki add-on project that keeps the useful developer loop from the source project while removing audio-specific, release-specific, and managed-runtime-specific machinery.

The scaffold must support:

- building the add-on from Python and Svelte sources
- linking this worktree into Anki's `addons21` directory
- launching Anki with the linked add-on
- running unit tests and real-Anki e2e tests
- running quality checks from one `scripts/dev.py` entrypoint
- documenting the workflow without naming the source project

## Architecture

The add-on runtime lives in `addon/anki_time_per_card/`. Anki imports it from a numeric symlink during local development, so runtime imports must be package-relative and must not assume the friendly source package name.

The visible feature is a Tools menu action that opens an Anki WebView dialog. Python reads today's `revlog` rows from the active collection, builds a JSON initial state, and a Svelte app renders the average time per reviewed card plus supporting counts.

The developer runner lives under `scripts/`. `scripts/dev.py` runs on system Python and discovers Anki's bundled Python for pytest, Ruff, mypy, and other Python tools. Frontend commands run inside `webview_ui/` and build generated bundles into `addon/anki_time_per_card/web/`.

## Files To Create

- `.gitignore`: ignore generated Python, Node, coverage, bundle, and CodeGraph artifacts.
- `.env.example`: document `ANKI_PYTHON` override.
- `AGENTS.md`: project-specific development guidance and CodeGraph usage.
- `README.md`: project overview and quick start.
- `DEVELOPMENT.md`: two-Python setup, setup/link/run/build workflow, frontend notes.
- `TESTING.md`: test and quality commands.
- `E2E_TESTING.md`: real Anki runtime test design.
- `ARCHITECTURE.md`: concise runtime and tooling architecture.
- `ANKI_API.md`: local Anki API guidance.
- `pyproject.toml`: Python project metadata and tool config.
- `addon/anki_time_per_card/__init__.py`: import-safe add-on bootstrap.
- `addon/anki_time_per_card/_version.py`: add-on version.
- `addon/anki_time_per_card/manifest.json`: Anki manifest.
- `addon/anki_time_per_card/config.json`: empty default config.
- `addon/anki_time_per_card/menu.py`: hook registration and Tools menu action.
- `addon/anki_time_per_card/stats.py`: import-safe revlog aggregation.
- `addon/anki_time_per_card/dialog.py`: Anki WebView dialog shell.
- `addon/anki_time_per_card/webview_shell.py`: HTML assembly helper for generated bundles.
- `webview_ui/package.json`: Svelte/Vite scripts and dependencies.
- `webview_ui/tsconfig.json`: strict TypeScript config.
- `webview_ui/vite.config.ts`: bundle config targeting the add-on `web/` directory.
- `webview_ui/vitest.config.ts`: frontend test config.
- `webview_ui/eslint.config.js`: frontend lint config.
- `webview_ui/src/main.ts`: Svelte mount entrypoint.
- `webview_ui/src/App.svelte`: stats UI.
- `webview_ui/src/lib/format.ts`: frontend formatting helpers.
- `webview_ui/src/lib/state.ts`: frontend state types and fallback state.
- `webview_ui/tests/format.test.ts`: frontend unit tests.
- `webview_ui/tests/setup.ts`: jsdom setup.
- `scripts/dev.py`, `scripts/dev_cli.py`: dev runner entrypoint and parser.
- `scripts/dev_scripts/*`: command registry and high-level command orchestration.
- `scripts/dev_tasks/*`: process runner, Anki discovery, frontend build, pytest, e2e sharding, quality helpers, setup.
- `tests/conftest.py`: unit test import path setup.
- `tests/test_stats.py`: import-safe stats unit tests.
- `tests/test_dev_runner.py`: dev runner behavior tests.
- `e2e/conftest.py`: temporary Anki profile and numeric add-on install.
- `e2e/helpers.py`: Qt/WebView polling helpers.
- `e2e/test_average_time_dialog.py`: real-Anki WebView e2e coverage.

## Implementation Steps

1. Create the plan and docs before code changes so future maintainers know which parts were intentionally copied and which were omitted.
2. Add the Python add-on runtime:
   - keep bootstrap import-safe outside Anki
   - register menu hooks only when `aqt` is importable
   - compute stats from `revlog.id` and `revlog.time`
   - render a WebView dialog from generated JS/CSS bundles
3. Add the Svelte frontend:
   - mount from `window.__INITIAL_STATE__`
   - show average per distinct reviewed card as the primary metric
   - show review count, distinct card count, total time, and average per answer as supporting metrics
4. Add the dev runner:
   - preserve concise/verbose output and idle-timeout handling
   - preserve Anki Python discovery and numeric symlink management
   - preserve build, run, test, e2e, parallel e2e, setup, info, and quality commands
   - remove source-project release/runtime/audio/contract commands
5. Add tests:
   - unit tests for day bounds, zero-review stats, revlog aggregation, and CLI run behavior
   - frontend tests for display formatting
   - e2e test that installs the add-on under the numeric package, inserts revlog rows, opens the dialog, and checks the rendered average
6. Generate dependency locks:
   - run npm install in `webview_ui/`
   - rely on `scripts/dev.py setup` to install Python tooling into Anki's Python
7. Verify:
   - `python3 scripts/dev.py build`
   - `python3 scripts/dev.py test`
   - `python3 scripts/dev.py test-svelte`
   - `python3 scripts/dev.py check`
   - `python3 scripts/dev.py test-e2e`

## Decisions

- Use local calendar day bounds, not scheduler rollover, because the feature request says "today's Anki session" and the UI explicitly labels the interval as today's local review log rows.
- Use distinct `revlog.cid` count for the primary "per card" average, and still display average per answer to avoid hiding repeat answers on the same card.
- Use numeric local add-on ID `1000000003` so this scaffold can coexist with other local add-ons.
- Keep generated WebView bundles ignored. The source of truth is `webview_ui/src/`; dev commands rebuild bundles before e2e.
- Keep quality tooling practical for a small scaffold: Ruff, mypy, Bandit, Vulture, Deptry, Radon, file-length scan, Python tests, coverage, and frontend validation.

## Verification Notes

The e2e test is the feature acceptance test. It creates a temporary Anki profile, copies the add-on under `addons21/1000000003`, inserts review log rows for two distinct cards, opens the dialog, and verifies the Svelte-rendered primary metric. That proves the Python runtime, Svelte build output, numeric package import path, and real Anki WebView path work together.
