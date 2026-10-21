#!/usr/bin/env python3
"""Fail-closed staging for real 8/9 ingredient quick-move GameTests."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "patches/inject-terminal-nine-ingredient-gametest.py"
WORKFLOW = ROOT / ".github/workflows/networkstorage-v1.6.yml"

FIXTURE = '''
class Build103GameTests {
  void run() {
    var xsxlabsBurstTerminalPos = somePos;
    var xsxCraftInv=xsxCraftPlayer.getInventory();
    xsxCraftMenu.clicked(0,0,net.minecraft.world.inventory.ContainerInput.QUICK_MOVE,xsxCraftPlayer);
    if(!rt.powered())throw new IllegalStateException("Shift crafting test network unpowered");
    var xsxCraftSequence=h.startSequence();
    xsxCraftSequence.thenExecute(()->{ });
  }
}
'''

class EightNineRecipeTest(unittest.TestCase):
    def inject(self, source):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "dev/obsidiannetwork/build103/Build103GameTests.java"
            target.parent.mkdir(parents=True)
            target.write_text(source)
            run = subprocess.run(
                [sys.executable, str(PATCH)],
                env={**os.environ, "V1_SOURCE_ROOT": folder},
                capture_output=True, text=True)
            return run, target.read_text()

    def test_both_8_and_9_input_recipes_are_real_menu_quickmoves(self):
        run, source = self.inject(FIXTURE)
        self.assertEqual(run.returncode, 0, run.stderr+run.stdout)
        for fragment in (
            "Items.IRON_INGOT,net.minecraft.world.item.Items.IRON_BLOCK",
            "Items.OAK_PLANKS,16",
            "XSXLABS_EIGHT_SLOT_NEXT_TICK_V2",
            "xsxCraftSequence.thenExecuteAfter(1,()->{",
            "xsxEightSlot==5 ? net.minecraft.world.item.ItemStack.EMPTY",
            "xsxCraftMenu.clicked(0,0,",
            "xsxEightAfter-xsxEightBefore!=16",
            "xsxNineProduced!=16",
            "XSXLABS_REAL_NINE_INGREDIENT_SHIFT_CRAFT_V1 PASS cases=4",
            "XSXLABS_REAL_EIGHT_INGREDIENT_SHIFT_CRAFT_V1 PASS ingredients=128",
            "not_server_MSPT=true",
        ):
            self.assertIn(fragment, source)
        rerun, unchanged = self.inject(source)
        self.assertNotEqual(rerun.returncode, 0)
        self.assertEqual(unchanged, source)

    def test_missing_fixture_anchor_fails_closed(self):
        run, source = self.inject(FIXTURE.replace(
            'Shift crafting test network unpowered', 'missing intended anchor'))
        self.assertNotEqual(run.returncode, 0)
        self.assertEqual(source, FIXTURE.replace(
            'Shift crafting test network unpowered', 'missing intended anchor'))

    def test_missing_tick_sequence_fails_closed(self):
        broken = FIXTURE.replace("xsxCraftSequence.thenExecute(()->{ });",
                                 "// deleted completion callback")
        run, source = self.inject(broken)
        self.assertNotEqual(run.returncode, 0)
        self.assertEqual(source, broken)

    def test_both_curios_modes_must_report_both_recipes(self):
        text = WORKFLOW.read_text()
        for log in ("build103-postpatch-gametest.log",
                    "build103-curios-installed-gametest.log"):
            for marker in (
                "XSXLABS_REAL_NINE_INGREDIENT_SHIFT_CRAFT_V1 PASS cases=4",
                "XSXLABS_REAL_EIGHT_INGREDIENT_SHIFT_CRAFT_V1 PASS ingredients=128 results=16"):
                self.assertIn(f"grep -Fq '{marker}' /tmp/{log}", text)

if __name__ == "__main__":
    unittest.main()
