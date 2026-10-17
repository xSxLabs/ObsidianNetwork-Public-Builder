#!/usr/bin/env python3
"""Fail-closed parser for actual Minecraft CI GameTest benchmark log records.

Old workflow accidentally used a regex matching a literal "\d", silently
turning every captured timing into {}. Never accept empty marker records.
"""
import re

PAIR = re.compile(r"(?<![A-Za-z0-9_])([a-z][a-z0-9_]*)=(\d+)\b")


def numbers_in(source_log: str, marker: str):
    if not marker or not isinstance(source_log, str):
        raise ValueError("A nonempty marker and log text are required")
    rows = []
    for line in source_log.splitlines():
        if marker not in line or "System.out.println" in line:
            continue
        # Ignore echoed commands in workflow setup; only actual runtime
        # markers should be parsed.
        if "\x1b[" in line or "grep -Fq" in line:
            continue
        values = {key: int(raw) for key, raw in PAIR.findall(line)}
        # Legacy REAL_STORAGE_BULK_DEPOSIT_NS and equipment reinsert markers
        # emitted an unnamed nanosecond duration immediately after the label.
        unnamed = re.search(r"(?<!\w)" + re.escape(marker) + r"\s+(\d+)\b", line)
        if unnamed:
            values["elapsed_ns"] = int(unnamed.group(1))
        if not values:
            raise ValueError(f"Empty parsed metrics for {marker}: {line[:180]}")
        rows.append(values)
    return rows


def require_metrics(rows, *fields):
    if not rows:
        raise ValueError("Missing GameTest benchmark rows")
    for i, row in enumerate(rows):
        if not isinstance(row, dict) or any(type(row.get(field)) is not int for field in fields):
            raise ValueError(f"Benchmark row {i} missing numeric metrics: {fields}, found={row}")
    return rows
