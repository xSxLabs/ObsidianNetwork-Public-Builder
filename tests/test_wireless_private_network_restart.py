#!/usr/bin/env python3
"""Ensure dedicated two-process test covers private saved networks and FE isolation.

The standalone probe modifies *only* the CI-generated restart subscriber. It
must never be copied into the distributable mod JAR.
"""
from pathlib import Path
import unittest

PATCH=(Path(__file__).resolve().parents[1]/
       "features/wireless-energy/apply-wireless-private-network-restart-probe.py").read_text()

class WirelessPrivateNetworkRestartContracts(unittest.TestCase):
 def test_real_saveddata_owner_name_and_mask_check(self):
  for marker in (
    'getDeclaredField("networks")',
    "data.setDirty();",
    "dev.obsidiannetwork.wireless.WirelessNetworkData.get(level.getServer())",
    "Private Solar Alpha",
    "Private Machine Beta",
    "one.chargingMask()==17",
    "two.chargingMask()==6",
    "one.owner().equals(WIRELESS_OWNER_1)",
    "two.owner().equals(WIRELESS_OWNER_2)",
    'WIRELESS_PRIVATE_SAVEDDATA_RESTART_V2 PASS'):
   self.assertIn(marker,PATCH,marker)
 def test_receiver_rejects_wrong_private_network_and_resumes_after_rebind(self):
  for marker in (
    "source.selectNetwork(WIRELESS_PRIVATE_ID);",
    "receiverBe.selectNetwork(WIRELESS_OTHER_ID);",
    "source.stored()==WIRELESS_FUNDED_FE && sink.stored()==0",
    "receiver.selectNetwork(WIRELESS_PRIVATE_ID);",
    "wirelessIsolationVerified=true;",
    "wirelessAfterTransferComplete(level)",
    'WIRELESS_PRIVATE_NETWORK_ISOLATION_V2 PASS'):
   self.assertIn(marker,PATCH,marker)
 def test_existing_exact_fe_and_stop_start_preserved(self):
  self.assertIn("apply-wireless-dedicated-restart-probe.py",PATCH)
  self.assertIn("assert s.count(old)==1",PATCH)
  self.assertIn("report.put(\"wireless_fe_conserved\",true)",PATCH)
  self.assertNotIn("forceChunk(",PATCH)

if __name__=="__main__":unittest.main()
