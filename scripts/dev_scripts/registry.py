"""Command registry for scripts/dev.py."""

from __future__ import annotations

from collections.abc import Callable

from scripts.dev_scripts.anki import cmd_info, cmd_run_anki
from scripts.dev_scripts.check import cmd_check
from scripts.dev_scripts.quality import cmd_deadcode, cmd_deps, cmd_quality_metrics, cmd_security
from scripts.dev_scripts.testing import cmd_test, cmd_test_e2e, cmd_test_e2e_parallel
from scripts.dev_scripts.tooling import cmd_lint, cmd_typecheck
from scripts.dev_scripts.types import Command, CommandRegistry
from scripts.dev_tasks.coverage import cmd_coverage
from scripts.dev_tasks.frontend import cmd_build, cmd_build_ui, cmd_test_svelte
from scripts.dev_tasks.python_env import cmd_link_addon
from scripts.dev_tasks.repository import cmd_file_lines
from scripts.dev_tasks.setup import cmd_setup


def no_args(command: Callable[[], int]) -> Command:
    return lambda _command_args: command()


COMMANDS: CommandRegistry = {
    "setup": (no_args(cmd_setup), "Install Python dev tools, create add-on symlink, and npm install"),
    "link-addon": (no_args(cmd_link_addon), "Point Anki's local numeric add-on symlink at this checkout"),
    "run-anki": (cmd_run_anki, "Build UI, link this checkout add-on, and launch real Anki"),
    "build": (no_args(cmd_build), "Build frontend bundles and byte-compile Python"),
    "build-ui": (no_args(cmd_build_ui), "Build the Svelte WebView bundle"),
    "test": (cmd_test, "Run Python unit tests"),
    "test-e2e": (cmd_test_e2e, "Build frontend bundles, then run real-Anki e2e tests"),
    "test-e2e-parallel": (cmd_test_e2e_parallel, "Build frontend bundles, then run e2e tests in shards"),
    "test-svelte": (no_args(cmd_test_svelte), "Build and validate the Svelte WebView app"),
    "lint": (cmd_lint, "Run Ruff safe autofix, then formatting check"),
    "typecheck": (cmd_typecheck, "Run mypy type checker"),
    "file-lines": (no_args(cmd_file_lines), "Check Python file lengths"),
    "security": (cmd_security, "Run Bandit security linter"),
    "deadcode": (cmd_deadcode, "Find dead code with Vulture"),
    "deps": (cmd_deps, "Check dependencies with Deptry"),
    "complexity": (cmd_quality_metrics, "Run Radon complexity and maintainability checks"),
    "coverage": (no_args(cmd_coverage), "Run Python tests with branch coverage"),
    "check": (cmd_check, "Run the full non-e2e quality pipeline"),
    "info": (cmd_info, "Print discovered Anki and frontend tool status"),
}
