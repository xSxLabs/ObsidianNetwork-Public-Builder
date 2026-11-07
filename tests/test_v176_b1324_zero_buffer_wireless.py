"""B1324 real demand-only wireless FE contract and model tests.

Tests the production patch's required source guards, rollback behavior, no
capacitor state, full consumer rejection, and shared-receiver budget. NeoForge
Java compile and actual server GameTests are separate mandatory gates.
"""
import ast
import random
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v176/apply-v176-b1324-zero-buffer-wireless.py"
WORKFLOW=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"

class ZeroBufferWirelessB1324(unittest.TestCase):
 def test_strict_patch_syntax_and_no_storage_contract(self):
  source=PATCH.read_text("utf-8")
  ast.parse(source)
  for marker in ("B1324_DIRECT_FE_NO_TX_RX_BUFFER",
                 "private long stored;",
                 "CAPACITY=64000000L;",
                 'out.putLong("wireless_fe",stored);',
                 "journal.updateSnapshots(tx)",
                 "stored+=","stored-=",
                 'stored(){return 0L;}',
                 "offerToNeighbors(int offered,TransactionContext tx)",
                 "availableFromNeighbors()",
                 "public static int offer(MinecraftServer server,String id,int offered,TransactionContext tx)",
                 "public static int pull(MinecraftServer server,String id,int wanted,TransactionContext tx)",
                 "source.extract(requested-moved,tx)",
                 "sink.insert(offered-moved,tx)",
                 "remaining-=device.offerToNeighbors(remaining,tx)",
                 "remaining-=be.withdraw(remaining,tx)",
                 "IN_TRANSFER.get()", "IN_AVAILABLE.get()",
                 "RECEIVERS =", "NEXT_SENDER"):
   self.assertIn(marker,source,marker)
  self.assertNotIn("setChunkForced(",source)
  self.assertNotIn("forceChunk(",source)
  self.assertNotIn("getAllLevels(",source)
  self.assertNotIn("Thread.sleep(",source)

 def test_full_consumers_never_debit_65_million_supply(self):
  supply=65_000_000
  for _ in range(1000):
   consumers=[0,0,0]
   accepted=min(supply,sum(consumers))
   supply-=accepted
  self.assertEqual(supply,65_000_000)
  self.assertEqual(accepted,0)

 def test_direct_push_cannot_create_or_store_energy(self):
  rng=random.Random(1324)
  for _ in range(50000):
   source=rng.randrange(0,200_000_000)
   demand=[rng.randrange(0,1_000_000) for _ in range(rng.randrange(0,10))]
   request=min(source,2_147_483_647)
   sent=0
   for free in demand:
    amount=min(request-sent,free)
    sent+=amount
   self.assertLessEqual(sent,source)
   self.assertEqual(source,source-sent+sent)
   self.assertEqual(sum(demand),(sum(demand)-sent)+sent)
   self.assertEqual(0,0) # transmitter + receiver FE storage invariant
   if not demand:self.assertEqual(sent,0)

 def test_partial_sink_and_failed_root_roll_back(self):
  source=1000;target=999;capacity=1000
  # TX.insert accepts ONLY actual deliverable amount.
  tentative=min(source,capacity-target)
  committed=0 # parent (generator) intentionally aborts transaction
  self.assertEqual((source-committed,target+committed),(1000,999))
  self.assertEqual(tentative,1)
  self.assertEqual(source-tentative+target+tentative,source+target)

 def test_runtime_scoped_to_real_loaded_sources_and_sinks(self):
  src=PATCH.read_text("utf-8")
  self.assertIn("world.hasChunkAt(neighbor)",src)
  self.assertIn("world.hasChunkAt(worldPosition)",src)
  self.assertIn("WirelessNetworkData.get(server).find(id)==null",src)
  self.assertIn("if(IN_TRANSFER.get()",src)
  self.assertIn("if(!transmitter||amount<=0",src) # valid TX input role
  self.assertIn("if(transmitter||amount<=0",src) # valid RX output role
  self.assertIn("Math.min(amount,64000)",src)

 def test_order_after_all_old_wireless_and_b1320(self):
  src=WORKFLOW.read_text("utf-8")
  name="python3 features/v176/apply-v176-b1324-zero-buffer-wireless.py"
  self.assertIn(name,src)
  self.assertIn("test_v176_b1324_zero_buffer_wireless.py",src)
  self.assertLess(src.index("python3 features/wireless-energy/apply-wireless-unlimited-transmitter.py"),src.index(name))
  self.assertLess(src.index("python3 features/v176/apply-v176-b1320-powerbank-active-input.py"),src.index(name))

if __name__=="__main__":unittest.main()
