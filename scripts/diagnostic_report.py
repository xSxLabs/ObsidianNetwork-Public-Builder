#!/usr/bin/env python3
"""Collect measured runtime markers without interpreting source checks as tests.

Input must be runtime/Gradle logs, not Python/Java source dumps. Only complete
standalone marker lines (optionally prefixed by actual log timestamps) count.
Malformed or missing required measurements make the command fail after writing
the diagnostic, so a nonempty list of empty dictionaries cannot pass CI.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class Schema:
    required: tuple[str, ...]
    positional: bool = False
    pass_literal: bool = False
    literal_fields: tuple[tuple[str, str], ...] = ()


SCHEMAS = {
    "FULL_EQUIPMENT_CELL_PHASE_NS": Schema(("insert", "remove", "decode", "max_insert", "max_remove", "max_decode", "cycles", "types")),
    "FULL_EQUIPMENT_CELL_REINSERT_NS": Schema(("ns", "cycles", "count", "types"), True),
    "EQUIPMENT_ATTACH_PRE_REGISTER_NS": Schema(("ns", "snapshot_ns", "types"), True),
    "EQUIPMENT_CELL_SLOW_SAVE_NS": Schema(("ns", "slot", "types"), True),
    "EQUIPMENT_REGISTRY_LOOKUP_NS": Schema(("legacy_median", "optimized_median", "legacy_p95", "optimized_p95", "legacy_max", "optimized_max", "samples", "types", "warmup", "checked_ids")),
    "EQUIPMENT_MENU_CYCLE_NS": Schema(("median", "p95", "max", "total", "cycles", "warmup", "count", "types")),
    "EQUIPMENT_MENU_CONSERVATION_V1": Schema(("offline_cycles", "attached_cycles", "count", "types", "menu_closes"), pass_literal=True),
    "EQUIPMENT_CANONICAL_FIXTURE_V1": Schema(("count", "types", "descriptor_bytes", "serialized_bytes")),
    "REAL_STORAGE_BULK_DEPOSIT_NS": Schema(("ns", "cycles", "operations", "amount_per_cycle"), True),
    "TERMINAL_CRAFT_MENU_NS": Schema(("samples", "operations", "median_ns", "p95_ns", "max_ns", "total_ns")),
    "TERMINAL_BULK_MENU_NS": Schema(("samples", "operations", "median_ns", "p95_ns", "max_ns", "total_ns")),
    "TERMINAL_RECIPE_MATCH_REBUILD_NS": Schema(("samples", "operations", "median_ns", "p95_ns", "max_ns", "total_ns")),
    "TERMINAL_RECIPE_MATCH_REUSE_NS": Schema(("samples", "operations", "median_ns", "p95_ns", "max_ns", "total_ns")),
    "TERMINAL_CRAFT_TICK_WORK_NS": Schema(("samples", "operations", "median_ns", "p95_ns", "max_ns", "total_ns")),
    "TERMINAL_BULK_TICK_WORK_NS": Schema(("samples", "operations", "median_ns", "p95_ns", "max_ns", "total_ns")),
    "TERMINAL_CRAFT_CONSERVATION": Schema(("crafted_planks",), pass_literal=True, literal_fields=(("full_inventory", "true"), ("partial_inventory", "true"), ("quick_move", "true"), ("manual_click", "true"))),
    "TERMINAL_BULK_CONSERVATION": Schema(("cycles", "items_per_cycle", "types", "menu_insertions", "payload_insertions", "payload_extractions"), pass_literal=True),
    "TERMINAL_MENU_STRESS_V1": Schema((), pass_literal=True, literal_fields=(("server_menu", "true"), ("rendered_client_gui", "false"), ("partial_and_full_storage", "true"))),
    "TERMINAL_RECIPE_CACHE_EQUIVALENCE": Schema(("variants",), pass_literal=True, literal_fields=(("exact_counts", "true"), ("exact_components", "true"), ("dynamic_candidates_live", "true"))),
    "REAL_50_DRIVE_BENCHMARK_V1": Schema(("cells", "drives", "trials", "operations_per_trial", "median_ns", "p90_ns", "min_ns", "total_operations")),
    "REAL_50_DRIVE_SUSTAINED_SUMMARY": Schema(("ticks", "operations", "p95_storage_work_ns", "worst_storage_work_ns")),
    "BENCHMARK_WINDOW_START": Schema(("wall_time_ms",)),
    "BENCHMARK_WINDOW_END": Schema(("wall_time_ms",)),
}
DEFAULT_REQUIRED = ("FULL_EQUIPMENT_CELL_PHASE_NS", "FULL_EQUIPMENT_CELL_REINSERT_NS", "REAL_STORAGE_BULK_DEPOSIT_NS")
CI_TIMESTAMP = re.compile(r"^(?P<time>\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z)\s+")
LOGGER = re.compile(r"^\[(?P<time>\d\d:\d\d:\d\d)\] \[(?P<thread>[^\]\r\n]+)/(?:INFO|WARN|ERROR|DEBUG)\](?: \[[^\]\r\n]+\])?:?\s+")
FIELD = re.compile(r"(?P<key>[A-Za-z][A-Za-z0-9_]*)=(?P<value>[A-Za-z0-9_.:/+\-]+)\Z")
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def runtime_line(raw: str) -> tuple[str, dict]:
    text = ANSI.sub("", raw).strip()
    provenance = {}
    ci = CI_TIMESTAMP.match(text)
    if ci:
        provenance["ci_emission_timestamp"] = ci.group("time")
        text = text[ci.end():]
    logger = LOGGER.match(text)
    if logger:
        provenance["server_clock"] = logger.group("time")
        provenance["thread"] = logger.group("thread")
        text = text[logger.end():]
    return text, provenance


def parse_measurement(body: str, schema: Schema) -> dict:
    tokens = body.split()
    values = {}
    if schema.pass_literal:
        if not tokens or tokens.pop(0) != "PASS":
            raise ValueError("mandatory PASS literal absent")
        values["status"] = "PASS"
    if schema.positional and tokens and tokens[0].isdigit():
        values["ns"] = int(tokens.pop(0))
    for token in tokens:
        field = FIELD.fullmatch(token)
        if not field:
            raise ValueError(f"invalid measurement token {token!r}")
        key, value = field.group("key", "value")
        if key in values:
            raise ValueError(f"duplicate measurement field {key}")
        values[key] = int(value) if value.isdigit() else value
    missing = [field for field in schema.required if type(values.get(field)) is not int]
    if missing:
        raise ValueError("missing/invalid mandatory numeric fields: " + ", ".join(missing))
    for key, expected in schema.literal_fields:
        if values.get(key) != expected:
            raise ValueError(f"mandatory field {key} must be {expected}")
    if any(type(values[field]) is int and values[field] < 0 for field in values):
        raise ValueError("negative measurement")
    for count in ("cycles", "count", "types", "samples", "operations", "ticks", "trials", "cells", "drives"):
        if count in schema.required and values[count] <= 0:
            raise ValueError(f"{count} must be positive")
    for median, percentile, maximum in (("median", "p95", "max"), ("median_ns", "p95_ns", "max_ns"), ("legacy_median", "legacy_p95", "legacy_max"), ("optimized_median", "optimized_p95", "optimized_max")):
        if all(key in values for key in (median, percentile, maximum)):
            if not all(type(values[key]) is int for key in (median, percentile, maximum)) or not values[median] <= values[percentile] <= values[maximum]:
                raise ValueError(f"invalid percentile ordering for {median}")
    return values


def parse_logs(paths: list[Path]) -> dict:
    measurements = {marker: [] for marker in SCHEMAS}
    errors, warnings, results, windows, environments = [], [], [], [], []
    for path in paths:
        for line_number, raw in enumerate(path.read_text(errors="replace").splitlines(), 1):
            body, metadata = runtime_line(raw)
            provenance = {"file": str(path), "line": line_number, **metadata}
            parts = body.split(None, 1)
            marker = parts[0] if parts else ""
            payload = parts[1] if len(parts) > 1 else ""
            if marker in SCHEMAS:
                try:
                    values = parse_measurement(payload, SCHEMAS[marker])
                    entry = {"values": values, "provenance": provenance}
                    if marker.startswith("BENCHMARK_WINDOW_"):
                        if not isinstance(values.get("workload"), str):
                            raise ValueError("benchmark window requires workload string")
                        windows.append({"event": marker, **entry})
                    else:
                        measurements[marker].append(entry)
                except ValueError as exc:
                    errors.append({"marker": marker, "error": str(exc), "provenance": provenance})
            # Only server logger output can assert GameTest execution or tick warnings.
            if "server_clock" not in metadata or metadata.get("thread") != "Server thread":
                continue
            passed = re.fullmatch(r"All (\d+) required tests passed(?:\s*:\))?", body)
            failed = re.search(r"\b(\d+) required tests failed\b", body)
            if passed:
                results.append({"passed": int(passed.group(1)), "failed": 0, "provenance": provenance})
            if failed:
                results.append({"passed": 0, "failed": int(failed.group(1)), "provenance": provenance})
            environment = re.fullmatch(r"Running test environment '([^']+)' batch (\d+) \((\d+) tests\)\.\.\.", body)
            if environment:
                environments.append({"environment": environment.group(1), "batch": int(environment.group(2)), "tests": int(environment.group(3)), "provenance": provenance})
            warning = re.fullmatch(r"Can't keep up!.*", body)
            if warning:
                behind = re.search(r"Running (\d+)ms or (\d+) ticks behind", body)
                warnings.append({"message": body, "behind_ms": int(behind.group(1)) if behind else None, "provenance": provenance})
    return {"measurements": measurements, "parse_errors": errors, "server_tick_warnings": warnings, "window_events": windows, "gametest_results": results, "gametest_environments": environments}


def attribute_warnings(parsed: dict, timezone: str) -> list[dict]:
    """Report timestamp overlap, never infer causality from log line ordering.

    Logger clocks have one-second resolution. CI timestamps may be buffered,
    therefore they are retained as provenance but never used for attribution.
    """
    active, complete = {}, []
    for entry in parsed["window_events"]:
        values = entry["values"]
        key = (entry["provenance"]["file"], values["workload"])
        if entry["event"] == "BENCHMARK_WINDOW_START":
            if key in active:
                parsed["parse_errors"].append({"error": "overlapping benchmark windows", "provenance": entry["provenance"]})
            active[key] = entry
        else:
            start = active.pop(key, None)
            if start is None or start["values"]["wall_time_ms"] > values["wall_time_ms"]:
                parsed["parse_errors"].append({"error": "unmatched/reversed benchmark window", "provenance": entry["provenance"]})
                continue
            complete.append({"workload": values["workload"], "start_wall_time_ms": start["values"]["wall_time_ms"], "end_wall_time_ms": values["wall_time_ms"], "start_provenance": start["provenance"], "end_provenance": entry["provenance"]})
    for start in active.values():
        parsed["parse_errors"].append({"error": "benchmark window has no end", "provenance": start["provenance"]})
    zone = ZoneInfo(timezone)
    for warning in parsed["server_tick_warnings"]:
        overlaps = []
        for window in complete:
            if warning["provenance"]["file"] != window["start_provenance"]["file"]:
                continue
            day = datetime.fromtimestamp(window["start_wall_time_ms"] / 1000, zone).date()
            for offset in (-1, 0, 1):
                stamp = datetime.fromisoformat(str(day + timedelta(days=offset)) + "T" + warning["provenance"]["server_clock"]).replace(tzinfo=zone).timestamp() * 1000
                backlog_start = stamp - (warning["behind_ms"] or 0)
                if backlog_start <= window["end_wall_time_ms"] and stamp + 999 >= window["start_wall_time_ms"]:
                    overlaps.append(window["workload"])
                    break
        warning.update({"temporal_overlap_workloads": overlaps, "causal_attribution_proven": False, "attribution": "runtime_clock_overlap_only" if overlaps else "no_proven_timestamp_overlap", "clock_resolution_ms": 1000})
    return complete


def read_restart(path: Path | None) -> dict:
    if path is None:
        return {"verified": False, "reason": "No process-restart report supplied"}
    data = json.loads(path.read_text())
    errors = []
    if data.get("schema_version") != 1 or data.get("status") != "passed":
        errors.append("restart report has no successful supported schema")
    for key in ("distinct_server_jvms", "same_saved_world"):
        if data.get(key) is not True:
            errors.append(f"{key} is not true")
    phases = data.get("phases", {})
    for name in ("before", "after"):
        phase = phases.get(name, {})
        for key in ("success", "normal_shutdown_verified"):
            if phase.get(key) is not True:
                errors.append(f"{name}.{key} is not true")
        if phase.get("phase") != name or phase.get("session") != data.get("session") or not data.get("session"):
            errors.append(f"{name} session/phase mismatch")
        if phase.get("gradle_exit_code") != 0 or type(phase.get("gradle_exit_code")) is not int:
            errors.append(f"{name} server command failed")
        if type(phase.get("server_jvm_pid")) is not int or phase.get("server_jvm_pid", 0) <= 0 or not phase.get("server_jvm_started"):
            errors.append(f"{name} lacks real JVM identity")
        expected_topologies = ["three_bundles", "three_standalone", "bundle_standalone_bundle", "standalone_bundle_standalone"]
        if phase.get("topologies") != expected_topologies:
            errors.append(f"{name} does not cover all four conduit topologies")
        targets = {"minecraft:cobblestone": 37, "minecraft:diamond": 5, "minecraft:emerald": 3}
        if name == "after":
            targets.update({"minecraft:gold_ingot": 7, "minecraft:redstone": 9})
        for lane in range(4):
            row = phase.get("endpoint_diagnostics", {}).get(f"lane_{lane}", {})
            if row.get("source") != {} or row.get("target") != targets:
                errors.append(f"{name}.lane_{lane} initial transfer count mismatch")
            for key in ("source_chunk_loaded", "target_chunk_loaded", "source_item_capability_available", "target_item_capability_available"):
                if row.get(key) is not True:
                    errors.append(f"{name}.lane_{lane}.{key} is not true")
            if lane != 1 and any(type(row.get(key)) is not int or row[key] <= 0 for key in ("nodes", "extract_endpoints", "insert_endpoints")):
                errors.append(f"{name}.lane_{lane} lacks connected bundle network endpoints")
    before, after = phases.get("before", {}), phases.get("after", {})
    if before.get("server_jvm_pid") == after.get("server_jvm_pid") and before.get("server_jvm_started") == after.get("server_jvm_started"):
        errors.append("both phases have the same JVM identity")
    for key in ("configuration_preserved", "item_conservation"):
        if after.get(key) is not True:
            errors.append(f"after.{key} is not true")
    if type(after.get("disconnect_ticks")) is not int or after.get("disconnect_ticks", 0) < 60 or type(after.get("reconnect_ticks")) is not int or after.get("reconnect_ticks", -1) < 0:
        errors.append("after phase lacks disconnect/reconnect evidence")
    for key in ("world_after_stop_sha256", "world_after_restart_sha256"):
        hashes = data.get(key)
        if not isinstance(hashes, dict) or "level.dat" not in hashes or not any(name.startswith("region/") and name.endswith(".mca") for name in hashes):
            errors.append(f"{key} lacks persisted level.dat/region evidence")
        elif not all(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) for value in hashes.values()):
            errors.append(f"{key} has invalid hashes")
    return {"verified": not errors, "errors": errors, "provenance": {"file": str(path), "sha256": digest(path)}, "evidence": data}


def read_server_ticks(path: Path | None, required_workloads: list[str]) -> dict:
    if path is None:
        return {"verified": False, "reason": "No server tick event report supplied", "errors": ["Server tick report required"] if required_workloads else []}
    data = json.loads(path.read_text())
    errors = []
    if data.get("schema_version") != 1 or type(data.get("server_jvm_pid")) is not int or data.get("server_jvm_pid", 0) <= 0:
        errors.append("Tick report lacks supported schema/server JVM identity")
    if data.get("tick_budget_ns") != 50_000_000:
        errors.append("Unexpected tick budget")
    samples = data.get("samples")
    valid_samples = isinstance(samples, list) and bool(samples)
    if valid_samples:
        for index, sample in enumerate(samples):
            if not isinstance(sample, dict) or type(sample.get("sequence")) is not int or sample.get("sequence") != index or any(type(sample.get(key)) is not int or sample[key] <= 0 for key in ("wall_time_ms", "duration_ns")) or not isinstance(sample.get("workloads"), list) or any(not isinstance(value, str) or not value for value in sample.get("workloads", [])):
                valid_samples = False
                break
    if not valid_samples:
        errors.append("Missing/malformed actual server tick event samples")
    else:
        names = {"all_server_ticks", *required_workloads}
        names.update(value for sample in samples for value in sample["workloads"])
        reported = data.get("workloads", {})
        if not isinstance(reported, dict):
            reported = {}
            errors.append("Tick workload summaries missing")
        for name in sorted(names):
            values = sorted(sample["duration_ns"] for sample in samples if name == "all_server_ticks" or name in sample["workloads"])
            if not values:
                errors.append(f"No server tick samples for required workload {name}")
                continue
            count = len(values)
            expected = {"ticks": count, "median_ns": values[(count * 50 + 99) // 100 - 1], "p95_ns": values[(count * 95 + 99) // 100 - 1], "max_ns": values[-1], "total_ns": sum(values), "over_budget_ticks": sum(value > 50_000_000 for value in values)}
            if reported.get(name) != expected:
                errors.append(f"Tick summary does not match raw samples for {name}")
    return {"verified": not errors, "errors": errors, "scope": "ServerTickEvent.Pre to Post event interval, excluding scheduling and tick-loop work outside these events; not complete server MSPT.", "provenance": {"file": str(path), "sha256": digest(path)}, "evidence": data}


HOTPATHS = {
    "network_index": ("core/NetworkIndex.java", ("capture", "invalidate", "revision")),
    "storage_cell_store": ("core/StorageCellStore.java", ("amount", "extract", "free", "insertExact")),
    "storage_network": ("core/StorageNetwork.java", ("capture", "extract", "insertExact", "invalidate", "previewInsertExact", "revision")),
    "terminal_menu": ("menu/StorageTerminalMenu.java", ("broadcastChanges", "matchingCraftRecipes", "quickMoveStack", "rebuildRecipeChoice")),
}


def hotpath_inventory(root: Path) -> dict:
    result = {"schema_version": 2, "kind": "source_audit_not_runtime_profile", "contains_runtime_measurements": False, "note": "Token counts include calls and declarations; they are not profiler timings."}
    for name, (relative, tokens) in HOTPATHS.items():
        path = root / relative
        source = path.read_text() if path.exists() else ""
        result[name] = {"path": relative, "exists": path.exists(), "bytes": path.stat().st_size if path.exists() else 0, "sha256": digest(path) if path.exists() else None, "calls_and_declarations": {token: len(re.findall(r"\b" + re.escape(token) + r"\s*\(", source)) for token in tokens}}
    return result


def make_report(args: argparse.Namespace) -> dict:
    parsed = parse_logs(args.log)
    windows = attribute_warnings(parsed, args.server_timezone)
    required = args.require_marker if args.require_marker is not None else DEFAULT_REQUIRED
    errors = parsed["parse_errors"]
    for marker in required:
        if not parsed["measurements"].get(marker):
            errors.append({"error": f"Required runtime measurement missing: {marker}"})
    execution_passed = bool(parsed["gametest_results"]) and all(r["failed"] == 0 and r["passed"] > 0 for r in parsed["gametest_results"])
    if args.require_gametest_pass and not execution_passed:
        errors.append({"error": "No successful actual GameTestServer completion, or required tests failed"})
    restart = read_restart(args.restart_report)
    if args.restart_report and not restart["verified"]:
        errors.append({"error": "Process restart evidence invalid", "details": restart["errors"]})
    ticks = read_server_ticks(getattr(args, "server_ticks", None), getattr(args, "require_tick_workload", None) or [])
    if ticks["errors"]:
        errors.append({"error": "Server tick evidence invalid", "details": ticks["errors"]})
    measurements = parsed["measurements"]
    equipment_menu_workloads = {entry["values"].get("workload") for entry in measurements["EQUIPMENT_MENU_CYCLE_NS"]}
    coverage = {
        "equipment_insert_remove_runtime": bool(measurements["FULL_EQUIPMENT_CELL_REINSERT_NS"]) and execution_passed,
        "equipment_server_menu_cycle": {"offline", "attached"}.issubset(equipment_menu_workloads) and bool(measurements["EQUIPMENT_MENU_CONSERVATION_V1"]) and execution_passed,
        "equipment_canonical_descriptors": bool(measurements["EQUIPMENT_CANONICAL_FIXTURE_V1"]) and execution_passed,
        "crafting_server_menu_stress": bool(measurements["TERMINAL_CRAFT_MENU_NS"] and measurements["TERMINAL_CRAFT_CONSERVATION"] and measurements["TERMINAL_MENU_STRESS_V1"]) and execution_passed,
        "bulk_server_menu_stress": bool(measurements["TERMINAL_BULK_MENU_NS"] and measurements["TERMINAL_BULK_CONSERVATION"] and measurements["TERMINAL_MENU_STRESS_V1"]) and execution_passed,
        "item_dedicated_process_restart": restart["verified"],
        "server_tick_event_work": ticks["verified"],
        "equipment_rendered_client_gui": False,
        "crafting_rendered_client_gui": False,
        "bulk_rendered_client_gui": False,
        "complete_server_mspt": False,
    }
    report = {
        "schema_version": 2,
        "status": "failed" if errors else "passed",
        "status_scope": "diagnostic extraction and required evidence only; not release readiness",
        "inputs": [{"file": str(path), "sha256": digest(path)} for path in args.log],
        "required_markers": list(required),
        "measurements": {key: value for key, value in measurements.items() if value},
        "validation_errors": errors,
        "gametests": {"successful_completion": execution_passed, "results": parsed["gametest_results"], "environments": parsed["gametest_environments"]},
        "item_conduit_process_restart": restart,
        "server_tick_events": ticks,
        "benchmark_windows": windows,
        "server_tick_warnings": parsed["server_tick_warnings"],
        "tick_warning_attribution": "Only server-clock/backlog intervals overlapping explicit wall-clock benchmark windows are associated; no causal claim. Buffered CI emission timestamps and line ordering are never used.",
        "server_timezone": args.server_timezone,
        "coverage": coverage,
        "missing_release_gates": [key for key, covered in coverage.items() if not covered],
        "measurement_limits": ["Server menu operations do not exercise rendered client screens or network latency.", "Per-operation tick work timings do not measure complete server MSPT.", "CI timings vary with warmup, JVM/JIT, garbage collection and runner load; compare identical workloads within the same JVM where available.", "Canonical Minecraft equipment descriptors differ from the historical synthetic descriptor benchmark. Do not derive a direct speedup ratio against Build 194; use matching workloads or the paired same-JVM reference measurements."],
    }
    if getattr(args, "source_root", None):
        report["source_audit"] = hotpath_inventory(args.source_root)
    if args.provenance_report:
        provenance = json.loads(args.provenance_report.read_text())
        report["packaged_runtime_provenance"] = {"file": str(args.provenance_report), "sha256": digest(args.provenance_report), "evidence": provenance}
        if provenance.get("kind") != "verified_packaged_runtime" or provenance.get("status") != "passed":
            errors.append({"error": "Packaged runtime provenance is not verified"})
            report["status"] = "failed"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, action="append", required=True, help="Runtime log; may be repeated")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--require-marker", choices=tuple(SCHEMAS), action="append", help="Override default mandatory markers; repeat for each")
    parser.add_argument("--require-gametest-pass", action="store_true")
    parser.add_argument("--restart-report", type=Path)
    parser.add_argument("--provenance-report", type=Path)
    parser.add_argument("--server-ticks", type=Path)
    parser.add_argument("--require-tick-workload", action="append", help="Require matching raw server tick samples and summary for this workload; repeatable")
    parser.add_argument("--server-timezone", default="UTC", help="Timezone of server HH:mm:ss logger clocks")
    parser.add_argument("--source-root", type=Path, help="Final dev/obsidiannetwork Java source directory for static inventory")
    parser.add_argument("--perf-output", type=Path, help="Write static source inventory here; requires --source-root")
    args = parser.parse_args()
    try:
        report = make_report(args)
        if args.perf_output:
            if not args.source_root:
                raise ValueError("--perf-output requires --source-root")
            args.perf_output.parent.mkdir(parents=True, exist_ok=True)
            args.perf_output.write_text(json.dumps(hotpath_inventory(args.source_root), indent=2, sort_keys=True) + "\n")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, f"DIAGNOSTIC_REPORT FAIL: {exc}\n")
    print(f"DIAGNOSTIC_REPORT {report['status'].upper()} {args.output}")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
