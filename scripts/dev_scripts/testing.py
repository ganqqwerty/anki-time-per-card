"""Unit-test command wiring."""

from __future__ import annotations

from pathlib import Path

from scripts.dev_tasks.process import run_process
from scripts.dev_tasks.python_env import find_anki_python

ROOT = Path(__file__).resolve().parents[2]


def cmd_test(_command_args: list[str]) -> int:
    anki_python = find_anki_python()
    return run_process(
        [str(anki_python), "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=ROOT,
        label="unit tests",
    )
