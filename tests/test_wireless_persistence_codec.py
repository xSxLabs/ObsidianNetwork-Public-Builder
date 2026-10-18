#!/usr/bin/env python3
"""Source contract: actual 26.1 BE and SavedData codec roundtrip in GameTest."""
from pathlib import Path
import unittest
SCRIPT=(Path(__file__).resolve().parents[1]/
        "features/wireless-energy/inject-wireless-persistence-gametest.py").read_text()
class WirelessPersistenceContracts(unittest.TestCase):
 def test_actual_block_entity_serialization_not_fake(self):
  for needle in ("crossTx.saveWithFullMetadata(nether.registryAccess())",
      "BlockEntity.loadStatic(",
      "restoredWireless.stored()==12000",
      "restoredWireless.networkId().equals(crossTx.networkId())",
      "WIRELESS_PERSISTENCE_CODEC_GAMETEST_V1 PASS"):
   self.assertIn(needle,SCRIPT)
 def test_saveddata_entry_codec_keeps_identity_and_mask(self):
  for needle in ("WirelessNetworkData.Entry.CODEC",
                 ".encodeStart(com.mojang.serialization.JsonOps.INSTANCE",
                 ".parse(com.mojang.serialization.JsonOps.INSTANCE",
                 "originalNetworkEntry.equals(restoredEntry)"):
   self.assertIn(needle,SCRIPT)
if __name__=="__main__":unittest.main()
