#!/usr/bin/env python3
"""B1861 v20 water/lava, chest/cargo, minecart and no-duplication contracts."""
import ast,os,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"features/v178/apply-v178-v20-b1861-fluid-container-minecarts.py"
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text("utf-8")

class MiningFluidContainersV20(unittest.TestCase):
 def test_patch_registered_after_claim_painter(self):
  s=SCRIPT.read_text("utf-8");ast.parse(s)
  newer="python3 features/v178/apply-v178-v20-b1861-fluid-container-minecarts.py"
  earlier="python3 features/v178/apply-v178-v19-b1855-claim-overlay.py"
  self.assertIn(newer,WF)
  self.assertIn(earlier,WF)
  self.assertLess(WF.index(earlier),WF.index(newer))
  self.assertIn("xSxLabs-Network-Storage-1.7.8-v20.jar",WF)
  self.assertIn("exactly(old,new)",s)
  self.assertIn("exactly(old2,new2)",s)
  self.assertNotIn("assert s.count(old)==1",s)
  self.assertNotIn("assert s.count(old2)==1",s)
  self.assertIn("xsxlabs-network-storage-1.7.8-v20",WF)
 def test_transaction_holds_all_loot_before_removal(self):
  s=SCRIPT.read_text("utf-8")
  for key in ("b1861Contents(inventory)","b1861StoreAll(contents,tx)",
      "if(!fits)return; // no break or chest mutation until ALL loot fits",
      "if(inventory!=null)inventory.clearContent()",
      "if(!world.destroyBlock(target,false)){",
      "inventory.setItem(i,contents[i]);",
      "cart.getPickResult()","b1861StoreAll(saved,tx)",
      "cart.discard();","!cart.getPassengers().isEmpty()"):
   self.assertIn(key,s,key)
  self.assertLess(s.index("if(fits)fits=machine.b1861StoreAll(contents,tx);"),
                  s.index("if(inventory!=null)inventory.clearContent()"))
 def test_fluid_budgets_and_owner_guards(self):
  s=SCRIPT.read_text("utf-8")
  for key in ("net.minecraft.world.level.block.LiquidBlock",
      "world.setBlock(target,net.minecraft.world.level.block.Blocks.AIR.defaultBlockState(),3)",
      "V178Claims.mayMachineMine(world,target,machine.owner)",
      "if(!world.hasChunkAt(target))return",
      "canMineThisTick(world)","budget(world)",
      "energy.set(Math.max(0,energy.getAmountAsInt()-ENERGY_PER_BLOCK))"):
   # Some original invariants are checked by script asserts rather than edits.
   self.assertIn(key,s,key)
 def test_generated_java(self):
  root=os.environ.get("V1_SOURCE_ROOT")
  if not root:self.skipTest("requires GitHub CI reconstructed source")
  s=(Path(root)/"dev/obsidiannetwork/mining/V178MiningBuilderBE.java").read_text("utf-8")
  for key in ("b1861Minecart(world,target)","cart.getPickResult()",
        "b1861Contents(inventory)","machine.b1861StoreAll(contents,tx)",
        "world.setBlock(target,net.minecraft.world.level.block.Blocks.AIR.defaultBlockState(),3)",
        "if(inventory!=null)inventory.clearContent()",
        "if(!world.destroyBlock(target,false)){"):
   self.assertIn(key,s,key)

if __name__=="__main__": unittest.main()
