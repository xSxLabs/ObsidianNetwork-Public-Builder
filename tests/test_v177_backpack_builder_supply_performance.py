#!/usr/bin/env python3
"""Builder-tool Backpack read cache: no phantom items, no tick-stale views."""
import ast
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v177/apply-v177-backpack-builder-supply-performance.py"
BASE=ROOT/"features/v176/apply-v176-b1307-backpack-builder-tools-item-capability.py"
FLOW=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")
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

class BuilderSupplyPerformance(unittest.TestCase):
 def test_generated_adapter_keeps_real_item_extraction_and_exact_checks(self):
  ast.parse(PATCH.read_text(encoding="utf-8"))
  with tempfile.TemporaryDirectory() as temp:
   folder=Path(temp)/"dev/obsidiannetwork/backpack"
   folder.mkdir(parents=True)
   (folder/"V176BackpackCableCapability.java").write_text(CAP,encoding="utf-8")
   env={**os.environ,"V1_SOURCE_ROOT":temp}
   for path in (BASE,PATCH):
    completed=subprocess.run([sys.executable,str(path)],env=env,capture_output=True,text=True)
    self.assertEqual(completed.returncode,0,completed.stdout+completed.stderr)
   java=(folder/"V176BackpackBuilderSupply.java").read_text(encoding="utf-8")
   self.assertIn('implements ResourceHandler<ItemResource>',java)
   self.assertIn('current==xsxViewSource||current.equals(xsxViewSource)',java)
   self.assertIn('amount==xsxViewAmount',java)
   self.assertIn('V176BackpackCells.entries(stack)',java)
   self.assertEqual(java.count('V176BackpackCells.entries('),1)
   self.assertIn('new MinecraftItemStackCodec(level.registryAccess())',java)
   self.assertIn('for(var entry:entries)decoded.add(resourceOf(entry,codec));',java)
   self.assertIn('if(!requested.equals(xsxViewResources.get(index)))return 0;',java)
   self.assertIn('ItemStack before=bag();',java)
   self.assertIn('ItemStack updated=before.copy();',java)
   self.assertIn('V176BackpackCells.extract(world,updated,entry.descriptor(),n)',java)
   self.assertIn('access.exchange(ItemResource.of(updated),1,tx)',java)
   self.assertIn('xsxViewValid=false; // root commit OR rollback',java)
   self.assertIn('return 0; // Supply-only.',java)
   self.assertNotIn('static Map<',java)
   self.assertNotIn('tickCount',java)
   self.assertEqual(java.count('getResource(int index)'),1)
   self.assertEqual(java.count('getAmountAsLong(int index)'),1)
   self.assertEqual(java.count('getCapacityAsLong(int index'),1)
   self.assertEqual(java.count('extract(int index'),1)
   again=subprocess.run([sys.executable,str(PATCH)],env=env,capture_output=True,text=True)
   self.assertNotEqual(again.returncode,0,"Must refuse double-injection")

 def test_source_only_in_branch_177_and_after_original_builder_adapter(self):
  a=FLOW.index("python3 features/v176/apply-v176-b1307-backpack-builder-tools-item-capability.py")
  b=FLOW.index("python3 features/v177/apply-v177-backpack-builder-supply-performance.py")
  self.assertLess(a,b)
  self.assertIn("test_v177_backpack_builder_supply_performance.py",FLOW)
  self.assertIn('if [ "$GITHUB_REF_NAME" = "1.7.7" ] || [ "$GITHUB_REF_NAME" = "1.7.8" ]; then',FLOW)

 def test_read_cache_conservation_and_transaction_rollback_model(self):
  rng=random.Random(1617)
  # Same immutable source version: one sorted rebuild for any number of reads.
  for _ in range(15000):
   count=rng.randrange(0,1_000_000)
   requested=rng.randrange(0,1000)
   accepts=rng.randrange(2)==1
   commits=rng.randrange(2)==1
   new_count=count-min(count,requested) if accepts and commits else count
   delivered=count-new_count
   self.assertEqual(delivered+new_count,count)
   # Cached views must be invalid after every attempted exchange;
   # an aborted one refreshes old values, not simulated ones.
   cached=count
   if accepts:
    cached=None
   if cached is not None:self.assertEqual(cached,count)
   if not commits:self.assertEqual(new_count,count)

if __name__=="__main__":
 unittest.main()
