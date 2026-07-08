"""Python-only add-on build command."""

from __future__ import annotations

from scripts.dev_tasks.process import run_process
from scripts.dev_tasks.python_env import _warn_if_addon_symlink_mismatch, find_anki_python


def cmd_build() -> int:
    anki_python = find_anki_python()
    rc = run_process(
        [str(anki_python), "-m", "compileall", "-q", "addon", "scripts"],
        label="python byte-compile",
    )
    if rc == 0:
        _warn_if_addon_symlink_mismatch()
    return rc
