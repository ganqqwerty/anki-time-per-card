# Live Review Average Overlay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the incorrect Tools-menu/Svelte stats dialog with a Python-only reviewer overlay that shows Anki's studied-today seconds-per-card value while reviewing.

**Architecture:** The add-on registers reviewer/webview hooks, injects one small HTML overlay into Anki's main review WebView, and updates that overlay after reviewer events. The displayed number uses Anki's own studied-today formula for active decks: count non-reschedule revlog rows after the scheduler day start and divide summed `revlog.time` by that count.

**Tech Stack:** Python add-on code running inside Anki, Anki `aqt.gui_hooks`, Anki collection `revlog` queries, existing `scripts/dev.py` quality/build tooling.

---

### Task 1: Remove Wrong UI And Tests

**Files:**
- Delete: `addon/anki_time_per_card/dialog.py`
- Delete: `addon/anki_time_per_card/menu.py`
- Delete: `addon/anki_time_per_card/stats.py`
- Delete: `addon/anki_time_per_card/webview_shell.py`
- Delete: `webview_ui/`
- Delete: `tests/`
- Delete: `e2e/`

- [x] Delete the Tools-menu dialog implementation and the Svelte frontend because the add-on must not expose a menu or after-the-fact dialog.
- [x] Delete the current unit/e2e/frontend tests because they verify the wrong product behavior.

### Task 2: Add Reviewer Overlay Runtime

**Files:**
- Modify: `addon/anki_time_per_card/__init__.py`
- Create: `addon/anki_time_per_card/reviewer_average.py`

- [x] Register hooks from `__init__.py` by importing `reviewer_average.register_hooks()` only when Anki imports are available.
- [x] In `reviewer_average.py`, implement `studied_today_average(col)` with this query:

```sql
select count(), coalesce(sum(time), 0)
from revlog
where type != 4
  and id > ?
  and cid in (select id from cards where did in <active-deck-ids>)
```

- [x] Compute the lower bound as `(col.sched.day_cutoff - 86400) * 1000`, matching `anki.stats.CollectionStats.todayStats()`.
- [x] Inject a fixed-position overlay into the main reviewer WebView via `webview_will_set_content` when the context is an `aqt.reviewer.Reviewer`.
- [x] Update the overlay from `reviewer_did_show_question`, `reviewer_did_show_answer`, and `reviewer_did_answer_card`.

### Task 3: Simplify Dev Runner

**Files:**
- Modify: `scripts/dev_scripts/registry.py`
- Modify: `scripts/dev_scripts/check.py`
- Delete: `scripts/dev_scripts/testing.py`
- Delete: `scripts/dev_tasks/frontend.py`
- Modify: `scripts/dev_tasks/setup.py`
- Delete: `scripts/dev_tasks/coverage.py`
- Delete: `scripts/dev_tasks/e2e_parallel.py`
- Delete: `scripts/dev_tasks/node_tools.py`

- [x] Remove frontend build/validation behavior and Node dependency installation.
- [x] Remove test/e2e/coverage/frontend command registrations.
- [x] Keep `setup`, `link-addon`, `run-anki`, `build`, `lint`, `typecheck`, `file-lines`, `security`, `deadcode`, `deps`, `complexity`, `check`, and `info`.
- [x] Make `build` byte-compile only the add-on and scripts.
- [x] Make `check` run only Python build and quality commands.

### Task 4: Update Docs

**Files:**
- Modify: `README.md`
- Modify: `DEVELOPMENT.md`
- Modify: `TESTING.md`
- Delete: `E2E_TESTING.md`
- Modify: `ARCHITECTURE.md`
- Modify: `ANKI_API.md`
- Modify: `pyproject.toml`
- Modify: `.gitignore`

- [x] Remove references to Svelte, WebView dialogs, Tools menu, frontend tests, unit tests, and e2e tests.
- [x] Document that the add-on is Python-only and shows one live `s/card` number in the reviewer.
- [x] Keep docs for setup, link, run, build, and quality commands.

### Task 5: Verify And Commit

**Files:**
- All modified files.

- [x] Run `python3 scripts/dev.py build` and confirm exit code 0.
- [x] Run `python3 scripts/dev.py check` and confirm exit code 0.
- [x] Run `python3 scripts/dev.py link-addon` and confirm the numeric add-on symlink points at this checkout.
- [x] Run `python3 scripts/dev.py run-anki` and confirm Anki launch command succeeds.
- [ ] Commit on `main` with a message that explains why the wrong dialog/test surface was removed and what behavior the replacement provides.
