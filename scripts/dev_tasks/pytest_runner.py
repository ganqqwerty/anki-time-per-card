"""Pytest command helpers."""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Sequence
from pathlib import Path

from scripts.dev_tasks.process import _read_seconds_env, is_verbose, run_process
from scripts.dev_tasks.python_env import find_anki_python


def _pytest_args(
    targets: str | Sequence[str],
    *,
    collect_only: bool = False,
    cache_dir: Path | None = None,
) -> list[str]:
    target_args = [targets] if isinstance(targets, str) else list(targets)
    args = ["pytest", *target_args]
    if is_verbose():
        args.extend(["-vv", "--durations=20", "-s"])
    else:
        args.extend(["-q", "--tb=short", "--show-capture=all", "-rfE"])
    if cache_dir is not None:
        args.extend(["-o", f"cache_dir={cache_dir}"])
    if collect_only:
        args.append("--collect-only")
    return args


def run_pytest(targets: str | Sequence[str], *, label: str) -> int:
    anki_python = find_anki_python()
    collect_warning_s = _read_seconds_env("DEV_PYTEST_COLLECT_WARNING_SECS", 10.0)
    collect_timeout_s = _read_seconds_env("DEV_PYTEST_COLLECT_TIMEOUT_SECS", 60.0)
    pytest_cache_dir = Path(tempfile.mkdtemp(prefix="atpc-pytest-cache-"))
    try:
        rc = run_process(
            [str(anki_python), "-m", *_pytest_args(targets, collect_only=True, cache_dir=pytest_cache_dir)],
            label=f"{label} (collect)",
            idle_warning_s=collect_warning_s,
            idle_timeout_s=collect_timeout_s,
            show_output_on_failure=True,
        )
        if rc != 0:
            return rc
        return run_process(
            [str(anki_python), "-m", *_pytest_args(targets, cache_dir=pytest_cache_dir)],
            label=f"{label} (run)",
            show_output_on_failure=True,
        )
    finally:
        shutil.rmtree(pytest_cache_dir, ignore_errors=True)
