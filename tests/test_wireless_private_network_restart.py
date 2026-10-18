#!/usr/bin/env python3
"""Ensure dedicated two-process test covers private saved networks and FE isolation.

The standalone probe modifies *only* the CI-generated restart subscriber. It
must never be copied into the distributable mod JAR.
"""
from pathlib import Path
import unittest
import tempfile
import subprocess
import sys

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
 def test_combined_patch_apply_to_real_restart_fixture(self):
  root=Path(__file__).resolve().parents[1]
  base=root/"features/wireless-energy/apply-wireless-dedicated-restart-probe.py"
  private=root/"features/wireless-energy/apply-wireless-private-network-restart-probe.py"
  with tempfile.TemporaryDirectory() as directory:
   work=Path(directory)
   probe=work/"tests/integration/ItemConduitRestartProbe.java"
   probe.parent.mkdir(parents=True)
   probe.write_text((root/"tests/integration/ItemConduitRestartProbe.java").read_text())
   for patch in (base,private):
    result=subprocess.run([sys.executable,str(patch)],cwd=work,capture_output=True,text=True)
    self.assertEqual(result.returncode,0,
      f"{patch.name} failed: stdout={result.stdout} stderr={result.stderr}")
   generated=probe.read_text()
   for marker in (
     "WIRELESS_PRIVATE_NETWORK_DEDICATED_RESTART_V2",
     "WIRELESS_PRIVATE_SAVEDDATA_RESTART_V2 PASS",
     "WIRELESS_PRIVATE_NETWORK_ISOLATION_V2 PASS",
     "WIRELESS_DEDICATED_PROCESS_RESTART_V1 PASS",
     "source.stored()+cell.stored()",
     "data.setDirty();"):
    self.assertIn(marker,generated)
 def test_existing_exact_fe_and_stop_start_preserved(self):
  self.assertIn("apply-wireless-dedicated-restart-probe.py",PATCH)
  self.assertIn("assert s.count(old)==1",PATCH)
  self.assertIn("report.put(\"wireless_fe_conserved\",true)",PATCH)
  self.assertNotIn("forceChunk(",PATCH)

if __name__=="__main__":unittest.main()
