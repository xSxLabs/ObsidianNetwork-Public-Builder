#!/usr/bin/env python3
"""Regression: exactly 500mB real NutriPaste in Armor Station and helmet refill."""
import ast
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v177/apply-v177-armor-station-nutripaste.py").read_text(encoding="utf-8")
FLOW=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")

class StationPaste(unittest.TestCase):
 def test_python_syntax(self):
  ast.parse(PATCH)
 def test_real_500mb_tank_accepts_only_nutripaste(self):
  for token in (
    "V177_STATION_NUTRIPASTE_500MB",
    "V177_PASTE_CAPACITY=500L",
    "NutriPasteFluids.SOURCE.get()",
    "return paste().equals(resource);",
    "if(offered<=0||!isValid(slot,resource))return 0;",
    "V177_PASTE_CAPACITY-v177Paste",
    "v177PasteJournal.updateSnapshots(tx)",
    "revertToSnapshot(Long before)",
    "return 0; // input only",
    "Capabilities.Fluid.BLOCK",
    "(station,side)->station.v177PastePort()",
  ):self.assertIn(token,PATCH,token)
 def test_refill_is_server_authoritative_and_debited_exactly(self):
  for token in (
    "V177ArmorStationPaste.fillHelmet(server,pos,be)",
    "NutriPaste.add(helmet,available)",
    "station.v177TakePaste(inserted)",
    "PowerArmorRuntime.full(player)",
    "V177ArmorIntegrity.piece(helmet,0)",
    "world.players()",
    "break; // one nearby player per station tick",
    "station.v177StoredPaste()<=0L",
    "player.getItemBySlot(PowerArmorRuntime.SLOTS[0])",
  ):self.assertIn(token,PATCH,token)
  self.assertNotIn("NutriPaste.add(helmet,500L)",PATCH)
 def test_station_paste_and_fe_are_independently_persisted(self):
  for token in (
    'out.putLong("v177_armor_station_paste_mb",v177StoredPaste());',
    'in.getLongOr("v177_armor_station_paste_mb",0L)',
    'Math.min(V177_PASTE_CAPACITY,',
    'v177_armor_station_fe',
    'V177ArmorIntegrity.repairNearby(server,pos,be)',
    "Paste refill does not consume FE",
  ):self.assertIn(token,PATCH,token)
 def test_amount_conservation(self):
  # Saturation cannot create paste, accept beyond 500 or overfill a helmet.
  def fill(tank,helmet,helmet_capacity=1_000_000):
   inserted=max(0,min(tank,helmet_capacity-helmet))
   return tank-inserted,helmet+inserted,inserted
  self.assertEqual(fill(500,0),(0,500,500))
  self.assertEqual(fill(500,999_800),(300,1_000_000,200))
  self.assertEqual(fill(500,1_000_000),(500,1_000_000,0))
  self.assertEqual(fill(0,400),(0,400,0))
 def test_v177_only_after_energy_station(self):
  first=FLOW.index("python3 features/v177/apply-v177-armor-integrity-repair.py")
  target=FLOW.index("python3 features/v177/apply-v177-armor-station-nutripaste.py")
  self.assertLess(first,target)
  self.assertIn("test_v177_armor_station_paste.py",FLOW)
  self.assertIn('if [ "$GITHUB_REF_NAME" = "1.7.7" ]; then',FLOW)

if __name__=="__main__":
 unittest.main()
