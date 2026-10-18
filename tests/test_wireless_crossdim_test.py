#!/usr/bin/env python3
"""Fail-closed checks: wireless integration test really crosses dimensions."""
from pathlib import Path
import unittest

SCRIPT=(Path(__file__).resolve().parents[1]/
        "features/wireless-energy/inject-wireless-crossdim-gametest.py").read_text()

class TrueCrossDimensionGameTestContracts(unittest.TestCase):
 def test_uses_real_second_server_level_and_separate_loaded_transmitter(self):
  for marker in (
   "getLevel(net.minecraft.world.level.Level.NETHER)",
   "nether.getChunkAt(crossTxPos)",
   "ObsidianNetwork.NETWORK_TRANSMITTER.get().defaultBlockState()",
   "nether.getBlockEntity(crossTxPos)",
   "crossTx.energyHandler().insert(12000,fillCross)",
   "worldSink.stored()>8000",
   "worldSource.stored()+worldTransmitter.stored()+worldSink.stored()+crossTx.stored()==20000",
   'System.out.println("WIRELESS_TRUE_CROSSDIM_FE_GAMETEST_V2 PASS")',
  ):self.assertIn(marker,SCRIPT)
 def test_rollbacks_untouched_and_cleanup_is_test_only(self):
  self.assertIn('assert source.count(anchor)==1',SCRIPT)
  self.assertIn('nether.setBlock(crossTxPos,Blocks.AIR.defaultBlockState(),3)',SCRIPT)
  self.assertNotIn('forceChunk(',SCRIPT)

if __name__=="__main__":unittest.main()
