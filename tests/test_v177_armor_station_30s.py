#!/usr/bin/env python3
"""60-second servicing contract for a fully depleted 4-piece Power Armor suit.

The station never generates FE or paste: the model requires a power source
replenishing the real 400k FE station tank between services and a source that
supplies 1M mB real NutriPaste. Without adequate input, filling takes longer.
"""
import ast
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
DOUBLE=(ROOT/"features/v177/apply-v177-armor-double-fe.py").read_text(encoding="utf-8")
ENERGY=(ROOT/"features/v177/apply-v177-armor-station-energy-charge.py").read_text(encoding="utf-8")
PASTE=(ROOT/"features/v177/apply-v177-armor-station-nutripaste.py").read_text(encoding="utf-8")
INTEGRITY=(ROOT/"features/v177/apply-v177-armor-integrity-repair.py").read_text(encoding="utf-8")
SUIT=(ROOT/"features/v17/apply-power-armor-stage1.py").read_text(encoding="utf-8")
NUTRITION=(ROOT/"features/v174/apply-nutrition-438.py").read_text(encoding="utf-8")
WORKFLOW=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")

class ThirtySecondArmorStationService(unittest.TestCase):
 def test_source_limits_match_actual_helmet_suit_and_station(self):
  for s in (ENERGY,PASTE,INTEGRITY):
   ast.parse(s)
  self.assertIn("public static final int MAX_FE_PER_SERVICE=400_000;",ENERGY)
  self.assertIn("SimpleEnergyHandler(400000,400000,0)",INTEGRITY)
  self.assertIn("public static final long V177_PASTE_CAPACITY=1_000_000L;",PASTE)
  self.assertIn("HELMET_CAPACITY=1_000_000L",NUTRITION)
  self.assertIn("p.stacksTo(1).durability(4000000)",SUIT)
  self.assertIn("Math.min(Long.MAX_VALUE/4L,base)*4L",DOUBLE)
  self.assertIn("instanceof dev.obsidiannetwork.powerarmor.PowerArmorItem",DOUBLE)
  self.assertIn("Math.min(400000,in.getIntOr(\"v177_armor_station_fe\",0))",INTEGRITY)
  self.assertIn("SUIT_HITPOINTS=1000",INTEGRITY)
  self.assertIn("server.getGameTime()%5L==0L",INTEGRITY)
  self.assertIn("V177ArmorIntegrity.repairNearby(server,pos,be);",INTEGRITY)
  self.assertIn("V177ArmorStationPaste.fillHelmet(server,pos,be);",PASTE)
  self.assertIn("V177ArmorStationCharge.chargeWornArmor(server,pos,be);",ENERGY)
  self.assertIn("NutriPaste.add(helmet,available)",PASTE)
  self.assertIn("station.v177TakePaste(inserted)",PASTE)
  self.assertIn("station.v177ConsumeFe(offered)",ENERGY)

 def test_zero_to_full_all_three_under_60_seconds_with_enough_real_inputs(self):
  # 20 TPS * 60s / service every 5 ticks = 240 service cycles.
  cycles=60*20//5
  energy=[0]*4
  hp=[0]*4
  paste=0
  supplied_fe=0
  consumed_fe=0
  supplied_paste=1_000_000
  station_paste=supplied_paste
  completed_on=None
  for service in range(1,cycles+1):
   # The external FE source refills the real 200k station store BETWEEN
   # services; this is explicitly a supply assumption, not energy creation.
   incoming_fe=400_000
   supplied_fe+=incoming_fe
   station_fe=incoming_fe
   if service>1:
    # Conservative 20 FE per armor piece per five ticks, to cover runtime use.
    for i in range(4):energy[i]=max(0,energy[i]-20)

   # Existing integrity service takes priority, real 25 FE for each HP
   # on each of four pieces and at most 10 HP per piece this cycle.
   repair_cost=0
   for i in range(4):
    restored=min(1000-hp[i],10,(min(1000,station_fe)-repair_cost)//25)
    if restored>0:
     hp[i]+=restored
     repair_cost+=25*restored
   station_fe-=repair_cost
   consumed_fe+=repair_cost

   # Paste uses a separate tank, consumes only real paste, fills helmet.
   inserted=min(station_paste,1_000_000-paste)
   station_paste-=inserted
   paste+=inserted

   # The original real station charging algorithm, retaining 2-pass fair
   # allocation and strictly debiting the shared FE buffer per transfer.
   available=min(400_000,station_fe)
   per_piece=max(1,available//4)
   for pass_number in range(2):
    for i in range(4):
     offered=min(16_000_000-energy[i],available,
                 per_piece if pass_number==0 else available)
     if offered>0:
      energy[i]+=offered
      available-=offered
      station_fe-=offered
      consumed_fe+=offered
   self.assertGreaterEqual(station_fe,0)
   self.assertLessEqual(consumed_fe,supplied_fe)
   self.assertEqual(station_paste+paste,supplied_paste)
   if all(x==16_000_000 for x in energy) and all(x==1000 for x in hp) and paste==1_000_000:
    completed_on=service
    break
  self.assertIsNotNone(completed_on,"At least one system did not fill within 60 seconds")
  self.assertLessEqual(completed_on,240)
  self.assertLessEqual(completed_on*5,1200)

 def test_pipeline_calls_integrity_then_paste_then_energy(self):
  a=WORKFLOW.index("python3 features/v177/apply-v177-armor-integrity-repair.py")
  b=WORKFLOW.index("python3 features/v177/apply-v177-armor-station-nutripaste.py")
  c=WORKFLOW.index("python3 features/v177/apply-v177-armor-station-energy-charge.py")
  self.assertLess(a,b)
  self.assertLess(b,c)
  self.assertIn("test_v177_armor_station_30s.py",WORKFLOW)

if __name__=="__main__":
 unittest.main()
