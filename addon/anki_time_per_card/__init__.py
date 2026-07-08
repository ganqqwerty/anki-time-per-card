"""Anki Time Per Card add-on bootstrap.

The package is imported by Anki from a numeric add-on directory during local
development. Keep this file small and tolerant of non-Anki imports.
"""

from __future__ import annotations

import sys

from ._version import __version__


def _bootstrap() -> None:
    try:
        import aqt  # noqa: F401
    except Exception:
        return

    try:
        from .menu import register_hooks

        register_hooks()
    except Exception as exc:  # pragma: no cover - defensive Anki import boundary
        print(f"Anki Time Per Card failed to initialize: {exc}", file=sys.stderr)


_bootstrap()

__all__ = ["__version__"]
