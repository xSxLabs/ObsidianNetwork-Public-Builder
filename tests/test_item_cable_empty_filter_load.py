#!/usr/bin/env python3
"""Fail-closed source contract tests for the empty cable ghost-slot fix."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PATCH = Path(__file__).resolve().parents[1] / "patches/item-cable-empty-filter-load.py"
TARGET = "dev/obsidiannetwork/blockentity/LogisticsCableBlockEntity.java"
SOURCE = """
public final class LogisticsCableBlockEntity {
 // XSXLABS_CABLE_INDEXED_GHOSTS_V3
 // XSXLABS_CABLE_FILTERS_LOAD
 for (int i=0; i<Math.min(ids.size(),18); i++) {
                   net.minecraft.resources.Identifier key =
                       net.minecraft.resources.Identifier.tryParse(ids.get(i));
                   if (key != null && allowed.add(key))
                      this.cableSlotIds[face.ordinal()][i]=key;
 }
 return this.mode(side) != Mode.IMPORT || allowed.isEmpty() || allowed.contains(id);
}
"""


class CableEmptyGhostLoadTests(unittest.TestCase):
    def test_patch_preserves_index_and_blocks_empty_entries(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / TARGET
            path.parent.mkdir(parents=True)
            path.write_text(SOURCE)
            env = os.environ.copy()
            env["V1_SOURCE_ROOT"] = d
            run = subprocess.run([sys.executable, str(PATCH)], env=env, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            updated = path.read_text()
            self.assertIn("if (storedFilterId == null || storedFilterId.isEmpty()) continue;", updated)
            self.assertIn("this.cableSlotIds[face.ordinal()][i]=key;", updated)
            self.assertIn("ITEM_GHOST_EMPTY_SLOT_LOAD_FIX_V1 PASS", run.stdout)
            again = subprocess.run([sys.executable, str(PATCH)], env=env, capture_output=True, text=True)
            self.assertNotEqual(again.returncode, 0, "Unexpected second patch must fail closed")

    def test_changed_upstream_parser_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / TARGET
            path.parent.mkdir(parents=True)
            path.write_text(SOURCE.replace("tryParse(ids.get(i))", "tryParse(other)"))
            env = os.environ.copy()
            env["V1_SOURCE_ROOT"] = d
            run = subprocess.run([sys.executable, str(PATCH)], env=env, capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertEqual(path.read_text(), SOURCE.replace("tryParse(ids.get(i))", "tryParse(other)"))


if __name__ == "__main__":
    unittest.main()
