"""Shared dev runner types."""

from __future__ import annotations

from collections.abc import Callable

Command = Callable[[list[str]], int]
CommandRegistry = dict[str, tuple[Command, str]]
