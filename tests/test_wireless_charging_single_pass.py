#!/usr/bin/env python3
"""Fail-closed regression contracts for single-pass wireless player charging."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]/"features/wireless-energy"
PATCH=(ROOT/"apply-wireless-charging-single-pass.py").read_text()

class WirelessSinglePassChargingContracts(unittest.TestCase):
 def test_inventory_enumerated_once_per_player_interval(self):
  self.assertIn("player.level().getGameTime()%20!=0",PATCH)
  self.assertEqual(PATCH.count("var inventory=player.getInventory().getNonEquipmentItems();"),1)
  self.assertIn("for(int i=0;i<inventory.size()&&remaining>0;i++)",PATCH)
  self.assertIn("int category=i<9?WirelessNetworkData.HOTBAR:WirelessNetworkData.INVENTORY",PATCH)
  self.assertIn("java.util.ArrayList<WirelessNetworkData.Entry> active",PATCH)
  self.assertIn("if(active.isEmpty())return;",PATCH)
 def test_per_category_network_masks_and_global_budget(self):
  for keyword in ("MAX_PER_PLAYER_TICK","WirelessNetworkData.HOTBAR","WirelessNetworkData.INVENTORY",
      "WirelessNetworkData.ARMOR","WirelessNetworkData.OFFHAND","WirelessNetworkData.CURIOS",
      "remaining-=chargeOne(player,network.id(),stack,remaining)"):
   self.assertIn(keyword,PATCH,keyword)
 def test_curios_enumerated_once_and_optional(self):
  self.assertIn('ModList.get().isLoaded("curios")',PATCH)
  self.assertIn("WirelessCuriosCharging.charge(player,active,remaining)",PATCH)
  self.assertIn("CuriosApi.getCuriosInventory(player)",PATCH)
  self.assertIn("java.util.List<WirelessNetworkData.Entry> networks",PATCH)
 def test_transactional_charge_one_kept_untouched(self):
  self.assertIn("target.write_text(s[:a]+new+s[b:])",PATCH)
  self.assertIn("s.count(old)==1",PATCH)
  self.assertNotIn("Transaction.openRoot()",PATCH)

if __name__=="__main__":unittest.main()
