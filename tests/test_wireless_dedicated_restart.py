#!/usr/bin/env python3
"""Test-only real two-process wireless save/restore probe contract."""
import unittest
from pathlib import Path

SCRIPT=(Path(__file__).resolve().parents[1]/
        "features/wireless-energy/apply-wireless-dedicated-restart-probe.py").read_text()

class WirelessDedicatedRestartContracts(unittest.TestCase):
 def test_no_mock_server_and_real_saved_buffer(self):
  for v in (
     "ItemConduitRestartProbe.java",
     "if (PHASE.equals(\"before\")) createWirelessBefore(level);",
     "else createWirelessAfter(level);",
     "WIRELESS_FUNDED_FE = 12000L",
     "ObsidianNetwork.NETWORK_TRANSMITTER.get().defaultBlockState()",
     "source.energyHandler().insert((int)WIRELESS_FUNDED_FE,tx)",
     "source.stored()==WIRELESS_FUNDED_FE",
     "wireless_fe_persisted",
     "WirelessEnergyRuntime.available(",
     "WIRELESS_DEDICATED_PROCESS_RESTART_V1 PASS"):
   self.assertIn(v,SCRIPT,v)
 def test_receiver_only_placed_in_second_jvm_and_conservation(self):
  self.assertIn('(!PHASE.equals("after") || wirelessAfterTransferComplete(level))',SCRIPT)
  self.assertIn('ObsidianNetwork.NETWORK_RECEIVER.get().defaultBlockState()',SCRIPT)
  self.assertIn('ObsidianNetwork.BASIC_ENERGY_CELL.get().defaultBlockState()',SCRIPT)
  self.assertIn("source.stored()+cell.stored()",SCRIPT)
  self.assertIn("wireless_fe_conserved",SCRIPT)
  self.assertIn("wireless_fe_received_after_restart",SCRIPT)
 def test_fail_closed_and_no_runtime_chunk_forcing(self):
  self.assertIn('assert source.count(old)==1',SCRIPT)
  self.assertNotIn("forceChunk(",SCRIPT)
  self.assertNotIn("setChunkForced(",SCRIPT)

if __name__=="__main__":unittest.main()
