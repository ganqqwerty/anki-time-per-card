"""Simple e2e pytest sharding."""

from __future__ import annotations

import os
from collections import defaultdict
from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

from scripts.dev_tasks.process import run_capture, run_process
from scripts.dev_tasks.python_env import find_anki_python

DEFAULT_E2E_JOBS = 2


@dataclass(frozen=True)
class E2EFileGroup:
    path: str
    nodeids: tuple[str, ...]

    @property
    def item_count(self) -> int:
        return len(self.nodeids)


@dataclass(frozen=True)
class E2EShard:
    name: str
    file_groups: tuple[E2EFileGroup, ...]

    @property
    def nodeids(self) -> tuple[str, ...]:
        return tuple(nodeid for group in self.file_groups for nodeid in group.nodeids)

    @property
    def item_count(self) -> int:
        return sum(group.item_count for group in self.file_groups)


@dataclass
class _MutableShard:
    name: str
    file_groups: list[E2EFileGroup]

    @property
    def item_count(self) -> int:
        return sum(group.item_count for group in self.file_groups)

    def freeze(self) -> E2EShard:
        return E2EShard(self.name, tuple(sorted(self.file_groups, key=lambda group: group.path)))


def collect_targets(command_args: Sequence[str]) -> list[str]:
    return list(command_args) if command_args else ["e2e/"]


def requested_worker_count(env: Mapping[str, str], shard_count: int) -> int:
    if shard_count <= 0:
        return 0
    raw = env.get("DEV_E2E_JOBS")
    try:
        requested = DEFAULT_E2E_JOBS if raw is None else int(raw)
    except ValueError:
        requested = DEFAULT_E2E_JOBS
    if requested < 1:
        requested = DEFAULT_E2E_JOBS
    return max(1, min(requested, shard_count))


def group_nodeids_by_file(nodeids: Sequence[str]) -> tuple[E2EFileGroup, ...]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for nodeid in nodeids:
        if "::" not in nodeid:
            continue
        grouped[_nodeid_file(nodeid)].append(nodeid)
    return tuple(E2EFileGroup(path, tuple(sorted(grouped[path]))) for path in sorted(grouped))


def plan_shards(file_groups: Sequence[E2EFileGroup], worker_count: int) -> tuple[E2EShard, ...]:
    if worker_count <= 0:
        return ()
    shards = [_MutableShard(name=f"e2e-{index + 1}", file_groups=[]) for index in range(worker_count)]
    for group in sorted(file_groups, key=lambda item: item.item_count, reverse=True):
        shard = min(shards, key=lambda item: item.item_count)
        shard.file_groups.append(group)
    return tuple(shard.freeze() for shard in shards if shard.file_groups)


def cmd_test_e2e_parallel(command_args: list[str]) -> int:
    targets = collect_targets(command_args)
    nodeids = _collect_nodeids(targets)
    if not nodeids:
        print("[dev] no e2e tests collected")
        return 1
    file_groups = group_nodeids_by_file(nodeids)
    worker_count = requested_worker_count(os.environ, len(file_groups))
    shards = plan_shards(file_groups, worker_count)
    print(f"[dev] collected {len(nodeids)} e2e tests across {len(file_groups)} files")
    print(f"[dev] running {len(shards)} e2e shard(s)")

    failures = 0
    with ThreadPoolExecutor(max_workers=max(1, len(shards))) as executor:
        futures = {executor.submit(_run_shard, shard): shard for shard in shards}
        for future in as_completed(futures):
            shard = futures[future]
            rc = future.result()
            if rc != 0:
                failures += 1
            print(f"[dev] shard {shard.name} exited {rc}")
    return 1 if failures else 0


def _collect_nodeids(targets: Sequence[str]) -> tuple[str, ...]:
    anki_python = find_anki_python()
    rc, output = run_capture(
        [str(anki_python), "-m", "pytest", *targets, "--collect-only", "-q"],
        label="collect e2e nodeids",
        show_output_on_failure=True,
    )
    if rc != 0:
        return ()
    nodeids = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if "::" in line and Path(_nodeid_file(line)).suffix == ".py":
            nodeids.append(line)
    return tuple(sorted(nodeids))


def _run_shard(shard: E2EShard) -> int:
    anki_python = find_anki_python()
    return run_process(
        [str(anki_python), "-m", "pytest", "-q", "--tb=short", *shard.nodeids],
        label=f"{shard.name}: {shard.item_count} e2e tests",
        show_output_on_failure=True,
    )


def _nodeid_file(nodeid: str) -> str:
    return nodeid.split("::", 1)[0]
