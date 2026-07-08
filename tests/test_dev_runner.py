from __future__ import annotations

import pytest

from scripts.dev_cli import parse_cli_args
from scripts.dev_scripts.runner import run_command
from scripts.dev_scripts.types import CommandRegistry
from scripts.dev_tasks.e2e_parallel import (
    E2EFileGroup,
    group_nodeids_by_file,
    plan_shards,
    requested_worker_count,
)


def test_parse_cli_rejects_global_options_after_command() -> None:
    commands: CommandRegistry = {"test": (lambda _args: 0, "run tests")}

    with pytest.raises(SystemExit):
        parse_cli_args(["test", "--verbose"], commands)


def test_run_command_dispatches_selected_command() -> None:
    calls: list[list[str]] = []

    def _command(args: list[str]) -> int:
        calls.append(args)
        return 7

    commands: CommandRegistry = {"demo": (_command, "demo command")}

    rc = run_command("demo", ["one", "two"], verbose=False, idle_timeout_s=None, commands=commands)

    assert rc == 7
    assert calls == [["one", "two"]]


def test_e2e_nodeids_are_grouped_by_file() -> None:
    groups = group_nodeids_by_file(
        [
            "e2e/test_a.py::test_two",
            "e2e/test_b.py::test_one",
            "e2e/test_a.py::test_one",
        ]
    )

    assert groups == (
        E2EFileGroup("e2e/test_a.py", ("e2e/test_a.py::test_one", "e2e/test_a.py::test_two")),
        E2EFileGroup("e2e/test_b.py", ("e2e/test_b.py::test_one",)),
    )


def test_e2e_worker_count_is_bounded() -> None:
    assert requested_worker_count({"DEV_E2E_JOBS": "8"}, shard_count=2) == 2
    assert requested_worker_count({"DEV_E2E_JOBS": "0"}, shard_count=3) == 2
    assert requested_worker_count({"DEV_E2E_JOBS": "bad"}, shard_count=1) == 1


def test_plan_shards_balances_files() -> None:
    shards = plan_shards(
        [
            E2EFileGroup("e2e/test_a.py", ("a1", "a2", "a3")),
            E2EFileGroup("e2e/test_b.py", ("b1",)),
            E2EFileGroup("e2e/test_c.py", ("c1",)),
        ],
        worker_count=2,
    )

    assert len(shards) == 2
    assert sorted(shard.item_count for shard in shards) == [2, 3]
