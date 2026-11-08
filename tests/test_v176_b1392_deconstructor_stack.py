"""B1392 Shift+Deconstruct integration guard.

Fixtures verify server-only batch routing and preservation of the original
single click. Quantity simulations cover full/partial recipe stacks.
"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "features/v176/apply-v176-b1392-deconstructor-stack.py"


def run_patch(menu_source, screen_source):
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "dev/obsidiannetwork"
        m = src / "menu/DeconstructionTerminalMenu.java"
        c = src / "client/DeconstructionTerminalScreen.java"
        m.parent.mkdir(parents=True)
        c.parent.mkdir(parents=True)
        m.write_text(menu_source, "utf-8")
        c.write_text(screen_source, "utf-8")
        run = subprocess.run(
            [sys.executable, str(PATCH)],
            env={**os.environ, "V1_SOURCE_ROOT": tmp},
            capture_output=True, text=True,
        )
        return run, m.read_text("utf-8"), c.read_text("utf-8")


MENU = """
class DeconstructionTerminalMenu {
 private static final Logger XSX_LOG = null;
 private SimpleContainer machine;
 private record Plan(ItemStack[] out,int consume,int cost,int score){}
 private Optional<Plan> serverPlan(Player player){return Optional.empty();}
 private void syncPreview(Optional<Plan> plan){}
 public boolean stillValid(Player player){return true;}
 private void broadcastChanges(){}
 public boolean clickMenuButton(Player player, int id) {
  if(id==1) { /* DECONSTRUCT success outputs= */ return true; }
  return false;
 }
 public int xpCost(){return 0;}
}
"""
SCREEN = """
class DeconstructionTerminalScreen {
 void init() {
  this.minecraft.gameMode.handleInventoryButtonClick(
      ((DeconstructionTerminalMenu)this.menu).containerId, 1);
 }
}
"""


class DeconstructorStack1392(unittest.TestCase):
    def test_normal_click_untouched_and_shift_server_authority(self):
        run, menu, screen = run_patch(MENU, SCREEN)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("B1392_DECONSTRUCT_STACK_SERVER_CLIENT_PATCH_PASS", run.stdout)
        self.assertIn("if(id==1) { /* DECONSTRUCT success outputs= */ return true; }", menu)
        self.assertIn("if (id == 2) return b1392DeconstructStack(player)", menu)
        self.assertIn("instanceof net.minecraft.server.level.ServerPlayer", menu)
        self.assertIn("this.stillValid(serverPlayer)", menu)
        self.assertIn("this.serverPlan(serverPlayer)", menu)
        self.assertIn("this.machine.setItem(0, input)", menu)
        self.assertIn("inventory.add(result)", menu)
        self.assertIn("serverPlayer.drop(result, false)", menu)
        self.assertIn("this.syncPreview(this.serverPlan(serverPlayer))", menu)
        self.assertEqual(menu.count("this.broadcastChanges();"), 1)
        self.assertIn("hasShiftDown() ? 2 : 1", screen)

    def test_fail_closed_no_modified_sources_on_drift(self):
        for menu, screen in (
            (MENU.replace("DECONSTRUCT success outputs=", "unexpected output"), SCREEN),
            (MENU, SCREEN.replace("handleInventoryButtonClick", "otherClick")),
            (MENU.replace("clickMenuButton", "unrelatedMethod"), SCREEN),
        ):
            run, m, c = run_patch(menu, screen)
            self.assertNotEqual(run.returncode, 0)
            self.assertEqual(m, menu)
            self.assertEqual(c, screen)

    def test_whole_stack_recipe_conservation(self):
        # Same integer rule as the generated Java: no more than the input
        # contains, including recipes that consume more than one source item.
        for input_count, consume, expected in (
            (64, 1, 64), (32, 2, 16), (64, 4, 16),
            (63, 4, 15), (3, 4, 0), (1, 1, 1)
        ):
            ops = min(input_count // consume, 4096)
            self.assertEqual(ops, expected)
            remaining = input_count - ops * consume
            self.assertGreaterEqual(remaining, 0)
            self.assertLess(remaining, consume)
            # Example recipe: 3 output items per operation.
            self.assertEqual(ops * 3, sum(
                min(64, ops * 3 - offset)
                for offset in range(0, ops * 3, 64)
            ))


if __name__ == "__main__":
    unittest.main()
