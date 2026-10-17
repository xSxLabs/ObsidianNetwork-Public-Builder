#!/usr/bin/env python3
"""Inspect two CI diagnostic reports without making unsupported TPS claims.

Usage:
    python3 performance/compare-ci-metrics.py dist/diagnostic-report.json
    python3 performance/compare-ci-metrics.py older.json newer.json

Each report has pre-final-patch and post-final-patch GameTest samples. Runs
use separate JVMs and can have uncontrolled JIT/GC and startup effects. This
tool deliberately never classifies one run as a proven optimization.
"""
import argparse
import json
from pathlib import Path


def positive(record, key):
    if not isinstance(record, dict):
        return None
    n = record.get(key)
    return n if type(n) is int and n > 0 else None


def sample(report, field, phase, metric):
    data = report.get(field, {})
    records = data.get(phase, []) if isinstance(data, dict) else []
    if not isinstance(records, list):
        return None
    vals = [positive(v, metric) for v in records]
    return vals[-1] if vals and vals[-1] is not None else None


def display(label, before, after, unit="ns"):
    if before is None or after is None:
        print(f"{label}: comparison unavailable (missing/invalid {unit} measurements)")
        return
    if before <= 0:
        raise ValueError("Zero baseline cannot be used for comparison")
    factor = after / before
    print(f"{label}: before={before:,} {unit}, after={after:,} {unit}, "
          f"observed_ratio={factor:.3f}x (UNCONTROLLED, NOT a speedup claim)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", nargs="+", type=Path)
    args = parser.parse_args()
    if len(args.reports) > 2:
        parser.error("Pass one or two report files")
    for file in args.reports:
        report = json.loads(file.read_text(encoding="utf-8"))
        print(f"\n=== {file} ===")
        # The existing bulk log uses an *unnamed* nanosecond value. Older
        # JSON diagnostics retained cycles but omitted that elapsed value.
        # Do not invent it from unrelated fields or call cycles elapsed time.
        display("Real bulk storage / 100 cycles",
                sample(report, "bulk_storage", "baseline_before_final_patches", "elapsed_ns"),
                sample(report, "bulk_storage", "measurements", "elapsed_ns"))
        # Missing bulk timings remain explicitly unavailable until the
        # CI report schema captures the named duration.
        before = sample(report, "equipment_64k", "baseline_before_final_patches", "insert")
        after = sample(report, "equipment_64k", "phase_measurements", "insert")
        display("64k equipment insert phase", before, after)
        before = sample(report, "autocraft_idle_reservations", "baseline_pre_patch", "median_ns")
        after = sample(report, "autocraft_idle_reservations", "after_final_patches", "median_ns")
        display("Live 50-drive autocraft idle / 500 reflective calls", before, after)
        gates = report.get("missing_release_gates", [])
        if isinstance(gates, list):
            print("Unverified release gates:", "; ".join(map(str, gates)) or "(none listed)")
        restart = report.get("item_conduit_restart", {})
        print("Real ITEM process restart:",
              "VERIFIED" if isinstance(restart, dict) and restart.get("real_process_restart_test") is True
              else "NOT VERIFIED")
    print("\nThese observations are not randomized paired TPS/MSPT trials. "
          "Do not infer stable throughput or player GUI latency.")


if __name__ == "__main__":
    main()
