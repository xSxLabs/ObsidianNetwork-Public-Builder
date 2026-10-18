#!/usr/bin/env python3
"""Contract for real loaded-sender and unknown network ID isolation GameTest."""
import unittest
from pathlib import Path

SRC=(Path(__file__).resolve().parents[1]/
     "features/wireless-energy/inject-wireless-source-isolation-gametest.py").read_text()

class WirelessSourceIsolationContracts(unittest.TestCase):
 def test_unload_and_reload_are_observed_by_real_runtime(self):
  for snippet in (
     "WirelessEnergyRuntime.unregister(crossTx)",
     "WirelessEnergyRuntime.register(crossTx)",
     "WIRELESS source detached from loaded registry is unavailable",
     "WIRELESS detached transmitter cannot supply FE",
     "WIRELESS detached transmitter retains all stored FE",
     "WIRELESS reloaded transmitter becomes available without FE loss",
     "WIRELESS_LOADED_SOURCE_ISOLATION_V1 PASS"):
   self.assertIn(snippet,SRC,snippet)
 def test_unknown_network_fails_closed_without_changing_buffer(self):
  for snippet in (
     "crossTx.selectNetwork(absentId)",
     "validId.equals(crossTx.networkId())",
     "WIRELESS non-existent network cannot withdraw FE",
     "crossTx.stored()==12000",
     "WIRELESS_LOADED_SOURCE_ISOLATION_V1 INJECTED"):
   self.assertIn(snippet,SRC,snippet)
 def test_unrelated_conservation_proof_is_not_removed(self):
  self.assertIn("assert s.count(anchor)==1",SRC)
  self.assertNotIn("forceChunk(",SRC)
  self.assertNotIn("setChunkForced(",SRC)

if __name__=="__main__":
 unittest.main()
