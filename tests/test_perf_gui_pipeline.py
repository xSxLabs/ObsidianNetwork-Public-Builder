#!/usr/bin/env python3
"""Fail-closed synthetic tests for the integrated GUI/JEI performance batch.

These tests check real textual patch application, not a Minecraft compilation.
The GitHub Actions Java compile, GameTests and server restart remain mandatory.
"""
import ast
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATCHES = {
    "autocrafter": "patches/perf-autocrafter-menu-once-per-tick.py",
    "controller": "patches/perf-controller-menu-status-batching.py",
    "drive": "patches/perf-drive-menu-serialization-hotpath.py",
    "jei": "patches/perf-terminal-jei-recipe-candidate-reuse.py",
}


def run_patch(name, source_root):
    env = dict(os.environ, V1_SOURCE_ROOT=str(source_root))
    return subprocess.run(
        [sys.executable, str(ROOT / PATCHES[name])],
        env=env, capture_output=True, text=True
    )


def assigned_string(script, variable):
    tree = ast.parse((ROOT / script).read_text(encoding="utf-8"))
    matches = [
        node.value.value for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == variable for target in node.targets)
        and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)
    ]
    assert len(matches) == 1, (script, variable, len(matches))
    return matches[0]


def drive_replacements():
    tree = ast.parse((ROOT / PATCHES["drive"]).read_text(encoding="utf-8"))
    changes = {"drive": [], "menu": []}
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "change" and len(node.args) == 3
                and isinstance(node.args[0], ast.Name)
                and node.args[0].id in changes
                and all(isinstance(a, ast.Constant) and isinstance(a.value, str)
                        for a in node.args[1:])):
            changes[node.args[0].id].append((node.args[1].value, node.args[2].value))
    assert len(changes["drive"]) == 1
    assert len(changes["menu"]) == 7
    return changes


class IntegratedGuiPerformanceTests(unittest.TestCase):
    def test_all_four_patches_are_in_the_actual_build_pipeline(self):
        workflow = (ROOT / ".github/workflows/networkstorage-v1.6.yml").read_text()
        after_wireless = workflow.index(
            "python3 features/wireless-energy/apply-wireless-unlimited-transmitter.py"
        )
        before_build = workflow.index("echo '===== BUILD 101 FINAL BUILD ====='")
        markers = []
        for name, filename in PATCHES.items():
            command = "python3 " + filename
            self.assertEqual(workflow.count(command), 1, name)
            offset = workflow.index(command)
            self.assertGreater(offset, after_wireless, name)
            self.assertLess(offset, before_build, name)
            markers.append(offset)
        self.assertEqual(markers, sorted(markers))
        self.assertIn("python3 -m unittest discover -s tests -p 'test_perf_*.py' -v", workflow)

    def test_controller_all_21_fields_preserved_and_one_tick_snapshot(self):
        old = assigned_string(PATCHES["controller"], "old")
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "dev/obsidiannetwork/menu/PowerStatusMenu.java"
            file.parent.mkdir(parents=True)
            file.write_text(
                old + "\n"
                + "private long lastSummaryTick;\n"
                + "if (now - this.lastSummaryTick >= 20L) {} \n"
                + "int getCount() {return 21;}\n"
                + "class FuelContainer {}\n", encoding="utf-8"
            )
            result = run_patch("controller", tmp)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            patched = file.read_text()
            self.assertIn("XSXLABS_CONTROLLER_STATUS_ONCE_PER_TICK_V1", patched)
            self.assertIn("if (lastControllerTick != now || lastControllerLevel != sl)", patched)
            self.assertEqual(patched.count("WorldTopologyBridge.runtimeForController(sl, c.getBlockPos())"), 1)
            for i in range(21):
                self.assertEqual(patched.count("controllerSnapshot[" + str(i) + "] ="), 1)
            self.assertIn("now - this.lastSummaryTick >= 20L", patched)
            self.assertNotEqual(run_patch("controller", tmp).returncode, 0)
            self.assertEqual(patched, file.read_text())

    def test_drive_menu_preserves_live_writes_and_has_defensive_copies(self):
        replacements = drive_replacements()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "dev/obsidiannetwork"
            drive = root / "blockentity/StorageDriveBlockEntity.java"
            menu = root / "menu/DriveMenu.java"
            for target, kind in ((drive, "drive"), (menu, "menu")):
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("\n".join(old for old, _ in replacements[kind]), encoding="utf-8")
            result = run_patch("drive", tmp)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            updated_drive = drive.read_text()
            updated_menu = menu.read_text()
            self.assertIn("XSXLABS_DRIVE_FAST_OCCUPANCY_V1", updated_drive)
            self.assertIn("this.cellInventory.copyToList()", updated_drive)
            self.assertIn("XSXLABS_DRIVE_GUI_TICK_SNAPSHOT_V1", updated_menu)
            self.assertIn("return cached[slot].copy();", updated_menu)
            self.assertIn("return this.be.removeCellAt(slot);", "\n".join(
                old for old, _ in replacements["menu"]
            ))
            self.assertEqual(updated_menu.count("invalidate();"), 5)
            self.assertIn("this.be.cellStack(slot);", updated_menu)
            self.assertNotEqual(run_patch("drive", tmp).returncode, 0)
            self.assertEqual(updated_drive, drive.read_text())
            self.assertEqual(updated_menu, menu.read_text())

    def test_jei_recipe_snapshots_once_but_conservation_is_unchanged(self):
        prefix = (
            "public void applyJeiRecipeGrid(Inventory inv) {\n"
            "                        HashMap<ItemKey, Long> reservedNet = new HashMap<>();\n"
            "                        int invSize = sp.getInventory().getContainerSize();\n"
            "for (ItemKey key : runtime.storage().index().keysSnapshot()) {}\n"
            "reservedNet.merge(bestKey, 1L, Math::addExact);\n"
            "runtime.storage().extract(desc[ixx].key(), 1L);\n"
            "runtime.storage().insertExact(desc[ixxx].key(), desc[ixxx].canonicalPayload(), 1L);\n"
            "this.batchingCraftMutation = false;\n"
            "ServerTerminalPayloadHandler.flushRuntimeDeltas(level, runtime);\n"
            "}\n"
            "private static Ingredient[] recipeIngredients3x3() {}\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "dev/obsidiannetwork/menu/StorageTerminalMenu.java"
            file.parent.mkdir(parents=True)
            file.write_text(prefix, encoding="utf-8")
            result = run_patch("jei", tmp)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            patched = file.read_text()
            self.assertEqual(patched.count("runtime.storage().index().keysSnapshot()"), 1)
            self.assertIn("for (ItemKey key : availableKeys)", patched)
            self.assertIn("reservedNet.merge(bestKey, 1L, Math::addExact)", patched)
            self.assertIn("runtime.storage().extract(desc[ixx].key(), 1L)", patched)
            self.assertIn("runtime.storage().insertExact(desc[ixxx].key(), desc[ixxx].canonicalPayload(), 1L)", patched)
            self.assertNotEqual(run_patch("jei", tmp).returncode, 0)
            self.assertEqual(patched, file.read_text())

    def test_jei_missing_conservation_anchor_aborts_without_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "dev/obsidiannetwork/menu/StorageTerminalMenu.java"
            file.parent.mkdir(parents=True)
            text = ("public void applyJeiRecipeGrid(\n"
                    "HashMap<ItemKey, Long> reservedNet = new HashMap<>();\n"
                    "int invSize = sp.getInventory().getContainerSize();\n"
                    "for (ItemKey key : runtime.storage().index().keysSnapshot()) {}\n"
                    "private static Ingredient[] recipeIngredients3x3(")
            file.write_text(text)
            self.assertNotEqual(run_patch("jei", tmp).returncode, 0)
            self.assertEqual(file.read_text(), text)


if __name__ == "__main__":
    unittest.main()
