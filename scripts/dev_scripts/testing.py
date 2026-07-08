"""Test command wiring."""

from __future__ import annotations

from scripts.dev_tasks.e2e_parallel import cmd_test_e2e_parallel as run_e2e_parallel
from scripts.dev_tasks.frontend import cmd_build_ui
from scripts.dev_tasks.pytest_runner import run_pytest

E2E_RUNTIME_NOTICE = (
    "[dev] e2e tests start a real Anki runtime; use --idle-timeout 900 if the first local run is slow."
)


def run_test_targets(command_args: list[str]) -> int:
    targets = command_args or ["tests/"]
    for target in targets:
        label = f"python tests: {target}" if command_args else "python tests"
        rc = run_pytest(target, label=label)
        if rc != 0:
            return rc
    return 0


def cmd_test(command_args: list[str]) -> int:
    return run_test_targets(command_args)


def cmd_test_e2e(command_args: list[str]) -> int:
    print(E2E_RUNTIME_NOTICE)
    build_rc = cmd_build_ui()
    if build_rc != 0:
        return build_rc
    targets = command_args or ["e2e/"]
    for target in targets:
        label = f"python e2e tests: {target}" if command_args else "python e2e tests"
        rc = run_pytest(target, label=label)
        if rc != 0:
            return rc
    return 0


def cmd_test_e2e_parallel(command_args: list[str]) -> int:
    print(E2E_RUNTIME_NOTICE)
    build_rc = cmd_build_ui()
    if build_rc != 0:
        return build_rc
    return run_e2e_parallel(command_args)
