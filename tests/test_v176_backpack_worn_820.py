"""26.1 client submit-node and optional Curios rendering source gates."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class Worn820(unittest.TestCase):
 def test_new_submit_api_not_removed_legacy(self):
  s=(ROOT/"features/v176/apply-v176-backpack-worn-render-820.py").read_text("utf-8")
  for fragment in ("RenderPlayerEvent.Post<?>","getSubmitNodeCollector()",
                   "new ItemStackRenderState()","getItemModelResolver().updateForLiving",
                   "model.submit(pose", "ItemDisplayContext.FIXED"):
   self.assertIn(fragment,s)
  self.assertNotIn("renderStatic(",s)
 def test_render_works_in_chest_and_optional_curios(self):
  s=(ROOT/"features/v176/apply-v176-backpack-worn-render-820.py").read_text("utf-8")
  self.assertIn("EquipmentSlot.CHEST",s)
  self.assertIn("ModList.get().isLoaded",s)
  self.assertIn("getStacksHandler(\\"back\\")",s)
  self.assertIn("NetworkBackpackItem",s)
 def test_build_stage(self):
  w=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text("utf-8")
  self.assertLess(w.index("python3 features/v176/apply-v176-backpack-meter-819.py"),
                  w.index("python3 features/v176/apply-v176-backpack-worn-render-820.py"))
if __name__=="__main__":
 unittest.main()
