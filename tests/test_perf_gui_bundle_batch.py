#!/usr/bin/env python3
"""Synthetic fail-closed gates for consolidated UI/terminal performance bundle.

The real Java compile, 50-drive tests and Minecraft GameTests are also required
by CI; these contracts are just fast first-stage validation.
"""
import ast
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
CONTROLLER=ROOT/"patches/perf-controller-menu-status-batching.py"
DRIVE=ROOT/"patches/perf-drive-menu-serialization-hotpath.py"
TERMINAL=ROOT/"patches/perf-terminal-jei-recipe-candidate-reuse.py"


def run_patch(path, root):
    return subprocess.run([sys.executable,str(path)],
                          env={**os.environ,"V1_SOURCE_ROOT":str(root)},
                          capture_output=True,text=True)


def source_str_assignment(path,name):
    tree=ast.parse(path.read_text())
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(
            isinstance(t,ast.Name) and t.id==name for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError(f"{name} not found in {path}")


class PerfGuiBundle(unittest.TestCase):
    def test_syntax(self):
        for path in (CONTROLLER,DRIVE,TERMINAL):
            ast.parse(path.read_text())

    def test_controller_21_fields_batched_once_per_tick(self):
        old=source_str_assignment(CONTROLLER,"old")
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            f=root/"dev/obsidiannetwork/menu/PowerStatusMenu.java"
            f.parent.mkdir(parents=True)
            f.write_text(
                "class PowerStatusMenu {private long lastSummaryTick;\n"
                "void probe(){long now=0; if(now - this.lastSummaryTick >= 20L){} }\n"
                +old+"\npublic int getCount(){return 21;}\nclass FuelContainer{}\n}")
            r=run_patch(CONTROLLER,root)
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            s=f.read_text()
            self.assertIn("XSXLABS_CONTROLLER_STATUS_ONCE_PER_TICK_V1",s)
            self.assertEqual(s.count("WorldTopologyBridge.runtimeForController(sl, c.getBlockPos())"),1)
            self.assertEqual(s.count("WorldTopologyBridge.templatesForRuntime(sl, r)"),1)
            self.assertIn("if (lastControllerTick != now",s)
            self.assertIn("WorldTopologyBridge.autocraftingBlockedJobs(sl, r)",s)
            for i in range(21):
                self.assertIn(f"controllerSnapshot[{i}] =",s)
            self.assertIn("else if (be instanceof SolidFuelGeneratorBlockEntity g)",s)
            self.assertNotEqual(run_patch(CONTROLLER,root).returncode,0)

    def test_drive_occupancy_and_gui_invalidation(self):
        tree=ast.parse(DRIVE.read_text())
        pairs={"drive":[],"menu":[]}
        for node in ast.walk(tree):
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=="change":
                if len(node.args)!=3 or not isinstance(node.args[0],ast.Name):
                    continue
                target=node.args[0].id
                pairs[target].append(ast.literal_eval(node.args[1]))
        self.assertEqual(len(pairs["drive"]),2)
        self.assertEqual(len(pairs["menu"]),8)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for folder,name,key in (
                 ("blockentity","StorageDriveBlockEntity.java","drive"),
                 ("menu","DriveMenu.java","menu")):
                f=root/("dev/obsidiannetwork/"+folder+"/"+name)
                f.parent.mkdir(parents=True,exist_ok=True)
                fixture = "class Fixture {\n"+"\n".join(pairs[key])+"\n}"
                if key == "menu":
                    fixture = "private static final int CELL_SLOTS = 16;\n" + fixture
                else:
                    fixture += ('\nthis.cellInventory.serialize(output.child("cell_inventory"));'
                                '\nthis.cellInventory.deserialize(input.childOrEmpty("cell_inventory"));'
                                '\nfor (int slot = 0; slot < StorageDriveRuntime.SLOTS; slot++) {}')
                f.write_text(fixture)
            r=run_patch(DRIVE,root)
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            be=(root/"dev/obsidiannetwork/blockentity/StorageDriveBlockEntity.java").read_text()
            ui=(root/"dev/obsidiannetwork/menu/DriveMenu.java").read_text()
            self.assertIn("XSXLABS_DRIVE_FAST_OCCUPANCY_V1",be)
            self.assertNotIn("this.cellInventory.getResource(i)",be)
            self.assertIn("cellInventory.copyToList()",be)
            self.assertIn("XSXLABS_DRIVE_GUI_TICK_SNAPSHOT_V1",ui)
            self.assertIn("cachedTick != tick",ui)
            self.assertIn("return cached[slot].copy();",ui)
            self.assertIn("return CELL_SLOTS;",ui)
            self.assertIn("new ItemStack[CELL_SLOTS]",ui)
            self.assertIn("new boolean[CELL_SLOTS]",ui)
            self.assertIn("slot >= CELL_SLOTS",ui)
            self.assertNotIn("slot >= 8",ui)
            self.assertIn("XSXLABS_DRIVE_LAST_CELL_ALL_16_V1",be)
            self.assertGreaterEqual(ui.count("invalidate();"),5)
            self.assertIn("this.be.removeCellAt(slot)",ui)
            self.assertNotEqual(run_patch(DRIVE,root).returncode,0)

    def test_terminal_jei_one_index_snapshot_conserves_rollback(self):
        old_start=source_str_assignment(TERMINAL,"old_start")
        old_loop=source_str_assignment(TERMINAL,"old_loop")
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            f=root/"dev/obsidiannetwork/menu/StorageTerminalMenu.java"
            f.parent.mkdir(parents=True)
            f.write_text(
                "public void applyJeiRecipeGrid(String recipeIdRaw, List<ItemStack> requested){\n"
                +old_start+"\nfor(int i=0;i<9;i++){\n"+old_loop+
                "\nreservedNet.merge(bestKey, 1L, Math::addExact);\n}\n"
                "runtime.storage().extract(desc[ixx].key(), 1L);\n"
                "runtime.storage().insertExact(desc[ixxx].key(), desc[ixxx].canonicalPayload(), 1L);\n"
                "this.batchingCraftMutation = false;\n"
                "ServerTerminalPayloadHandler.flushRuntimeDeltas(level, runtime);\n}\n"
                "private static Ingredient[] recipeIngredients3x3(CraftingRecipe recipe){return null;}\n")
            r=run_patch(TERMINAL,root)
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            s=f.read_text()
            self.assertEqual(s.count("runtime.storage().index().keysSnapshot()"),1)
            self.assertIn("for (ItemKey key : availableKeys)",s)
            self.assertIn("reservedNet.merge(bestKey, 1L, Math::addExact)",s)
            self.assertIn("runtime.storage().extract(desc[ixx].key(), 1L)",s)
            self.assertIn("ServerTerminalPayloadHandler.flushRuntimeDeltas(level, runtime);",s)
            self.assertNotEqual(run_patch(TERMINAL,root).returncode,0)

if __name__=="__main__":
    unittest.main()
