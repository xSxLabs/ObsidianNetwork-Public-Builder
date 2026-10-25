#!/usr/bin/env python3
"""v1.7.2: plain Create elevator / mechanical piston carries an actual suit."""
import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v172/apply-power-armor-create-carrier-138.py").read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")
class CreateArmorCarrier138(unittest.TestCase):
 def test_patch_syntax(self):ast.parse(PATCH)
 def test_no_custom_block_and_no_required_create_dependency(self):
  self.assertIn("BUILD138_CREATE_MOVING_PLATFORM_COMPAT",PATCH)
  self.assertIn("com.simibubi.create.content.contraptions.AbstractContraptionEntity",PATCH)
  self.assertNotIn(".getMethod(",PATCH)
  self.assertIn('lookup.findVirtual(base,"toLocalVector"',PATCH)
  self.assertIn('lookup.findVirtual(base,"toGlobalVector"',PATCH)
  self.assertNotIn("import com.simibubi.create",PATCH)
  self.assertNotIn('registerBlock(',PATCH)
  self.assertNotIn('registerSimpleBlockItem(',PATCH)
 def test_actual_create_platform_support_must_exist(self):
  for s in ("getBlocks","blocks.containsKey(underneath)","BlockPos.containing",
            "Math.abs(localFeet.y","return new Attachment(contraption.getUUID(),feet)"):
   self.assertIn(s,PATCH,s)
 def test_motion_up_down_on_client_tracked_real_stand(self):
  for s in ("EntityTickEvent.Post","getContraption","toLocalVector",
            "toGlobalVector","stand.setPos(dest.x,dest.y,dest.z)",
            "world.noCollision(stand,stand.getBoundingBox().move(delta))",
            "world.hasChunkAt(BlockPos.containing(dest))"):
   self.assertIn(s,PATCH,s)
 def test_original_suit_items_never_copied(self):
  for bad in ("setItemSlot(","ItemStack.EMPTY","addFreshEntity(","startRiding(",
              "forceChunk(","setNoGravity(false)"):
   self.assertNotIn(bad,PATCH,bad)
  self.assertIn("PowerArmorRecallIndex.get(level.getServer()).index(stand,level,owner)",PATCH)
  self.assertIn("ATTACHED.remove(stand.getUUID())",PATCH)
 def test_ci_after_recall(self):
  self.assertLess(WF.index("python3 features/v172/apply-power-armor-recall-last-worn-131.py"),
                  WF.index("python3 features/v172/apply-power-armor-create-carrier-138.py"))
  self.assertIn("BUILD138_CREATE_PLATFORM_AUTOMATIC PASS",WF)
if __name__=="__main__":unittest.main()
