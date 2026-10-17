#!/usr/bin/env python3
"""Validate exact, fail-closed empty ghost filter patching without Minecraft."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PATCH = Path(__file__).resolve().parents[1] / "patches/standalone-cable-empty-filter-load.py"
FIXTURE = """class LogisticsCableBlockEntity {
 // XSXLABS_CABLE_INDEXED_GHOSTS_V3
 // XSXLABS_CABLE_FILTERS_LOAD
 void save() { String value = key == null ? "" : key.toString(); }
 void load() {
                   net.minecraft.resources.Identifier key =
                       net.minecraft.resources.Identifier.tryParse(ids.get(i));
                   if (key != null && allowed.add(key))
                      this.cableSlotIds[face.ordinal()][i]=key;
 }
 boolean allowed() { return this.mode(side) != Mode.IMPORT || allowed.isEmpty() || allowed.contains(id); }
}
"""


class EmptyGhostFilterPatchTests(unittest.TestCase):
    def apply(self, text):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "dev/obsidiannetwork/blockentity/LogisticsCableBlockEntity.java"
            target.parent.mkdir(parents=True)
            target.write_text(text)
            env = dict(os.environ, V1_SOURCE_ROOT=temp)
            run = subprocess.run([sys.executable, str(PATCH)],
                                 env=env, capture_output=True, text=True)
            return run, target.read_text()

    def test_exact_patch_keeps_nonblank_filters_and_rejects_empty_slots(self):
        result, updated = self.apply(FIXTURE)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("rawFilterId.isEmpty() ? null", updated)
        self.assertIn("!key.getPath().isEmpty()", updated)
        self.assertIn('return key == null ? "" : key.toString();', updated)
        self.assertIn("allowed.contains(id)", updated)
        self.assertNotIn("Identifier.tryParse(ids.get(i));", updated)

    def test_source_drift_fails_without_modifying_file(self):
        modified = FIXTURE.replace("Identifier.tryParse(ids.get(i));",
                                   "Identifier.tryParse(someOtherData);")
        result, updated = self.apply(modified)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("filter load loop anchor changed", result.stderr)
        self.assertEqual(updated, modified)


if __name__ == "__main__":
    unittest.main()
