"""B1261: real reconstructed Block Java patch and pickup safety checks.

These are source/behavioral-model gates, not a substitute for the full Java
compile or multiplayer ingame test.
"""
import ast
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
FEATURE=ROOT/"features/v176"
PATCH=FEATURE/"apply-v176-b1261-backpack-selected-hotbar-pickup.py"
PLACEMENT=FEATURE/"apply-v176-backpack-world-placement.py"
WORKFLOW=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"


def block_fixture():
    tree=ast.parse(PLACEMENT.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if (isinstance(node,ast.Call) and isinstance(node.func,ast.Name)
                and node.func.id=="add" and len(node.args)>=2
                and isinstance(node.args[0],ast.Constant)
                and node.args[0].value=="backpack/NetworkBackpackBlock.java"):
            code=ast.literal_eval(node.args[1])
            old="""  // Terminal-style GUI open will be connected after menu registration.
  return InteractionResult.SUCCESS;"""
            assert code.count(old)==1
            return code.replace(old,"  return V176BackpackOpen.openPlaced(server,pos);",1)
    raise AssertionError("B1261_BASE_BLOCK_GENERATOR_MISSING")


def execute_patch(source=None):
    if source is None:source=block_fixture()
    with tempfile.TemporaryDirectory() as tmp:
        target=Path(tmp)/"dev/obsidiannetwork/backpack/NetworkBackpackBlock.java"
        target.parent.mkdir(parents=True)
        target.write_text(source,encoding="utf-8")
        run=subprocess.run([sys.executable,str(PATCH)],
            env={**os.environ,"V1_SOURCE_ROOT":tmp},
            capture_output=True,text=True)
        return run,target.read_text(encoding="utf-8")


def model_pickup(hotbar,selected,placed,remove_ok=True):
    """Ownership state machine: vacant selection is the only allowed target."""
    inv=list(hotbar)
    if not 0<=selected<9 or inv[selected] is not None or placed is None:
        return inv,placed,False
    original=placed
    placed=None
    inv[selected]=original
    if not remove_ok:
        inv[selected]=None
        placed=original
        return inv,placed,False
    return inv,placed,True


class BackpackHotbarPickupB1261(unittest.TestCase):
    def test_patch_applies_to_actual_generated_world_block(self):
        ast.parse(PATCH.read_text(encoding="utf-8"))
        result,source=execute_patch()
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn("B1261_BACKPACK_SELECTED_EMPTY_HOTBAR_PICKUP_FAIL_CLOSED_PASS",result.stdout)
        self.assertIn("getSelectedSlot()",source)
        self.assertIn("Inventory.isHotbarSlot(selected)",source)
        self.assertIn("!inventory.getItem(selected).isEmpty()",source)
        self.assertIn("inventory.setItem(selected,original);",source)
        self.assertIn("if(!world.removeBlock(pos,false))",source)
        self.assertIn("bag.setBackpack(original);",source)
        self.assertNotIn("getInventory().add(original)",source)
        self.assertNotIn("Containers.dropItemStack",source)
        self.assertIn("return V176BackpackOpen.openPlaced(server,pos);",source)
        self.assertEqual(source.count("bag.takeBackpack()"),1)
        self.assertEqual(source.count("useItemOn("),1)
        self.assertEqual(source.count("useWithoutItem("),1)

    def test_take_only_after_selected_slot_check(self):
        result,source=execute_patch()
        self.assertEqual(result.returncode,0)
        a=source.index("!inventory.getItem(selected).isEmpty()")
        b=source.index("bag.takeBackpack()")
        c=source.index("inventory.setItem(selected,original)")
        d=source.index("if(!world.removeBlock(pos,false))")
        self.assertLess(a,b)
        self.assertLess(b,c)
        self.assertLess(c,d)
        self.assertIn("inventory.setItem(selected,ItemStack.EMPTY);",source)

    def test_drift_fails_before_writing_java(self):
        original=block_fixture().replace(
            "if(!server.getInventory().add(original))",
            "if(!server.getInventory().add(original.copy()))")
        result,after=execute_patch(original)
        self.assertNotEqual(result.returncode,0)
        self.assertIn("B1261_BACKPACK_PICKUP_SOURCE_DRIFT",result.stderr)
        self.assertEqual(after,original)

    def test_all_24_variants_keep_full_item_components_and_no_overwrite(self):
        for tier in range(1,25):
            # The same original stack, including stored cell/component payload.
            bag=("backpack",tier,{"cells":("filled","equipment"),"magnet":"enabled"})
            for selected in range(9):
                inv=[None]*9
                result,world,taken=model_pickup(inv,selected,bag)
                self.assertTrue(taken)
                self.assertIsNone(world)
                self.assertIs(result[selected],bag)
                self.assertEqual(sum(x is not None for x in result),1)
                inv[selected]=("occupied",selected)
                before=list(inv)
                result,world,taken=model_pickup(inv,selected,bag)
                self.assertFalse(taken)
                self.assertEqual(result,before)
                self.assertIs(world,bag)
                # A failed world removal must restore the original BE owner.
                inv=[None]*9
                result,world,taken=model_pickup(inv,selected,bag,False)
                self.assertFalse(taken)
                self.assertEqual(result,inv)
                self.assertIs(world,bag)

    def test_no_other_subsystem_or_frozen_branch_modified(self):
        p=PATCH.read_text(encoding="utf-8")
        for unrelated in ("features/v175/","PowerArmorEntrySequence",
                          "NetworkDriveBlockEntity","ReactorController",
                          "V176BackpackCells.insert","xsxCableCommitRevision"):
            self.assertNotIn(unrelated,p)
        workflow=WORKFLOW.read_text("utf-8")
        self.assertIn(PATCH.name,workflow)
        self.assertIn(Path(__file__).name,workflow)
        self.assertGreater(workflow.index(PATCH.name),
                           workflow.index("apply-v176-b1258-backpack-preview-and-resource-reuse.py"))


if __name__=="__main__":
    unittest.main()
