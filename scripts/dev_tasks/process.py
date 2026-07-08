"""Process execution helpers for the development task runner."""

from __future__ import annotations

import os
import queue
import shlex
import subprocess
import sys
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_VERBOSE = False
_IDLE_TIMEOUT_S: float | None = None
_QUIET_TEST_OUTPUT: ContextVar[int] = ContextVar("_QUIET_TEST_OUTPUT", default=0)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def set_verbose(verbose: bool) -> None:
    global _VERBOSE
    _VERBOSE = verbose


def set_idle_timeout(timeout_s: float | None) -> None:
    global _IDLE_TIMEOUT_S
    _IDLE_TIMEOUT_S = timeout_s


def is_verbose() -> bool:
    return _VERBOSE


@contextmanager
def quiet_test_output() -> Iterator[None]:
    token = _QUIET_TEST_OUTPUT.set(_QUIET_TEST_OUTPUT.get() + 1)
    try:
        yield
    finally:
        _QUIET_TEST_OUTPUT.reset(token)


def is_quiet_test_output() -> bool:
    return _QUIET_TEST_OUTPUT.get() > 0


def _read_seconds_env(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return value if value > 0 else 0.0


def _format_duration(seconds: float) -> str:
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, rest = divmod(seconds, 60)
    return f"{int(minutes)}m {rest:.0f}s"


def _reader_thread(stream, output_queue: queue.Queue[str | None]) -> None:
    try:
        for line in iter(stream.readline, ""):
            output_queue.put(line)
    finally:
        output_queue.put(None)


def _print_buffered_failure(output: list[str], *, label: str | None) -> None:
    if not output:
        return
    if label:
        print(f"[dev] output from failed {label}:")
    sys.stdout.write("".join(output))
    if not output[-1].endswith("\n"):
        print()


def _run(
    cmd: list[str],
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
    *,
    label: str | None = None,
    idle_warning_s: float | None = None,
    idle_timeout_s: float | None = None,
    show_output_on_failure: bool = False,
) -> int:
    quiet_mode = is_quiet_test_output() and not is_verbose()
    run_cwd = cwd or ROOT
    merged_env = {**os.environ, **env} if env else None
    rendered_cmd = shlex.join(str(part) for part in cmd)
    resolved_idle_warning = idle_warning_s
    if resolved_idle_warning is None:
        resolved_idle_warning = _read_seconds_env("DEV_IDLE_WARNING_SECS", 30.0)
    resolved_idle_timeout = idle_timeout_s
    if resolved_idle_timeout is None:
        resolved_idle_timeout = (
            _IDLE_TIMEOUT_S
            if _IDLE_TIMEOUT_S is not None
            else _read_seconds_env("DEV_IDLE_TIMEOUT_SECS", 300.0)
        )
    terminate_grace_s = _read_seconds_env("DEV_TERMINATE_GRACE_SECS", 5.0)

    if is_verbose():
        print(f"[dev] {label or rendered_cmd}")
        print(f"[dev] cwd: {run_cwd}")
    elif not quiet_mode:
        print(f"[dev] {label or rendered_cmd}")

    process = subprocess.Popen(
        [str(part) for part in cmd],
        cwd=run_cwd,
        env=merged_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    assert process.stdout is not None
    output_queue: queue.Queue[str | None] = queue.Queue()
    reader = threading.Thread(target=_reader_thread, args=(process.stdout, output_queue), daemon=True)
    reader.start()

    start = time.monotonic()
    last_output = start
    next_warning = start + resolved_idle_warning if resolved_idle_warning else float("inf")
    stream_closed = False
    timed_out = False
    buffered_output: list[str] = []

    while True:
        try:
            item = output_queue.get(timeout=0.1)
        except queue.Empty:
            item = "__NO_OUTPUT__"
        now = time.monotonic()

        if item is None:
            stream_closed = True
        elif item != "__NO_OUTPUT__":
            last_output = now
            if is_verbose():
                sys.stdout.write(item)
                sys.stdout.flush()
            elif quiet_mode or show_output_on_failure:
                buffered_output.append(item)

        if process.poll() is not None and stream_closed:
            break

        idle_for = now - last_output
        if resolved_idle_warning and now >= next_warning and process.poll() is None:
            if not quiet_mode:
                print(
                    f"[dev] waiting for output from {label or rendered_cmd} "
                    f"({_format_duration(idle_for)} idle)"
                )
            next_warning = now + resolved_idle_warning
        if resolved_idle_timeout and idle_for >= resolved_idle_timeout and process.poll() is None:
            timed_out = True
            process.terminate()
            try:
                process.wait(timeout=terminate_grace_s)
            except subprocess.TimeoutExpired:
                process.kill()
            break

    rc = process.wait()
    reader.join(timeout=1)
    elapsed = time.monotonic() - start
    if rc != 0 and buffered_output and not is_verbose():
        _print_buffered_failure(buffered_output, label=label if quiet_mode else None)
    status = "OK" if rc == 0 and not timed_out else f"FAIL {rc}"
    if timed_out:
        status = f"TIMEOUT {rc}"
    if not quiet_mode or rc != 0:
        print(f"[dev] {status} in {_format_duration(elapsed)}")
    return rc


run_process = _run


def _run_capture(
    cmd: list[str],
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
    *,
    label: str | None = None,
    show_output_on_failure: bool = False,
) -> tuple[int, str]:
    quiet_mode = is_quiet_test_output() and not is_verbose()
    run_cwd = cwd or ROOT
    merged_env = {**os.environ, **env} if env else None
    rendered_cmd = shlex.join(str(part) for part in cmd)
    if is_verbose():
        print(f"[dev] {label or rendered_cmd}")
        print(f"[dev] cwd: {run_cwd}")
    elif not quiet_mode:
        print(f"[dev] {label or rendered_cmd}")

    start = time.monotonic()
    result = subprocess.run(
        [str(part) for part in cmd],
        cwd=run_cwd,
        env=merged_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    output = result.stdout or ""
    if output and is_verbose():
        sys.stdout.write(output)
        sys.stdout.flush()
    if result.returncode != 0 and output and (quiet_mode or show_output_on_failure) and not is_verbose():
        _print_buffered_failure([output], label=label if quiet_mode else None)
    if not quiet_mode or result.returncode != 0:
        status = "OK" if result.returncode == 0 else f"FAIL {result.returncode}"
        print(f"[dev] {status} in {_format_duration(time.monotonic() - start)}")
    return result.returncode, output


run_capture = _run_capture
