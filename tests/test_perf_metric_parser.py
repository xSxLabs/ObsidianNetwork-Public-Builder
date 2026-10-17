#!/usr/bin/env python3
"""Make empty GameTest performance-report rows a CI failure."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "performance"))
from metric_parser import numbers_in, require_metrics


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


if __name__ == "__main__":
    unittest.main()
