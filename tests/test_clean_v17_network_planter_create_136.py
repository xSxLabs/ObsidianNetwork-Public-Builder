#!/usr/bin/env python3
"""v1.7.2 Create and Network Planter safety gates."""
import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PL=(ROOT/"features/v172/apply-network-planter-135.py").read_text()
CR=(ROOT/"features/v172/apply-power-armor-create-platform-136.py").read_text()
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
class Build136(unittest.TestCase):
 def test_python_syntax(self):ast.parse(PL);ast.parse(CR)
 def test_network_direct_only_accepts_real_insert(self):
  for x in ("runtimeForAccessory(level,cablePos)","NETWORK_CABLE.get()",
            "runtime.storage().insert(key,output.getCount())","if(written>0L)",
            "output.shrink((int)Math.min(written,output.getCount()))"):
   self.assertIn(x,PL)
 def test_persistent_hopper_fallback(self):
  for x in ('out.store("soil",ItemStack.CODEC','out.store("seed",ItemStack.CODEC',
            'out.store("output",ItemStack.CODEC','in.read("output",ItemStack.CODEC)',
            "VanillaContainerWrapper.of(planter)","Capabilities.Item.BLOCK",
            "side==Direction.DOWN","Containers.dropItemStack","preRemoveSideEffects"):
   self.assertIn(x,PL)
 def test_speed_upgrade_is_effective_and_limited(self):
  self.assertIn("Math.min(16-upgrades,held.getCount())",PL)
  self.assertIn("600D/(1D+0.70D*upgrades)",PL)
 def test_create_carries_original_and_updates_recall(self):
  for x in ("V172_CREATE_MOVING_PLATFORM",
            "com.simibubi.create.content.contraptions.AbstractContraptionEntity",
            "getContraption","getBlocks","toGlobalVector",
            "suit.setPos(target.x,target.y,target.z)",
            "PowerArmorRecallIndex.get(world.getServer()).index"):
   self.assertIn(x,CR)
  for x in ("new ArmorStand(","addFreshEntity(","suit.setItemSlot("):
   self.assertNotIn(x,CR)
 def test_correct_branch_and_pipeline(self):
  self.assertIn("branches: [v1.7, v1.7.2, v1.7.3]",WF)
  self.assertIn("python3 features/v172/apply-network-planter-135.py",WF)
  self.assertIn("python3 features/v172/apply-power-armor-create-platform-136.py",WF)
if __name__=="__main__":unittest.main()
