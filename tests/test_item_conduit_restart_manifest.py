#!/usr/bin/env python3
"""Focused filesystem invariants for the real ITEM conduit restart harness."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "integration/item_conduit_restart.py"
spec = importlib.util.spec_from_file_location("item_conduit_restart", SCRIPT)
restart = importlib.util.module_from_spec(spec)
spec.loader.exec_module(restart)


class WorldManifestTests(unittest.TestCase):
    def test_nonempty_level_dat_is_required(self):
        with tempfile.TemporaryDirectory() as d:
            world = Path(d)
            with self.assertRaisesRegex(AssertionError, "nonempty level.dat"):
                restart.world_manifest(world)
            (world / "level.dat").write_bytes(b"")
            with self.assertRaisesRegex(AssertionError, "nonempty level.dat"):
                restart.world_manifest(world)

    def test_missing_region_files_do_not_prevent_second_jvm_verification(self):
        with tempfile.TemporaryDirectory() as d:
            world = Path(d)
            (world / "level.dat").write_bytes(b"valid level file")
            manifest = restart.world_manifest(world)
            self.assertEqual(set(manifest), {"level.dat"})

    def test_active_filter_is_required_across_real_server_restart(self):
        harness = SCRIPT.read_text()
        probe = (SCRIPT.parent / "ItemConduitRestartProbe.java").read_text()
        for key in ("active_filter_runtime_verified", "active_filter_loaded_from_disk",
                    "active_filter_after_reconnect"):
            self.assertIn(key, harness)
        for key in ("V174_ITEM_CABLE_ACTIVE_ALLOWLIST_RESTART_467",
                    "B467_ACTIVE_FILTER_RUNTIME", "filteredDiamondsDelivered(level)",
                    "!sourceCable.cableAllows(Direction.WEST, emerald)",
                    "lane == 5 && index == 1"):
            self.assertIn(key, probe)

    def test_recursive_region_discovery_and_hashes(self):
        with tempfile.TemporaryDirectory() as d:
            world = Path(d)
            (world / "level.dat").write_bytes(b"world")
            region = world / "alternate" / "region"
            region.mkdir(parents=True)
            (region / "r.0.0.mca").write_bytes(b"chunk")
            manifest = restart.world_manifest(world)
            self.assertEqual(set(manifest), {"level.dat", "alternate/region/r.0.0.mca"})
            self.assertTrue(all(len(h) == 64 for h in manifest.values()))


if __name__ == "__main__":
    unittest.main()
