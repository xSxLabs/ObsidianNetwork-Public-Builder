"""Buildlock preflight for B878/B879: server-independent renderer and asset contracts."""
from pathlib import Path
import ast
import unittest

ROOT=Path(__file__).resolve().parents[1]
FEATURE=ROOT/"features"/"v176"

class IngameRenderAndIconContracts(unittest.TestCase):
 def script(self,name):
  p=FEATURE/name
  s=p.read_text(encoding="utf-8")
  ast.parse(s,filename=str(p))
  return s

 def test_weapon_mount_is_along_raised_arm(self):
  s=self.script("apply-v176-b878-right-arm-first-person-mount.py")
  self.assertIn("addBox(-0.9F,5.0F,-3.5F,1.8F,13.0F,1.8F)",s)
  self.assertIn("RenderHandEvent event",s)
  self.assertIn("InteractionHand.MAIN_HAND",s)
  self.assertIn("V176AttackPoseContext.aim(state)",s)
  self.assertIn("state.rightArmPose=HumanoidModel.ArmPose.SPYGLASS",s)
  self.assertIn("state.setRenderData(V176AttackRenderState.ACTIVE,armed)",s)
  self.assertIn("state.setRenderData(V176AttackRenderState.TIER,tier)",s)
  self.assertIn("PLAYER_RENDER_ARMED.get()",s)
  # The old muzzle geometry occurs intentionally as an exact search anchor.
  # Verify the replacement is present; don't reject the patch's old-side text.
  self.assertIn("No square black muzzle block or giant end cap.",s)
  # The replacement is constrained to createBarrel, not brittle B745 lines.
  self.assertIn('s.index(" private static ModelPart createBarrel(){")',s)
  self.assertIn('old_builder.count(".addBox(")>=2',s)
  self.assertIn("B889_BARREL_STRUCTURE_DRIFT",s)
  self.assertNotIn("B878_DRIFT', 'client/V176MicroMgVisualClient",s)

 def test_card_and_vanilla_model_targets(self):
  s=self.script("apply-v176-b879-vanilla-block-icons-card-backpack-gui.py")
  self.assertIn('card=Image.open(cards/"power_card_speed.png")',s)
  self.assertIn('"layer0":"obsidiannetwork:item/power_card_micro_mg"',s)
  self.assertIn('"minecraft:block/cobblestone"',s)
  self.assertIn('"minecraft:block/obsidian"',s)
  self.assertIn('"minecraft:composite"',s)
  self.assertIn('_badge_small.png',s)
  self.assertIn('scale(0.72F,0.72F)',s)
  self.assertIn('this.menu.slots.indexOf(slot)',s)
  self.assertIn('menuIndex>=4 && menuIndex<49',s)
  self.assertNotIn('slot.index>=4 && slot.index<49',s)

 def test_workflow_order_and_buildlock(self):
  w=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
  names=["apply-v176-b862-worn-micro-mg-render-gate.py",
         "apply-v176-b863-micro-mg-upgrade-icon.py",
         "apply-v176-b878-right-arm-first-person-mount.py",
         "apply-v176-b879-vanilla-block-icons-card-backpack-gui.py"]
  indices=[w.index("python3 features/v176/"+n) for n in names]
  self.assertEqual(indices,sorted(indices))
  self.assertIn("B879_NOT_VANILLA_BLOCK_TEXTURE_",w)
  self.assertIn("B878_MISSING_ARMOR_POSE_CONTEXT",w)
  # New commits must remain staged until the user explicitly requests build.
  self.assertNotIn("B878_EXPLICIT_BUILD_20261102",w)
  self.assertNotIn("B879_EXPLICIT_BUILD_20261102",w)

if __name__=="__main__":
 unittest.main()
