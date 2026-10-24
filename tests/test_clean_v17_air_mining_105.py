#!/usr/bin/env python3
"""Build 105 standalone contract: additive Air Mining disk and break speed."""
import ast
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v17/apply-power-armor-air-mining-105.py").read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")

class AirMining105(unittest.TestCase):
 def test_python_is_valid(self):
  ast.parse(PATCH)
 def test_real_registry_station_recovery_and_disk(self):
  for key in (
   'POWER_CARD_AIR_MINING',
   'ITEMS.registerItem("power_card_air_mining"',
   'case "air_mining" ->',
   'textures/item/power_card_air_mining.png',
   'models/item/power_card_air_mining.json',
   'items/power_card_air_mining.json',
   'item.obsidiannetwork.power_card_air_mining',
   'assert not java.exists()',
  ):self.assertIn(key,PATCH)
 def test_no_walking_or_elytra_bonus_and_no_client_server_desync(self):
  for key in (
   'PlayerEvent.BreakSpeed',
   'EventPriority.LOWEST',
   '!player.getAbilities().flying',
   'player.onGround()',
   'tier<1||tier>24',
   'PowerArmorRuntime.tier(armor,i)!=tier',
   'EnergyTool.energy(armor)<20L',
   '"air_mining".equals(id)',
   'Float.isFinite(speed)',
   'event.setNewSpeed(speed*5.0F);',
  ):self.assertIn(key,PATCH)
  self.assertNotIn('instanceof ServerPlayer',PATCH)
  self.assertNotIn('player.setOnGround',PATCH)
 def test_premium_recipe_and_workflow(self):
  for key in ('"minecraft:netherite_pickaxe"','"obsidiannetwork:advanced_energy_cell"',
              '"minecraft:nether_star"','"obsidiannetwork:power_armor_upgrade"',
              '"pattern":["ABA","CDC","AEA"]'):self.assertIn(key,PATCH)
  self.assertIn("python3 features/v17/apply-power-armor-air-mining-105.py",WF)
  self.assertLess(WF.index("apply-power-armor-energy-shield-104.py"),
                  WF.index("apply-power-armor-air-mining-105.py"))
  self.assertIn("BUILD105_AIR_MINING",WF)

if __name__=="__main__":unittest.main()
