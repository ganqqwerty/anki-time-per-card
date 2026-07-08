"""Shared Qt/WebView polling helpers for e2e tests."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from typing import Any

from PyQt6.QtWidgets import QApplication

DEFAULT_E2E_TIMEOUT = 5.0


def _run_event_loop_step() -> None:
    QApplication.processEvents()
    time.sleep(0.01)


def run_js(target, expr: str, callback: Callable[[Any], None] | None = None) -> None:
    if hasattr(target, "run_js"):
        target.run_js(expr, callback)
        return
    if hasattr(target, "evalWithCallback"):
        target.evalWithCallback(expr, callback)
        return
    target.page().runJavaScript(expr, callback)


def wait_for_js(target, expr: str, timeout: float = DEFAULT_E2E_TIMEOUT):
    result = [None]

    def _capture(value):
        result[0] = value

    deadline = time.time() + timeout
    while time.time() < deadline:
        result[0] = None
        run_js(target, expr, _capture)
        inner_deadline = time.time() + 0.25
        while result[0] is None and time.time() < inner_deadline:
            _run_event_loop_step()
        if result[0] is not None:
            return result[0]
        _run_event_loop_step()
    raise TimeoutError(f"Timed out waiting for JS result: {expr}")


def wait_for_js_condition(
    target,
    expr: str,
    predicate: Callable[[Any], bool] = bool,
    timeout: float = DEFAULT_E2E_TIMEOUT,
):
    deadline = time.time() + timeout
    last_result: Any = None
    while time.time() < deadline:
        remaining = max(0.01, deadline - time.time())
        try:
            result = wait_for_js(target, expr, timeout=min(0.5, remaining))
            last_result = result
            if predicate(result):
                return result
        except TimeoutError:
            pass
        _run_event_loop_step()
    raise TimeoutError(f"Condition not met within {timeout}s for: {expr} (last result: {last_result!r})")


def wait_for_selector(target, selector: str, timeout: float = DEFAULT_E2E_TIMEOUT) -> bool:
    expr = f"document.querySelector({json.dumps(selector)}) !== null"
    result = wait_for_js_condition(target, expr, timeout=timeout)
    return bool(result)
