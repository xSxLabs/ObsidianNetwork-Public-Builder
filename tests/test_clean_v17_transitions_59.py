#!/usr/bin/env python3
"""Build 59: fail closed tests for removal of deploy and first-use hotkey."""
import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
S=(ROOT/"features/v17/apply-power-armor-transitions-59.py").read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")
class Clean59(unittest.TestCase):
 def test_generator_python_valid_and_after_gecko(self):
  ast.parse(S)
  self.assertIn("apply-power-armor-transitions-59.py",WF)
  self.assertLess(WF.index("python3 features/v17/apply-power-armor-geckolib.py"),
                  WF.index("python3 features/v17/apply-power-armor-transitions-59.py"))
 def test_initial_wearing_does_not_require_backup(self):
  self.assertIn("backup==null?ItemStack.EMPTY:backup.previous().get(i).copy()",S)
  self.assertIn("if(!spawn(player,suit))return 0;",S)
  self.assertIn("if(backup!=null)saved.finish(player);",S)
  self.assertIn("if(ACTIVE.containsKey(player.getUUID()))",S)
  self.assertIn("public static int deploy(ServerPlayer player)",S)
  self.assertIn('Commands.literal("deploy")',S)
 def test_enter_rejects_second_suit_and_keeps_recovery(self):
  self.assertIn("if(PowerArmorRuntime.full(player))",S)
  self.assertIn("if(ACTIVE.containsKey(player.getUUID()))return;",S)
  self.assertIn('if(!full(stand))',S)
  self.assertIn('PowerArmorCommands.java',S)
 def test_apotheosis_actual_runtime_check_is_optional(self):
  self.assertIn('Class.forName("dev.shadowsoffire.apotheosis.loot.LootCategory")',S)
  self.assertIn('getMethod("forItem",ItemStack.class)',S)
  self.assertIn('Commands.literal("compat")',S)
  for t in ("HELMET","CHESTPLATE","LEGGINGS","BOOTS"):
   self.assertIn("POWER_ARMOR_MK2_"+t+".get()",S)
   self.assertIn("POWER_ARMOR_"+t+".get()",S)
if __name__=="__main__":unittest.main()
