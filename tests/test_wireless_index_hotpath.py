#!/usr/bin/env python3
"""Protect receiver FE budget/rollback and loaded-sender indexed lookups."""
from pathlib import Path
import unittest

SCRIPT=(Path(__file__).resolve().parents[1]/
        "features/wireless-energy/apply-wireless-index-hotpath.py").read_text()

class WirelessIndexHotpathContracts(unittest.TestCase):
 def test_only_one_index_availability_query_per_receiver_work_tick(self):
  self.assertIn("int remainingSupply=-1;",SCRIPT)
  self.assertIn("if(target==null)continue;",SCRIPT)
  self.assertIn("if(remainingSupply<0){",SCRIPT)
  self.assertIn("remainingSupply=(int)Math.min(MAX_TRANSFER,WirelessEnergyRuntime.available",SCRIPT)
  self.assertIn("if(remainingSupply<=0)break;",SCRIPT)
  self.assertIn("if(remainingBudget<=0||remainingSupply==0)break;",SCRIPT)
  self.assertIn("int offer=Math.min(remainingBudget,remainingSupply);",SCRIPT)
  self.assertIn("remainingSupply-=accepted;",SCRIPT)
 def test_commit_only_debits_sender_and_receiver_budget(self):
  self.assertIn("if(accepted==withdrawn){tx.commit();remainingBudget-=accepted;remainingSupply-=accepted;}",SCRIPT)
  self.assertNotIn("forceChunk(",SCRIPT)
  self.assertNotIn("setChunkForced(",SCRIPT)
 def test_unregister_visits_only_matching_network(self):
  self.assertIn("var bucket=server.get(sender.networkId());",SCRIPT)
  self.assertIn("if(bucket.isEmpty())server.remove(sender.networkId());",SCRIPT)
  # Old pattern is the deliberate fail-closed replacement anchor in this patch.\n  self.assertIn("for(var bucket:server.values())bucket.removeIf",SCRIPT)\n  self.assertIn("if(server.isEmpty())LOADED.remove(level.getServer());",SCRIPT)
 def test_fail_closed_on_source_drift(self):
  self.assertIn("assert source.count(old)==1",SCRIPT)

if __name__=="__main__":unittest.main()
