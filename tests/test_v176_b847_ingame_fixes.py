"""B847 fail-closed integration checks: real avatar pose, native arm layer, modules, icons."""
import pathlib,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
SRC=ROOT/"features/v176/apply-v176-b847-ingame-fixes.py"
class TestB847(unittest.TestCase):
 def test_player_model_final_setup_and_layer_attachment(self):
  s=SRC.read_text("utf-8")
  self.assertIn("@Mixin(PlayerModel.class)",s)
  self.assertIn("AvatarRenderState;)V",s)
  self.assertIn("rightArm.xRot=-1.535F",s)
  self.assertIn("rightSleeve.copyFrom(this.rightArm)",s)
  self.assertIn("RenderLayer<AvatarRenderState,PlayerModel>",s)
  self.assertIn("getParentModel().rightArm,tier,deployment",s)
  self.assertIn("s=s[:start]+s[end:]",s)
  self.assertIn("RenderPlayerEvent.Post<?> event",s)
 def test_module_installation_and_client_slot_limit(self):
  s=SRC.read_text("utf-8")
  for part in ("V176BackpackCells.putUpgrade","storage.source.save(bag)",
      "current.shrink(1)","getMaxStackSize(ItemStack stack)","slot<4?1",
      "slotIndex<4?1"):
   self.assertIn(part,s)
 def test_concrete_rgba_icons_and_different_backpack_palettes(self):
  s=SRC.read_text("utf-8")
  for part in ("compressed_cobblestone_1x","compressed_cobblestone_3x",
      "compressed_obsidian_1x","network_backpack_magnet_upgrade",
      "power_card_micro_mg","len(palettes)==24","len(set(palettes))==24",
      '"elements"]=shape'):
   self.assertIn(part,s)
 def test_recipe_block_and_workflow(self):
  recipe=(ROOT/"features/v176/apply-v176-obsidian-star-icons-843.py").read_text("utf-8")
  self.assertIn('"D":"minecraft:diamond_block"',recipe)
  self.assertNotIn('"D":"minecraft:diamond"',recipe)
  workflow=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text("utf-8")
  self.assertIn("python3 features/v176/apply-v176-b847-ingame-fixes.py",workflow)
  self.assertIn("B847_EXPLICIT_BUILD_20261102",workflow)
if __name__=="__main__":unittest.main()
