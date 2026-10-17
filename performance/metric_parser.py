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


def validated_sustained_tick_work(source_log: str):
    """Validate real 20-tick storage work, not whole-server MSPT or GC."""
    sample_marker = "REAL_50_DRIVE_SUSTAINED_TICK "
    summary_marker = "REAL_50_DRIVE_SUSTAINED_SUMMARY "
    samples = require_metrics(numbers_in(source_log, sample_marker),
                              "sample", "operations", "storage_work_ns", "tick_wall_ns")
    summaries = require_metrics(numbers_in(source_log, summary_marker),
                                "ticks", "operations", "p95_storage_work_ns", "worst_storage_work_ns")
    if len(samples) != 20 or len(summaries) != 1:
        raise ValueError("Expected exactly 20 consecutive sustained storage ticks and one summary")
    if [row["sample"] for row in samples] != list(range(1, 21)):
        raise ValueError("Sustained storage tick sample sequence is incomplete or out of order")
    if any(row["operations"] != 200 or row["storage_work_ns"] <= 0 or row["tick_wall_ns"] <= 0
           for row in samples):
        raise ValueError("Sustained tick work must contain 200 operations and positive timings")
    summary = summaries[0]
    sorted_work = sorted(row["storage_work_ns"] for row in samples)
    if (summary["ticks"] != 20 or summary["operations"] != 4000
            or summary["p95_storage_work_ns"] != sorted_work[18]
            or summary["worst_storage_work_ns"] != sorted_work[19]):
        raise ValueError("Sustained tick summary does not match real 20-tick samples")
    if (sum("wall_clock_not_MSPT=true" in line for line in source_log.splitlines()
            if sample_marker in line and "System.out.println" not in line) != 20
            or not any(summary_marker in line and "not_server_MSPT=true" in line
                       and "System.out.println" not in line for line in source_log.splitlines())):
        raise ValueError("Sustained tick records must not be represented as server MSPT")
    return {"samples": samples, "summary": summary,
            "scope": "20 on-tick storage-work durations; not whole-server MSPT, p99, or GC"}
