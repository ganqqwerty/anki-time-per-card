"""One-time repository setup command."""

from __future__ import annotations

from scripts.dev_tasks.process import run_process
from scripts.dev_tasks.python_env import _find_anki_python, _setup_addon_symlink

DEV_DEPS = [
    "argcomplete",
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
    return pip_rc
