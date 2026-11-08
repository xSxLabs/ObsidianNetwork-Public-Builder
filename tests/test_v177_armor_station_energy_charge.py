#!/usr/bin/env python3
"""Regressions: standing on the station charges 4 armor items using only real FE."""
import ast
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v177/apply-v177-armor-station-energy-charge.py").read_text(encoding="utf-8")
FLOW=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")

class ArmorStationEnergyCharge(unittest.TestCase):
 def test_python_syntax(self):
  ast.parse(PATCH)

 def test_all_three_services_share_station_tick_and_buffers(self):
  for needle in (
      "V177ArmorIntegrity.repairNearby(server,pos,be);",
      "V177ArmorStationPaste.fillHelmet(server,pos,be);",
      "V177ArmorStationCharge.chargeWornArmor(server,pos,be);",
      "public static final int MAX_FE_PER_SERVICE=20_000;",
      "station.v177StoredFe()",
      "station.v177ConsumeFe(offered)",
      "EnergyTool.energy(armor)",
      "EnergyTool.capacity(armor)",
      "EnergyTool.setEnergy(armor,stored+drawn)",
      "PowerArmorRuntime.SLOTS.length",
      "PowerArmorRuntime.full(player)",
      "V177ArmorIntegrity.piece(armor,slot)",
  ):self.assertIn(needle,PATCH,needle)

 def test_fe_debited_before_item_mutation(self):
  self.assertLess(PATCH.index("int drawn=station.v177ConsumeFe(offered);"),
                  PATCH.index("EnergyTool.setEnergy(armor,stored+drawn);"))
  self.assertIn("long missing=Math.max(0L,capacity-stored);",PATCH)
  self.assertIn("if(missing<=0L)continue;",PATCH)
  self.assertIn("int available=Math.min(MAX_FE_PER_SERVICE,station.v177StoredFe());",PATCH)
  self.assertIn("if(available<=0)return;",PATCH)
  self.assertIn("available-=drawn;",PATCH)

 def test_energy_distribution_math(self):
  def distribute(stock,parts,cap=100_000):
   rest=min(20_000,stock)
   original=sum(parts)
   step=max(1,rest//4)
   for pass_number in range(2):
    for i in range(4):
     absent=cap-parts[i]
     take=min(absent,rest,step if pass_number==0 else rest)
     parts[i]+=take
     rest-=take
   return stock-(min(20_000,stock)-rest),parts

  after,charged=distribute(200_000,[0,0,0,0])
  self.assertEqual(after,180_000)
  self.assertEqual(charged,[5000,5000,5000,5000])
  after,charged=distribute(20_000,[100_000,0,100_000,0])
  self.assertEqual(after,0)
  self.assertEqual(charged,[100_000,15_000,100_000,5_000])
  after,charged=distribute(20_000,[100_000]*4)
  self.assertEqual(after,20_000)
  self.assertEqual(charged,[100_000]*4)
  after,charged=distribute(999,[0]*4)
  self.assertEqual(after,0)
  self.assertEqual(sum(charged),999)

 def test_station_specific_and_original_patch_order(self):
  start=FLOW.index("python3 features/v177/apply-v177-armor-integrity-repair.py")
  paste=FLOW.index("python3 features/v177/apply-v177-armor-station-nutripaste.py")
  charge=FLOW.index("python3 features/v177/apply-v177-armor-station-energy-charge.py")
  self.assertLess(start,paste)
  self.assertLess(paste,charge)
  self.assertIn("test_v177_armor_station_energy_charge.py",FLOW)
  self.assertIn('if [ "$GITHUB_REF_NAME" = "1.7.7" ]; then',FLOW)

if __name__=="__main__":
 unittest.main()
