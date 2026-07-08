"""Python lint and typecheck commands."""

from __future__ import annotations

from scripts.dev_tasks.process import run_process
from scripts.dev_tasks.python_env import find_anki_python

PYTHON_TARGETS = ["addon", "scripts"]


def cmd_lint(_command_args: list[str]) -> int:
    anki_python = find_anki_python()
    fix_rc = run_process([str(anki_python), "-m", "ruff", "check", "--fix", "."], label="ruff lint autofix")
    if fix_rc != 0:
        return fix_rc
    return run_process([str(anki_python), "-m", "ruff", "format", "--check", "."], label="ruff format check")


def run_typecheck() -> int:
    anki_python = find_anki_python()
    return run_process([str(anki_python), "-m", "mypy", *PYTHON_TARGETS], label="mypy typecheck")


def cmd_typecheck(_command_args: list[str]) -> int:
    return run_typecheck()
