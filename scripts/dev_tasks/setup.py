"""One-time repository setup command."""

from __future__ import annotations

import sys

from scripts.dev_tasks.node_tools import WEBVIEW_UI_DIR, find_npm_install_command
from scripts.dev_tasks.process import run_process
from scripts.dev_tasks.python_env import _find_anki_python, _setup_addon_symlink

DEV_DEPS = [
    "argcomplete",
    "pytest>=8.0",
    "pytest-cov",
    "pytest-qt",
    "ruff",
    "mypy",
    "radon",
    "deptry",
    "vulture>=2.14",
    "bandit",
]


def cmd_setup() -> int:
    anki_python = _find_anki_python()
    print(f"Anki Python: {anki_python}")
    pip_rc = run_process(
        [str(anki_python), "-m", "pip", "install", *DEV_DEPS],
        label="installing Python dev dependencies",
    )
    if pip_rc == 0:
        print(f"  Installed: {', '.join(DEV_DEPS)}")
    _setup_addon_symlink()

    npm_rc = 0
    npm = find_npm_install_command()
    if WEBVIEW_UI_DIR.is_dir():
        if npm:
            npm_cmd = [*npm, "ci"]
            if not (WEBVIEW_UI_DIR / "package-lock.json").is_file():
                npm_cmd = [*npm, "install"]
            npm_rc = run_process(npm_cmd, cwd=WEBVIEW_UI_DIR, label="webview UI npm install")
        else:
            print("ERROR: npm not found. Install Node.js 18+ with npm.", file=sys.stderr)
            npm_rc = 1
    if pip_rc != 0:
        return pip_rc
    return npm_rc
