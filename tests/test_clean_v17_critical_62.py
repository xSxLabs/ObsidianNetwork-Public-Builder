#!/usr/bin/env python3
"""Build 62 contract tests: real no-dup semantics instead of text-only Gecko checks."""
import ast, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
S=(ROOT/"features/v17/apply-power-armor-critical-62.py").read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")
class Critical62(unittest.TestCase):
 def test_overlay_after_all_earlier_fixes(self):
  ast.parse(S)
  self.assertIn("python3 features/v17/apply-power-armor-critical-62.py",WF)
  self.assertLess(WF.index("python3 features/v17/apply-power-armor-enter-packet-60.py"),
                  WF.index("python3 features/v17/apply-power-armor-critical-62.py"))
 def test_exit_removes_first_then_creates_only_one_suit(self):
  src=S.split("new=''' public static int exit(ServerPlayer player){",1)[1].split("'''",1)[0]
  self.assertLess(src.index("player.setItemSlot(slot,ItemStack.EMPTY)"),
                  src.index("ArmorStand stand=spawn(player,worn)"))
  self.assertIn("if(stand==null)",src)
  self.assertIn("stand.discard();",src)
  self.assertIn("saved.finish(player)",src)
  self.assertIn("stale power-armor backup",src)
 def test_enter_transfers_then_discards_with_revert(self):
  src=S.split("new=''' private static void finishEntering",1)[1].split("'''",1)[0]
  self.assertLess(src.index("stand.setItemSlot(slot,ItemStack.EMPTY)"),
                  src.index("player.setItemSlot(PowerArmorRuntime.SLOTS[i],suit.get(i))"))
  self.assertIn("ItemStack.matches",src)
  self.assertIn("saved.save(player,original)",src)
  self.assertIn("saved.finish(player)",src)
  self.assertIn("stand.discard()",src)
 def test_early_right_click_and_animation_are_live(self):
  self.assertIn("InputEvent.InteractionKeyMappingTriggered",S)
  self.assertIn("event.isUseItem()",S)
  self.assertIn("mc.hitResult instanceof net.minecraft.world.phys.EntityHitResult",S)
  self.assertIn("pose(stand,t,animation.entering());",S)
  self.assertIn("PowerArmorVisualEntity.java",S)
if __name__=="__main__":unittest.main()
