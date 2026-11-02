"""B862 buildlock source contracts: shared render-state + backpack 3D / GUI safety.
Tests are pure Python and do not reconstruct Minecraft or start a CI build.
"""
import ast
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]

class V176StagedFixContracts(unittest.TestCase):
 def read(self,leaf):
  return (ROOT/"features"/"v176"/leaf).read_text(encoding="utf-8")

 def test_staged_patch_python_syntax(self):
  for name in ("apply-v176-b857-backpack-equipment-gui-3d.py",
               "apply-v176-b858-player-renderstate-arm-layer.py",
               "apply-v176-b862-worn-micro-mg-render-gate.py",
               "apply-v176-b863-micro-mg-upgrade-icon.py"):
   with self.subTest(name=name):
    ast.parse(self.read(name),filename=name)

 def test_final_arm_and_barrel_share_avatar_signal(self):
  state=self.read("apply-v176-b858-player-renderstate-arm-layer.py")
  worn=self.read("apply-v176-b862-worn-micro-mg-render-gate.py")
  self.assertIn("registerAvatarEntityModifier(",state)
  self.assertIn("V176AttackRenderState.ACTIVE",state)
  self.assertIn("V176AttackRenderState.ACTIVE",worn)
  self.assertIn("weaponInstalled(Player player)",worn)
  self.assertIn("PowerArmorRuntime.SLOTS",worn)
  self.assertIn("markLayerSubmitted(state.id)",worn)
  # Prevent the old incompatible B843 assertion from returning after B858.
  self.assertIn('assert "V176AttackRenderState.ACTIVE" in src',worn)
  self.assertNotIn('assert "V176MicroMgVisualClient.armedForAttack(player)" in src',worn)
  self.assertIn("this.rightArm.xRot=-1.535F;",self.read("apply-v176-b847-ingame-fixes.py"))

 def test_backpack_no_magnet_on_blank_click(self):
  bag=self.read("apply-v176-b857-backpack-equipment-gui-3d.py")
  self.assertIn("Always swallow clicks in the 45-slot item list",bag)
  self.assertIn("return true;'''",bag)
  self.assertIn("EquipmentCellStore.CAPACITY",bag)
  self.assertIn("EquipmentEligibility.isEquipment(d.key())",bag)
  self.assertIn('"parent":"minecraft:block/cube_all"',bag)
  self.assertIn("ITEM COUNT:",bag)
  self.assertIn("handleContainerInput(",bag)
  self.assertIn("ContainerInput.QUICK_MOVE",bag)
  self.assertIn("return stack.getItem() instanceof StorageCellItem",bag)
  self.assertIn("||stack.getItem() instanceof EquipmentCellItem",bag)

 def test_explicit_buildlock_has_no_new_marker(self):
  # Only a user-approved EXPLICIT commit triggers slow jobs.
  workflow=(ROOT/".github"/"workflows"/"networkstorage-v1.7-clean.yml").read_text()
  self.assertIn("apply-v176-b857-backpack-equipment-gui-3d.py",workflow)
  self.assertIn("apply-v176-b858-player-renderstate-arm-layer.py",workflow)
  self.assertIn("apply-v176-b862-worn-micro-mg-render-gate.py",workflow)
  self.assertIn("apply-v176-b863-micro-mg-upgrade-icon.py",workflow)
  self.assertLess(workflow.index("python3 features/v176/apply-v176-b857-backpack-equipment-gui-3d.py"),
                  workflow.index("python3 features/v176/apply-v176-b862-worn-micro-mg-render-gate.py"))

if __name__=="__main__":
 unittest.main()
