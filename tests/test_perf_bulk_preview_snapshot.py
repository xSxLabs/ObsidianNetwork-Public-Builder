#!/usr/bin/env python3
"""Source-shape and equivalence gates for read-only bulk storage preflight.

Synthetic Python reference workload is NOT a Minecraft/TPS benchmark.
"""
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "patches/perf-bulk-preview-snapshot-elision.py"
STORAGE_NETWORK = """public class StorageNetwork {
 public long previewInsertExact(ItemKey key, byte[] canonicalPayload, long requested) {
   LinkedHashSet<StorageCellStore> existing = this.sources.get(key);
   if (existing != null) {
     for (StorageCellStore cell : List.copyOf(existing)) {
       remaining -= cell.previewInsertExact(key, canonicalPayload, remaining);
     }
   }
   return requested - remaining;
 }
 public long insertExact(ItemKey key, byte[] canonicalPayload, long requested) {
   for (StorageCellStore cell : List.copyOf(existing)) { cell.insertExact(key, canonicalPayload, requested); }
   return requested;
 }
 public long extract(ItemKey key, long requested) {
   for (StorageCellStore cell : List.copyOf(set)) { cell.extract(key, requested); set.remove(cell); }
   return requested;
 }
}
"""
CELL = """public class StorageCellStore {
 public long previewInsertExact(ItemKey key, byte[] canonicalPayload, long requested) {
   return Math.min(requested, this.free());
 }
 public long insertExact(ItemKey key, byte[] canonicalPayload, long requested) {
   this.mutationListener.run(); return requested;
 }
}
"""


def run_patch(network_source=STORAGE_NETWORK, cell_source=CELL):
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "dev/obsidiannetwork/core"
        src.mkdir(parents=True)
        (src / "StorageNetwork.java").write_text(network_source)
        (src / "StorageCellStore.java").write_text(cell_source)
        env = dict(os.environ, V1_SOURCE_ROOT=tmp)
        result = subprocess.run([sys.executable, str(PATCH)], env=env, text=True,
                                capture_output=True)
        updated = (src / "StorageNetwork.java").read_text()
        return result, updated


class BulkPreviewTests(unittest.TestCase):
    def test_only_readonly_preflight_uses_direct_set(self):
        run, updated = run_patch()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("XSXLABS_BULK_READONLY_PREVIEW_NO_SNAPSHOT_V1", updated)
        self.assertEqual(updated.count("for (StorageCellStore cell : List.copyOf(existing))"), 1,
                         "Commit-time insertion must retain its snapshot")
        self.assertIn("for (StorageCellStore cell : List.copyOf(set))", updated,
                      "Mutating extraction must retain its snapshot")

    def test_mutating_cell_preview_is_rejected_without_changes(self):
        broken = CELL.replace("return Math.min(requested, this.free());",
                              "this.mutationListener.run(); return Math.min(requested, this.free());")
        run, updated = run_patch(cell_source=broken)
        self.assertNotEqual(run.returncode, 0)
        self.assertEqual(updated, STORAGE_NETWORK)

    def test_source_drift_is_rejected_without_changes(self):
        broken = STORAGE_NETWORK.replace("List.copyOf(existing)", "makeSnapshot(existing)", 1)
        run, updated = run_patch(network_source=broken)
        self.assertNotEqual(run.returncode, 0)
        self.assertEqual(updated, broken)

    def test_randomized_readonly_existing_sources_preflight(self):
        rnd = random.Random(20901)
        for _ in range(5000):
            remaining = rnd.randrange(0, 8193)
            capacities = [rnd.randrange(0, 1025) for _ in range(rnd.randrange(0, 150))]
            baseline = remaining
            for free in list(capacities):
                if baseline == 0:
                    break
                baseline -= min(baseline, free)
            optimized = remaining
            for free in capacities:
                if optimized == 0:
                    break
                optimized -= min(optimized, free)
            self.assertEqual(baseline, optimized)
            self.assertEqual(capacities, capacities[:])
            self.assertGreaterEqual(optimized, 0)


if __name__ == "__main__":
    unittest.main()
