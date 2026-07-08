"""Node.js and frontend tool discovery helpers."""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Sequence
from pathlib import Path, PosixPath

ROOT = Path(__file__).resolve().parents[2]
WEBVIEW_UI_DIR = ROOT / "webview_ui"


def _path_for_host(path_str: str) -> Path:
    if "/" in path_str and "\\" not in path_str:
        return PosixPath(path_str)
    return Path(path_str)


def _which_first(*names: str) -> str | None:
    for name in names:
        resolved = shutil.which(name)
        if resolved:
            return resolved
    return None


def _command_is_usable(command: Sequence[str]) -> bool:
    try:
        result = subprocess.run(list(command), capture_output=True, text=True, check=False, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def find_node_command() -> str | None:
    candidates: list[Path] = []
    if os.name == "nt":
        path_node = _which_first("node.exe", "node")
        if path_node:
            candidates.append(Path(path_node))
        candidates.extend(
            [
                Path(r"C:\Program Files\nodejs\node.exe"),
                Path(r"C:\Program Files (x86)\nodejs\node.exe"),
            ]
        )
    else:
        path_node = _which_first("node")
        if path_node:
            candidates.append(Path(path_node))

    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve() if candidate.exists() else candidate
        if resolved in seen or not resolved.is_file():
            continue
        seen.add(resolved)
        if _command_is_usable([str(resolved), "--version"]):
            return str(resolved)
    return None


def find_npm_install_command(node_command: str | None = None) -> list[str] | None:
    if os.name == "nt":
        npm_on_path = _which_first("npm.cmd", "npm")
        if npm_on_path and _command_is_usable([npm_on_path, "--version"]):
            return [npm_on_path]
    else:
        npm_on_path = _which_first("npm")
        if npm_on_path and _command_is_usable([npm_on_path, "--version"]):
            return [npm_on_path]

    node = node_command or find_node_command()
    if not node:
        return None

    node_path = _path_for_host(node)
    if os.name == "nt":
        npm_cmd = node_path.parent / "npm.cmd"
        if npm_cmd.is_file():
            return [str(npm_cmd)]
        npm_cli = node_path.parent / "node_modules" / "npm" / "bin" / "npm-cli.js"
        if npm_cli.is_file():
            return [node, str(npm_cli)]
        return None

    for candidate in [
        node_path.parent.parent / "lib" / "node_modules" / "npm" / "bin" / "npm-cli.js",
        node_path.parent / "../lib/node_modules/npm/bin/npm-cli.js",
    ]:
        resolved = candidate.resolve()
        if resolved.is_file():
            return [node, str(resolved)]
    return None


def frontend_npm_command(script: str, *, extra_args: Sequence[str] = ()) -> list[str] | None:
    npm = find_npm_install_command()
    if not npm:
        return None
    command = [*npm, "run", script]
    if extra_args:
        command.extend(["--", *extra_args])
    return command


def frontend_runner_status() -> tuple[str, str]:
    node = find_node_command()
    npm = find_npm_install_command(node)
    node_version = ""
    if node:
        try:
            node_version = subprocess.run(
                [node, "--version"],
                capture_output=True,
                text=True,
                check=False,
                timeout=15,
            ).stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            node_version = ""
    return node_version, " ".join(npm) if npm else "not found"
