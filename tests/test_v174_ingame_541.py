#!/usr/bin/env python3
"""B541 independent source safety gates for tank, HUD, and formed visuals."""
import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"features/v174/apply-v174-ingame-541.py"
class TestFixes(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.code=P.read_text(encoding="utf-8");ast.parse(cls.code)
 def test_helmet_in_one_tick_not_once_per_second(self):
  s=self.code
  self.assertIn("B541_FAST_HELMET",s)
  self.assertIn("int offer=(int)Math.min(room,(long)held.getAmount());",s)
  self.assertIn("NutriPaste.add(stack,taken.getAmount())",s)
  self.assertIn("if(inserted<taken.getAmount())",s)
  self.assertNotIn("getGameTime()%20L!=0L",s)
 def test_only_paste_enters_helmet(self):
  s=self.code
  self.assertIn("held.getFluid()!=dev.obsidiannetwork.nutrition.NutriPasteFluids.SOURCE.get()",s)
  self.assertIn("B541_TANK_HELMET_OR_EMPTY_BUCKET_ONLY",s)
  self.assertIn("Items.BUCKET",s)
  self.assertIn("stack.getCount()!=1",s)
 def test_bucket_transaction_safety(self):
  s=self.code
  self.assertIn("held.getAmount()<1000",s)
  self.assertIn("held.getFluid().getBucket()",s)
  self.assertIn("result==net.minecraft.world.item.Items.AIR",s)
  self.assertIn("tankFluid.drain(1000",s)
  self.assertIn("if(!drawn.isEmpty())tankFluid.fill(drawn",s)
  self.assertIn("NUTRIPASTE_BUCKET",s)
  self.assertIn(".bucket(()->dev.obsidiannetwork.ObsidianNetwork.NUTRIPASTE_BUCKET.get())",s)
 def test_hotbar_placement_not_chat_rows(self):
  s=self.code
  self.assertIn("B541_HUD_LEFT_OF_HOTBAR_FE",s)
  self.assertIn("B541_HUD_LEFT_OF_HOTBAR_PASTE",s)
  self.assertIn("getGuiScaledHeight()-29",s)
  self.assertIn("getGuiScaledHeight()-47",s)
  self.assertIn("B541_NO_H_LABEL",s)
 def test_forms_8_variants_no_server_tick(self):
  s=self.code
  self.assertIn("B541_EIGHT_STATE_REGRESSION",s)
  self.assertIn("block/reactor_casing_formed_top.png",s)
  self.assertIn("powerbank_casing_formed",s)
  self.assertIn("minecraft:block/cube",s)
  self.assertNotIn("new BlockEntityRenderer",s)
if __name__=="__main__":unittest.main()
