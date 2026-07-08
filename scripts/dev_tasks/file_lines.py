"""Python file-length checks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

MAX_PYTHON_FILE_LINES = 450
IGNORED_PARTS = {
    ".git",
    ".codegraph",
    ".mypy_cache",
    ".ruff_cache",
    "__pycache__",
}


@dataclass(frozen=True)
class FileLengthViolation:
    path: Path
    line_count: int


@dataclass(frozen=True)
class FileLengthReport:
    violations: tuple[FileLengthViolation, ...]

    @property
    def exit_code(self) -> int:
        return 1 if self.violations else 0


def scan_python_file_lengths(root: Path) -> FileLengthReport:
    violations: list[FileLengthViolation] = []
    for path in sorted(root.rglob("*.py")):
        if any(part in IGNORED_PARTS for part in path.relative_to(root).parts):
            continue
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > MAX_PYTHON_FILE_LINES:
            violations.append(FileLengthViolation(path.relative_to(root), line_count))
    return FileLengthReport(tuple(violations))


def format_python_file_length_report(report: FileLengthReport) -> str:
    if not report.violations:
        return f"Python file length check OK: all files <= {MAX_PYTHON_FILE_LINES} lines"
    lines = [f"Python files over {MAX_PYTHON_FILE_LINES} lines:"]
    lines.extend(f"  {violation.path}: {violation.line_count}" for violation in report.violations)
    return "\n".join(lines)
