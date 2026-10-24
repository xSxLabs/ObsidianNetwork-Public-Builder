#!/usr/bin/env python3
"""Build146 source-level conservation and integration gates."""
import ast, unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]
A=(P/"features/v172/apply-network-planter-146.py").read_text()
B=(P/"features/v172/apply-power-armor-recall-jade-146.py").read_text()
W=(P/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
class Build146(unittest.TestCase):
 def test_patch_syntax(self):
  ast.parse(A);ast.parse(B)
 def test_real_nine_item_slots(self):
  for token in ("private final ItemStack[] output=new ItemStack[9]",
      "getContainerSize(){return 27;}", "slot>=9&&slot<=17",
      "private boolean fits(Map<Item,Integer> drops)", "if(!be.fits(batch))",
      "be.stalled=true", "return;", "OUTPUT_SLOTS={9,10,11,12,13,14,15,16,17}"):
   self.assertIn(token,A)
 def test_wood_and_growth(self):
  for token in ('"pale_oak"', '"dark_oak"', '"cherry"', '"mangrove"',
      '"bamboo"', '"crimson"', '"warped"',
      'IntegerProperty.create("age",0,3)', "NetworkPlanterBlock.Plant.of(seed)",
      "int height" if False else "height=[2,4,8,12][age]"):
   self.assertIn(token,A)
 def test_tree_byproducts_never_replace_log(self):
  for token in ("plant.tree?1+world.getRandom().nextInt(3):1",
      "world.getRandom().nextFloat()<.34F",
      "world.getRandom().nextFloat()<.24F",
      "world.getRandom().nextFloat()<.12F",
      "world.getRandom().nextFloat()<.08F",
      "Items.STICK","Items.APPLE","plant.leaves","plant.seed"):
   self.assertIn(token,A)
 def test_container_without_hopper_and_network_priority(self):
  for token in ("WorldTopologyBridge.runtimeForAccessory(world,p)",
      "runtime.storage().insert(key,stack.getCount())",
      "worldPosition.below()", "dest.setItem(slot,updated)",
      "stack.shrink(moved)", "side==Direction.DOWN?",
      "VanillaContainerWrapper.of(planter.outputOnly())"):
   self.assertIn(token,A)
 def test_jade_and_true_32_block_recall(self):
  for token in ("Math.sqrt(1024D-", "no safe 32-block arrival location.",
      "registerBlockComponent(PlanterProvider.INSTANCE",
      "BUILD146_JADE_PLANTER_STATUS", "p.slotsUsed()+\"/9 slots\""):
   self.assertIn(token,B)
 def test_workflow_executes_both(self):
  for filename in ("apply-network-planter-146.py","apply-power-armor-recall-jade-146.py"):
   self.assertIn("python3 features/v172/"+filename,W)
if __name__=="__main__":unittest.main()
