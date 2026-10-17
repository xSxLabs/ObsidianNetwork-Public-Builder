#!/usr/bin/env python3
"""Make empty GameTest performance-report rows a CI failure."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "performance"))
from metric_parser import numbers_in, require_metrics, validated_sustained_tick_work, validated_server_observations


class MetricParserTests(unittest.TestCase):
    def test_bulk_unnamed_elapsed_and_named_operation_counts(self):
        log = ("[20:00:39] [Server thread/INFO]: REAL_STORAGE_BULK_DEPOSIT_NS "
               "8135282 cycles=100 operations=200 amount_per_cycle=4096\n")
        actual = numbers_in(log, "REAL_STORAGE_BULK_DEPOSIT_NS")
        self.assertEqual(actual, [{"elapsed_ns": 8135282, "cycles": 100,
                                   "operations": 200, "amount_per_cycle": 4096}])
        require_metrics(actual, "elapsed_ns", "cycles", "operations")

    def test_autocraft_median_and_p90_numeric(self):
        log = ("REAL_AUTOCRAFT_IDLE_RESERVATION_V1 samples=9 calls_per_sample=500 "
               "inputs=12 median_ns=2044626 p90_ns=3743488 optimized_required=true\n")
        parsed = require_metrics(numbers_in(log, "REAL_AUTOCRAFT_IDLE_RESERVATION_V1"),
                                 "median_ns", "p90_ns", "samples", "calls_per_sample")
        self.assertEqual(parsed[0]["p90_ns"], 3743488)
        self.assertEqual(parsed[0]["calls_per_sample"], 500)

    def test_equipment_phase_values(self):
        parsed = numbers_in("FULL_EQUIPMENT_CELL_PHASE_NS insert=1407721396 remove=3779925 "
                            "decode=393920662 max_insert=98611803 cycles=25 types=257",
                            "FULL_EQUIPMENT_CELL_PHASE_NS")
        self.assertEqual(parsed[0]["insert"], 1407721396)
        self.assertEqual(parsed[0]["max_insert"], 98611803)
        require_metrics(parsed, "insert", "remove", "decode", "cycles")

    def test_echoed_source_is_not_measurement(self):
        self.assertEqual(numbers_in('System.out.println("REAL_STORAGE_BULK_DEPOSIT_NS "+clock);',
                                    "REAL_STORAGE_BULK_DEPOSIT_NS"), [])

    def test_invalid_empty_marker_not_accepted(self):
        with self.assertRaises(ValueError):
            numbers_in("REAL_STORAGE_BULK_DEPOSIT_NS no-metric-present",
                       "REAL_STORAGE_BULK_DEPOSIT_NS")
        with self.assertRaises(ValueError):
            require_metrics([{}], "elapsed_ns")
        with self.assertRaises(ValueError):
            require_metrics([], "median_ns")

    def test_log_runtime_prefix_and_multiple_phase_lines(self):
        log = ("2026-10-17T18:00:39Z REAL_STORAGE_BULK_DEPOSIT_NS 7659603 cycles=100\n"
               "2026-10-17T18:01:39Z REAL_STORAGE_BULK_DEPOSIT_NS 8135282 cycles=100")
        parsed = numbers_in(log, "REAL_STORAGE_BULK_DEPOSIT_NS")
        self.assertEqual([v["elapsed_ns"] for v in parsed], [7659603, 8135282])


    @staticmethod
    def _sustained_fixture():
        rows = [
            f"LOG REAL_50_DRIVE_SUSTAINED_TICK sample={i} operations=200 "
            f"storage_work_ns={1000 + i} tick_wall_ns={50000000 + i} "
            "wall_clock_not_MSPT=true"
            for i in range(1, 21)
        ]
        rows.append("REAL_50_DRIVE_SUSTAINED_SUMMARY ticks=20 operations=4000 "
                    "p95_storage_work_ns=1019 worst_storage_work_ns=1020 not_server_MSPT=true")
        return "\n".join(rows)

    def test_sustained_ticks_are_real_and_consistent(self):
        actual = validated_sustained_tick_work(self._sustained_fixture())
        self.assertEqual(len(actual["samples"]), 20)
        self.assertEqual(actual["summary"]["p95_storage_work_ns"], 1019)
        self.assertIn("not whole-server MSPT", actual["scope"])

    def test_sustained_ticks_reject_missing_duplicate_or_shuffled_samples(self):
        fixture = self._sustained_fixture()
        for altered in (
            fixture.replace("sample=8 operations=200", "sample=7 operations=200"),
            fixture.replace("sample=8 operations=200", "sample=28 operations=200"),
            fixture.replace("LOG REAL_50_DRIVE_SUSTAINED_TICK sample=8", "OTHER sample=8"),
        ):
            with self.subTest(altered=altered[:60]):
                with self.assertRaises(ValueError):
                    validated_sustained_tick_work(altered)

    def test_sustained_ticks_reject_fabricated_quantiles(self):
        fixture = self._sustained_fixture()
        for altered in (
            fixture.replace("p95_storage_work_ns=1019", "p95_storage_work_ns=1020"),
            fixture.replace("worst_storage_work_ns=1020", "worst_storage_work_ns=1019"),
            fixture.replace("operations=4000", "operations=3900"),
            fixture.replace("operations=200", "operations=199"),
        ):
            with self.subTest(altered=altered[-100:]):
                with self.assertRaises(ValueError):
                    validated_sustained_tick_work(altered)

    def test_sustained_ticks_reject_false_mspt_or_zero_durations(self):
        fixture = self._sustained_fixture()
        for altered in (
            fixture.replace("wall_clock_not_MSPT=true", "wall_clock_not_MSPT=false"),
            fixture.replace("not_server_MSPT=true", "not_server_MSPT=false"),
            fixture.replace("storage_work_ns=1001", "storage_work_ns=0"),
            fixture.replace("tick_wall_ns=50000001", "tick_wall_ns=0"),
        ):
            with self.subTest(altered=altered[-100:]):
                with self.assertRaises(ValueError):
                    validated_sustained_tick_work(altered)


    @staticmethod
    def _real_server_metrics_fixture():
        return ("REAL_SERVER_TICK_RING_V1 samples=100 p95_ns=1000 p99_ns=2000 worst_ns=3000 "
                "ring_scope=true uncontrolled=true\n"
                "REAL_SERVER_GC_WINDOW_V1 beans=2 collections_delta=0 time_ms_delta=0 "
                "approximate_gc_accounting=true uncontrolled=true\n")

    def test_real_server_observations_allow_no_gc_during_short_window(self):
        actual=validated_server_observations(self._real_server_metrics_fixture())
        self.assertEqual(actual["ticks"]["p99_ns"],2000)
        self.assertEqual(actual["gc"]["collections_delta"],0)

    def test_real_server_observations_reject_quantile_and_scope_mismatch(self):
        original=self._real_server_metrics_fixture()
        for changed in (original.replace("p95_ns=1000","p95_ns=4000"),
                        original.replace("p99_ns=2000","p99_ns=4000"),
                        original.replace("samples=100","samples=10"),
                        original.replace("ring_scope=true","ring_scope=false"),
                        original.replace("uncontrolled=true","uncontrolled=false")):
            with self.subTest(changed=changed[:65]):
                with self.assertRaises(ValueError):
                    validated_server_observations(changed)

    def test_real_server_observations_reject_missing_gc(self):
        original=self._real_server_metrics_fixture()
        for changed in (original.splitlines(keepends=True)[0], original+original,
                        original.replace("beans=2","beans=0"),
                        original.replace("approximate_gc_accounting=true","approximate_gc_accounting=false")):
            with self.subTest(changed=changed[:65]):
                with self.assertRaises(ValueError):
                    validated_server_observations(changed)


if __name__ == "__main__":
    unittest.main()
