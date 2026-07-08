"""Quality command wiring."""

from __future__ import annotations

from pathlib import Path

from scripts.dev_tasks.process import run_process
from scripts.dev_tasks.python_env import find_anki_python

ROOT = Path(__file__).resolve().parents[2]
PYTHON_TARGETS = ["addon/anki_time_per_card", "scripts"]


def cmd_security(_command_args: list[str]) -> int:
    anki_python = find_anki_python()
    return run_process(
        [
            str(anki_python),
            "-m",
            "bandit",
            "-r",
            "addon/anki_time_per_card",
            "-c",
            "pyproject.toml",
            "-ll",
            "-ii",
        ],
        label="bandit security",
    )


def cmd_deadcode(_command_args: list[str]) -> int:
    anki_python = find_anki_python()
    paths = [*PYTHON_TARGETS]
    whitelist = ROOT / "vulture_whitelist.py"
    if whitelist.is_file():
        paths.append(str(whitelist))
    return run_process(
        [str(anki_python), "-m", "vulture", *paths, "--min-confidence", "90"],
        label="vulture deadcode",
    )


def cmd_deps(_command_args: list[str]) -> int:
    anki_python = find_anki_python()
    return run_process([str(anki_python), "-m", "deptry", "."], label="deptry dependency check")


def cmd_complexity(_command_args: list[str]) -> int:
    anki_python = find_anki_python()
    cc_rc = run_process(
        [str(anki_python), "-m", "radon", "cc", "-s", "-a", *PYTHON_TARGETS],
        label="radon cyclomatic complexity",
    )
    if cc_rc != 0:
        return cc_rc
    return run_process(
        [str(anki_python), "-m", "radon", "mi", "-s", *PYTHON_TARGETS],
        label="radon maintainability",
    )


def cmd_quality_metrics(command_args: list[str]) -> int:
    return cmd_complexity(command_args)
