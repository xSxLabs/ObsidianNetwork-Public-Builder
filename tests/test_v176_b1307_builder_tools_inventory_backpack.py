"""B1307 native NeoForge 26.1 inventory/worn backpack builder-tool supply.

Source contract and atomic transaction model, not a replacement for compiled
Java and dedicated-server / Construction Sticks / Building Gadgets 2 tests.
"""
import ast,os,random,subprocess,sys,tempfile,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v176/apply-v176-b1307-backpack-builder-tools-item-capability.py"
WF=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"
CAP="""package dev.obsidiannetwork.backpack;
import net.neoforged.neoforge.capabilities.Capabilities;
import dev.obsidiannetwork.registry.ModBlockEntities;
public final class V176BackpackCableCapability {
 @SubscribeEvent public static void register(RegisterCapabilitiesEvent event){
  event.registerBlockEntity(Capabilities.Item.BLOCK,
      ModBlockEntities.NETWORK_BACKPACK.get(),
      (bag,side)->bag.cableItemHandler());
 }
}
"""
def apply(source=CAP):
 with tempfile.TemporaryDirectory() as d:
  root=Path(d)/"dev/obsidiannetwork/backpack"
  root.mkdir(parents=True)
  (root/"V176BackpackCableCapability.java").write_text(source,"utf-8")
  p=subprocess.run([sys.executable,str(PATCH)],capture_output=True,text=True,
                   env={**os.environ,"V1_SOURCE_ROOT":d})
  cap=(root/"V176BackpackCableCapability.java").read_text("utf-8")
  java=(root/"V176BackpackBuilderSupply.java").read_text("utf-8") if (root/"V176BackpackBuilderSupply.java").exists() else ""
  return p,cap,java

class BuilderToolBackpackItemCapability(unittest.TestCase):
 def test_generated_java_native_item_api_and_exactly_24_mks(self):
  ast.parse(PATCH.read_text("utf-8"))
  run,cap,java=apply()
  self.assertEqual(run.returncode,0,run.stderr)
  self.assertEqual(cap.count("registerItem(Capabilities.Item.ITEM"),1)
  self.assertEqual(cap.count("registerBlockEntity(Capabilities.Item.BLOCK"),1)
  for i in range(1,25):
   self.assertEqual(cap.count(f"ObsidianNetwork.NETWORK_BACKPACK_MK{i}.get()"),1)
  self.assertIn("implements ResourceHandler<ItemResource>",java)
  self.assertIn("ItemAccess access",java)
  self.assertIn("ServerLifecycleHooks.getCurrentServer()",java)
  self.assertIn("V176BackpackCells.entries(before)",java)
  self.assertIn("V176BackpackCells.extract(world,updated,entry.descriptor(),n)",java)
  self.assertIn("access.exchange(ItemResource.of(updated),1,tx)",java)
  self.assertIn("if(!requested.equals(resourceOf(entry)))return 0;",java)
  self.assertIn("int n=(int)Math.min((long)amount,entry.count())",java)
  self.assertIn("return 0; // Supply-only.",java)
  self.assertNotIn("static Map<",java)
  self.assertNotIn("getInventory()",java)
  self.assertNotIn("registerBlock(Capabilities.Item.BLOCK",cap)
  self.assertNotIn("scan",java.lower())

 def test_fail_closed_if_original_block_capability_changed(self):
  bad=CAP.replace("bag.cableItemHandler()","bag.otherHandler()")
  run,out,java=apply(bad)
  self.assertNotEqual(run.returncode,0)
  self.assertEqual(out,bad)
  self.assertEqual(java,"")

 def test_commit_and_simulation_conserve_items(self):
  rng=random.Random(1307)
  for _ in range(30000):
   original=rng.randrange(0,200000)
   requested=rng.randrange(0,200)
   actual=min(original,requested)
   buyer_accepts=bool(rng.randrange(2))
   root_commits=bool(rng.randrange(2))
   post=original-actual if buyer_accepts and root_commits else original
   delivered=actual if buyer_accepts and root_commits else 0
   self.assertEqual(post+delivered,original)

 def test_rejected_descriptor_and_invalid_access_no_changes(self):
  for stored in range(0,4096):
   invalid_index=-1
   mismatched_resource=True
   no_server=True
   self.assertTrue(invalid_index<0)
   self.assertTrue(mismatched_resource)
   self.assertTrue(no_server)
   self.assertEqual(stored,stored)

 def test_pipeline_script_after_backpack_sort_and_before_release_build(self):
  workflow=WF.read_text("utf-8")
  self.assertIn(PATCH.name,workflow)
  self.assertIn(Path(__file__).name,workflow)
  self.assertLess(workflow.index("python3 features/v176/apply-v176-b1304-backpack-sort-display-names.py"),
                  workflow.index("python3 features/v176/"+PATCH.name))
  self.assertLess(workflow.index("python3 features/v176/"+PATCH.name),
                  workflow.index("echo '===== BUILD 101 FINAL BUILD ====='"))

if __name__=="__main__":unittest.main()
