"""Full check command wiring."""

from __future__ import annotations

from collections.abc import Callable

from scripts.dev_scripts.quality import cmd_deadcode, cmd_deps, cmd_quality_metrics, cmd_security
from scripts.dev_scripts.testing import cmd_test
from scripts.dev_scripts.tooling import cmd_lint, cmd_typecheck
from scripts.dev_tasks.coverage import cmd_coverage
from scripts.dev_tasks.frontend import cmd_build_ui, cmd_test_svelte
from scripts.dev_tasks.repository import cmd_file_lines

CheckStep = tuple[str, Callable[[], int]]


def cmd_check(_command_args: list[str]) -> int:
    print("[dev] check runs build, Python quality tools, Python tests, coverage, and frontend validation")
    steps: list[CheckStep] = [
        ("build-ui", cmd_build_ui),
        ("lint", lambda: cmd_lint([])),
        ("typecheck", lambda: cmd_typecheck([])),
        ("file-lines", cmd_file_lines),
        ("security", lambda: cmd_security([])),
        ("deadcode", lambda: cmd_deadcode([])),
        ("deps", lambda: cmd_deps([])),
        ("complexity", lambda: cmd_quality_metrics([])),
        ("test", lambda: cmd_test([])),
        ("coverage", cmd_coverage),
        ("test-svelte", cmd_test_svelte),
    ]
    for name, step in steps:
        print(f"[dev] check step: {name}")
        rc = step()
        if rc != 0:
            print(f"[dev] check stopped at {name}")
            return rc
    return 0
