"""Frontend build and validation commands."""

from __future__ import annotations

import sys

from scripts.dev_tasks.node_tools import WEBVIEW_UI_DIR, frontend_npm_command
from scripts.dev_tasks.process import run_process
from scripts.dev_tasks.python_env import _warn_if_addon_symlink_mismatch, die


def cmd_build_ui() -> int:
    if not WEBVIEW_UI_DIR.is_dir():
        die("webview_ui/ directory not found.")
    npm = frontend_npm_command("build")
    if not npm:
        die("npm not found. Install Node.js 18+.")
    assert npm is not None
    rc = run_process(npm, cwd=WEBVIEW_UI_DIR, label="frontend webview bundle build")
    if rc == 0:
        _warn_if_addon_symlink_mismatch()
    return rc


def cmd_build() -> int:
    ui_rc = cmd_build_ui()
    if ui_rc != 0:
        return ui_rc
    from scripts.dev_tasks.python_env import find_anki_python

    anki_python = find_anki_python()
    return run_process(
        [str(anki_python), "-m", "compileall", "-q", "addon", "scripts", "tests", "e2e"],
        label="python byte-compile",
    )


def cmd_test_svelte() -> int:
    if not WEBVIEW_UI_DIR.is_dir():
        print("ERROR: webview_ui/ not found; cannot validate frontend.", file=sys.stderr)
        return 1
    npm = frontend_npm_command("validate")
    if not npm:
        print("ERROR: npm not found. Install Node.js 18+.", file=sys.stderr)
        return 1
    if not (WEBVIEW_UI_DIR / "node_modules").is_dir():
        print("ERROR: webview_ui/node_modules not found. Run: python3 scripts/dev.py setup", file=sys.stderr)
        return 1
    build_rc = cmd_build_ui()
    if build_rc != 0:
        return build_rc
    return run_process(npm, cwd=WEBVIEW_UI_DIR, label="frontend validation")
