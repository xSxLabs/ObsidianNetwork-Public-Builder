import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/diagnostic_report.py"
SPEC = importlib.util.spec_from_file_location("diagnostic_report", SCRIPT)
diagnostic = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = diagnostic
SPEC.loader.exec_module(diagnostic)


class RuntimeMarkerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.log = Path(self.directory.name) / "runtime.log"

    def parse(self, text):
        self.log.write_text(text)
        return diagnostic.parse_logs([self.log])

    def test_unnamed_main_value_is_retained(self):
        parsed = self.parse("FULL_EQUIPMENT_CELL_REINSERT_NS 3082929162 cycles=25 count=64000 types=257\n")
        values = parsed["measurements"]["FULL_EQUIPMENT_CELL_REINSERT_NS"][0]["values"]
        self.assertEqual(values, dict(ns=3082929162, cycles=25, count=64000, types=257))
        self.assertFalse(parsed["parse_errors"])

    def test_ns_field_and_digit_keys(self):
        parsed = self.parse("2026-10-17T14:33:41.3064447Z [14:33:35] [Server thread/INFO] [test/probe]: TERMINAL_CRAFT_MENU_NS samples=25 operations=100 median_ns=10 p95_ns=15 max_ns=19 total_ns=250\nREAL_STORAGE_BULK_DEPOSIT_NS ns=7265548 cycles=100 operations=200 amount_per_cycle=4096\n")
        self.assertEqual(parsed["measurements"]["TERMINAL_CRAFT_MENU_NS"][0]["values"]["p95_ns"], 15)
        self.assertEqual(parsed["measurements"]["REAL_STORAGE_BULK_DEPOSIT_NS"][0]["values"]["ns"], 7265548)
        self.assertFalse(parsed["parse_errors"])

    def test_historical_optional_uppercase_key_is_retained(self):
        parsed = self.parse("REAL_50_DRIVE_SUSTAINED_SUMMARY ticks=20 operations=4000 p95_storage_work_ns=695511 worst_storage_work_ns=703516 not_server_MSPT=true\n")
        self.assertFalse(parsed["parse_errors"])
        self.assertEqual(parsed["measurements"]["REAL_50_DRIVE_SUSTAINED_SUMMARY"][0]["values"]["not_server_MSPT"], "true")

    def test_source_and_shell_commands_are_not_runtime_markers(self):
        parsed = self.parse('System.out.println("REAL_STORAGE_BULK_DEPOSIT_NS 4 cycles=100 operations=200 amount_per_cycle=4096");\n2026-10-17T14:33:41Z 955: REAL_STORAGE_BULK_DEPOSIT_NS 4 cycles=100 operations=200 amount_per_cycle=4096\n+ echo REAL_STORAGE_BULK_DEPOSIT_NS 4 cycles=100 operations=200 amount_per_cycle=4096\nprint("REAL_STORAGE_BULK_DEPOSIT_NS 4 cycles=100 operations=200 amount_per_cycle=4096")\n')
        self.assertFalse(any(parsed["measurements"].values()))

    def test_malformed_known_marker_fails_closed(self):
        for body in ("", "ns=nope cycles=100 operations=200 amount_per_cycle=4096", "4 cycles=100 operations=200", "4 cycles=100 operations=200 amount_per_cycle=4096 cycles=100", "4 cycles=100 operations=200 amount_per_cycle=4096;"):
            with self.subTest(body=body):
                parsed = self.parse("REAL_STORAGE_BULK_DEPOSIT_NS " + body)
                self.assertFalse(parsed["measurements"]["REAL_STORAGE_BULK_DEPOSIT_NS"])
                self.assertEqual(len(parsed["parse_errors"]), 1)

    def test_percentile_ordering_is_validated(self):
        parsed = self.parse("TERMINAL_CRAFT_MENU_NS samples=25 operations=100 median_ns=20 p95_ns=15 max_ns=19 total_ns=250")
        self.assertEqual(len(parsed["parse_errors"]), 1)

    def test_only_actual_server_completion_counts(self):
        parsed = self.parse('echo "All 8 required tests passed :)"\n2026-10-17T14:33:41Z [14:33:39] [Server thread/INFO] [minecraft/GameTestServer]: All 8 required tests passed :)\n')
        self.assertEqual(len(parsed["gametest_results"]), 1)
        self.assertEqual(parsed["gametest_results"][0]["passed"], 8)

    def test_warning_uses_explicit_runtime_clocks_not_buffered_ci_timestamp(self):
        start = int(datetime(2026, 10, 17, 10, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
        parsed = self.parse(f"2026-10-17T14:00:00Z BENCHMARK_WINDOW_START workload=equipment wall_time_ms={start}\n2026-10-17T14:00:00Z BENCHMARK_WINDOW_END workload=equipment wall_time_ms={start+1000}\n2026-10-17T14:00:00Z [10:00:02] [Server thread/WARN] [minecraft/MinecraftServer]: Can't keep up! Is the server overloaded? Running 1500ms or 30 ticks behind\n2026-10-17T14:00:00Z [13:59:59] [Server thread/WARN] [minecraft/MinecraftServer]: Can't keep up! Is the server overloaded? Running 1500ms or 30 ticks behind\n")
        diagnostic.attribute_warnings(parsed, "UTC")
        self.assertEqual(parsed["server_tick_warnings"][0]["temporal_overlap_workloads"], ["equipment"])
        self.assertEqual(parsed["server_tick_warnings"][1]["temporal_overlap_workloads"], [])
        self.assertFalse(parsed["server_tick_warnings"][0]["causal_attribution_proven"])

    def test_unmatched_windows_are_invalid(self):
        parsed = self.parse("BENCHMARK_WINDOW_END workload=equipment wall_time_ms=1")
        diagnostic.attribute_warnings(parsed, "UTC")
        self.assertEqual(len(parsed["parse_errors"]), 1)

    def test_missing_required_marker_cannot_pass(self):
        self.log.write_text("FULL_EQUIPMENT_CELL_REINSERT_NS 10 cycles=25 count=64000 types=257\n")
        args = argparse.Namespace(log=[self.log], server_timezone="UTC", require_marker=None, require_gametest_pass=False, restart_report=None, provenance_report=None)
        report = diagnostic.make_report(args)
        self.assertEqual(report["status"], "failed")
        self.assertFalse(report["coverage"]["equipment_rendered_client_gui"])

    def test_forged_success_without_jvm_phases_does_not_pass_restart(self):
        path = Path(self.directory.name) / "restart.json"
        path.write_text(json.dumps(dict(schema_version=1, status="passed", distinct_server_jvms=True, same_saved_world=True)))
        result = diagnostic.read_restart(path)
        self.assertFalse(result["verified"])

    def test_complete_restart_schema_passes_with_standalone_no_node_counts(self):
        path = Path(self.directory.name) / "restart.json"
        data = dict(schema_version=1, status="passed", session="test-session", distinct_server_jvms=True, same_saved_world=True, phases={})
        topologies = ["three_bundles", "three_standalone", "bundle_standalone_bundle", "standalone_bundle_standalone"]
        for index, name in enumerate(("before", "after")):
            targets = {"minecraft:cobblestone": 37, "minecraft:diamond": 5, "minecraft:emerald": 3}
            if name == "after":
                targets.update({"minecraft:gold_ingot": 7, "minecraft:redstone": 9})
            phase = dict(success=True, normal_shutdown_verified=True, phase=name, session="test-session", gradle_exit_code=0, server_jvm_pid=123+index, server_jvm_started=f"2026-10-17T10:0{index}:00Z", topologies=topologies, endpoint_diagnostics={})
            for lane in range(4):
                row = dict(source={}, target=targets, source_chunk_loaded=True, target_chunk_loaded=True, source_item_capability_available=True, target_item_capability_available=True)
                if lane != 1:
                    row.update(nodes=3, extract_endpoints=1, insert_endpoints=1)
                phase["endpoint_diagnostics"][f"lane_{lane}"] = row
            if name == "after":
                phase.update(configuration_preserved=True, item_conservation=True, disconnect_ticks=60, reconnect_ticks=5)
            data["phases"][name] = phase
        for name in ("world_after_stop_sha256", "world_after_restart_sha256"):
            data[name] = {"level.dat": "a"*64, "region/r.0.0.mca": "b"*64}
        path.write_text(json.dumps(data))
        self.assertTrue(diagnostic.read_restart(path)["verified"])
        data["phases"]["after"]["endpoint_diagnostics"]["lane_2"]["target"] = {"minecraft:diamond": 999}
        path.write_text(json.dumps(data))
        self.assertFalse(diagnostic.read_restart(path)["verified"])

    def tick_report(self):
        path = Path(self.directory.name) / "ticks.json"
        samples = [dict(sequence=i, wall_time_ms=1_000+i*50, duration_ns=value, workloads=["equipment_attached"]) for i, value in enumerate((10_000_000, 30_000_000, 60_000_000))]
        stats = dict(ticks=3, median_ns=30_000_000, p95_ns=60_000_000, max_ns=60_000_000, total_ns=100_000_000, over_budget_ticks=1)
        data = dict(schema_version=1, server_jvm_pid=123, tick_budget_ns=50_000_000, samples=samples, workloads=dict(equipment_attached=stats, all_server_ticks=stats))
        path.write_text(json.dumps(data))
        return path, data

    def test_tick_summary_is_recomputed_from_actual_samples(self):
        path, _ = self.tick_report()
        result = diagnostic.read_server_ticks(path, ["equipment_attached"])
        self.assertTrue(result["verified"])
        self.assertIn("not complete server MSPT", result["scope"])

    def test_tick_summary_disagreement_fails_closed(self):
        path, data = self.tick_report()
        data["workloads"]["equipment_attached"]["p95_ns"] = 1
        path.write_text(json.dumps(data))
        self.assertFalse(diagnostic.read_server_ticks(path, ["equipment_attached"])["verified"])

    def test_absent_required_tick_workload_fails(self):
        path, _ = self.tick_report()
        self.assertFalse(diagnostic.read_server_ticks(path, ["rapid_crafting"])["verified"])
        self.assertFalse(diagnostic.read_server_ticks(None, ["rapid_crafting"])["verified"])


if __name__ == "__main__":
    unittest.main()
