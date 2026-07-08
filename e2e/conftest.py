"""E2E test setup for the local Anki add-on."""

from __future__ import annotations

import importlib
import os
import shutil
import signal
import subprocess
import sys
import time
from contextlib import suppress
from pathlib import Path
from unittest.mock import patch

import pytest

importlib.import_module("anki.collection")
aqt = importlib.import_module("aqt")

PROJECT_ROOT = Path(__file__).parent.parent
ADDON_DIR = PROJECT_ROOT / "addon" / "anki_time_per_card"
ADDON_NUMERIC_ID = "1000000003"


def import_runtime_addon_module(module_suffix: str = ""):
    """Import the add-on as Anki loads it, using the numeric package id."""

    if module_suffix and not module_suffix.startswith("."):
        raise ValueError("module_suffix must be empty or start with '.'")
    return importlib.import_module(f"{ADDON_NUMERIC_ID}{module_suffix}")


def _process_events_until(predicate, timeout_s: float, message: str) -> None:
    from PyQt6.QtWidgets import QApplication

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        QApplication.processEvents()
        if predicate():
            return
        time.sleep(0.02)
    pytest.fail(message)


def _start_anki_runtime() -> None:
    from aqt.profiles import ProfileManager

    def _skip_lang_dialog(self, idx: int) -> None:
        del idx
        self.meta["defaultLang"] = "en_US"

    startup_argv = ["anki"]
    with (
        patch.object(ProfileManager, "setDefaultLang", _skip_lang_dialog),
        patch.object(aqt.AnkiApp, "secondInstance", lambda self: False),
        patch.object(sys, "argv", startup_argv.copy()),
    ):
        aqt._run(exec=False, argv=startup_argv)


@pytest.fixture(scope="session")
def anki_base(tmp_path_factory):
    base = tmp_path_factory.mktemp("anki_base")
    addons = base / "addons21"
    addons.mkdir()
    addon_dir = addons / ADDON_NUMERIC_ID
    shutil.copytree(
        ADDON_DIR.resolve(),
        addon_dir,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.log", "meta.json"),
    )
    os.environ["ANKI_BASE"] = str(base)
    yield base


@pytest.fixture(scope="session")
def qapp(anki_base):
    from PyQt6.QtCore import QEvent
    from PyQt6.QtWidgets import QApplication

    del anki_base
    original_event = aqt.AnkiApp.event

    def _event_without_file_open(self, event):
        if event is not None and event.type() == QEvent.Type.FileOpen:
            return True
        return original_event(self, event)

    with patch.object(aqt.AnkiApp, "event", _event_without_file_open):
        app = QApplication.instance()
        if app is None or not isinstance(app, aqt.AnkiApp):
            _start_anki_runtime()
            app = QApplication.instance()
        if app is None or not isinstance(app, aqt.AnkiApp):
            raise RuntimeError(
                "E2E tests require a real aqt.AnkiApp; "
                f"got {type(app).__name__ if app is not None else 'None'} instead."
            )
        yield app


@pytest.fixture(scope="session")
def anki_mw(qapp):
    del qapp
    _process_events_until(
        lambda: aqt.mw is not None and aqt.mw.col is not None,
        timeout_s=10.0,
        message="Anki did not finish initializing within 10s",
    )
    aqt.mw.hide()
    import_runtime_addon_module("")
    aqt.mw.addonManager.writeConfig(ADDON_NUMERIC_ID, {})
    yield aqt.mw


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_sessionfinish(session, exitstatus):
    """Force-exit after pytest prints the summary to avoid Qt WebEngine teardown hangs."""

    del session
    yield

    for stream in (sys.stdout, sys.stderr):
        flush = getattr(stream, "flush", None)
        if callable(flush):
            flush()

    try:
        result = subprocess.run(["pgrep", "-P", str(os.getpid())], capture_output=True, text=True, timeout=2)
        for pid_str in result.stdout.split():
            with suppress(ValueError, OSError):
                os.kill(int(pid_str), signal.SIGKILL)
    except Exception:
        pass

    os._exit(int(exitstatus))
