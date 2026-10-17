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
