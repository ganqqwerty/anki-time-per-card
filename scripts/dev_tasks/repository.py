"""Repository structure checks."""

from __future__ import annotations

from pathlib import Path

from scripts.dev_tasks.file_lines import format_python_file_length_report, scan_python_file_lengths

ROOT = Path(__file__).resolve().parents[2]


def cmd_file_lines() -> int:
    report = scan_python_file_lengths(ROOT)
    print(format_python_file_length_report(report))
    return report.exit_code
