"""Coverage command."""

from __future__ import annotations

from scripts.dev_tasks.process import run_process
from scripts.dev_tasks.python_env import find_anki_python


def cmd_coverage() -> int:
    anki_python = find_anki_python()
    return run_process(
        [
            str(anki_python),
            "-m",
            "pytest",
            "tests/",
            "--cov=addon/anki_time_per_card",
            "--cov=scripts",
            "--cov-report=term-missing",
            "--cov-report=xml",
        ],
        label="python coverage",
        show_output_on_failure=True,
    )
