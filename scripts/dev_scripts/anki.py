"""Anki launch and environment information commands."""

from __future__ import annotations

from pathlib import Path

from scripts.dev_tasks.frontend import cmd_build_ui
from scripts.dev_tasks.node_tools import frontend_runner_status
from scripts.dev_tasks.python_env import (
    ADDON_SYMLINK_ID,
    ROOT,
    _format_addon_link_status,
    _print_addon_symlink_info,
    cmd_launch_anki,
    cmd_link_addon,
    find_anki_python,
)


def cmd_run_anki(_command_args: list[str]) -> int:
    build_rc = cmd_build_ui()
    if build_rc != 0:
        return build_rc
    link_rc = cmd_link_addon()
    if link_rc != 0:
        return link_rc
    return cmd_launch_anki()


def cmd_info(_command_args: list[str]) -> int:
    anki_python = find_anki_python()
    node_version, npm_runner = frontend_runner_status()
    print(f"Project root:  {ROOT}")
    print(f"Anki Python:   {anki_python}")
    print(f"Add-on ID:     {ADDON_SYMLINK_ID}")
    _print_addon_symlink_info()
    print(f"Node.js:       {node_version or 'not found'}")
    print(f"npm runner:    {npm_runner}")
    print(f"Web bundle:    {Path('addon/anki_time_per_card/web').resolve()}")
    print(f"Link status:   {_format_addon_link_status()}")
    return 0
