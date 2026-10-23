#!/usr/bin/env python3
"""Build95 optional Jade tooltip contract, independent of downloading Jade."""
import ast
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=(ROOT/"features/v17/apply-power-armor-jade-95.py").read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")

class JadeArmorBonus(unittest.TestCase):
 def test_valid_python(self):
  ast.parse(SCRIPT)

 def test_client_only_jade_and_no_required_mod(self):
  for item in (
    "@WailaPlugin","registerEntityComponent(SuitBonusProvider.INSTANCE, ArmorStand.class)",
    'compileOnly \'maven.modrinth:jade:26.1.12+neoforge\'',
    "PowerArmorSuitWorld.full(stand)","PowerArmorRuntime.tier(",
    "PowerArmorRuntime.SLOTS","ModDataComponents.POWER_ARMOR_UPGRADES",
    "cards.merge(id,1,Integer::sum)", "EnergyTool.energy(piece)<20L"):
   self.assertIn(item,SCRIPT)
  self.assertNotIn("runtimeOnly 'maven.modrinth:jade",SCRIPT)
  self.assertNotIn("implementation 'maven.modrinth:jade",SCRIPT)

 def test_exact_actual_bonuses(self):
  for item in (
    "Math.min(3,n);effect(tooltip,\"strength\",lvl,lvl*3)",
    "Math.min(2,n);effect(tooltip,\"resistance\",lvl,lvl*20)",
    'effect(tooltip,"protection",Math.min(5,n),Math.min(5,n)*8)',
    "Math.min(80,Math.min(5,n)*16)",
    "Math.min(80,Math.min(5,n)*24)",
    '"network_elytra"', '"flight"',
    "nightVisionOn=true", "if(nightVisionOn)"):
   self.assertIn(item,SCRIPT)

 def test_build_pipeline(self):
  self.assertLess(WF.index("apply-power-armor-network-elytra-94.py"),
                  WF.index("apply-power-armor-jade-95.py"))
  self.assertIn("BUILD95_JADE_POWER_ARMOR_BONUS",WF)
  self.assertIn("test_clean_v17_*.py",WF)

if __name__=="__main__":
 unittest.main()
