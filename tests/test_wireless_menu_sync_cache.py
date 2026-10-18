#!/usr/bin/env python3
"""Enforce network menu single snapshot per server tick without stale persistence."""
from pathlib import Path
import unittest
SRC=(Path(__file__).resolve().parents[1]/
     "features/wireless-energy/apply-wireless-menu-sync-cache.py").read_text()
class WirelessMenuSyncCacheContracts(unittest.TestCase):
 def test_network_list_not_filtered_once_per_data_index(self):
  for fragment in (
      "private long lastSnapshotTick=Long.MIN_VALUE;",
      "private List<WirelessNetworkData.Entry> cachedNetworks=List.of();",
      "long now=player.level().getGameTime();",
      "if(now!=lastSnapshotTick){",
      "cachedNetworks=sd.available(player);",
      "lastSnapshotTick=now;",
      "var nets=cachedNetworks;"):
   self.assertIn(fragment,SRC,fragment)
 def test_cache_per_menu_not_static_global(self):
  self.assertNotIn("static List<WirelessNetworkData.Entry>",SRC)
  self.assertIn("assert s.count(needle)==1",SRC)
if __name__=="__main__":unittest.main()
