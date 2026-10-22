#!/usr/bin/env python3
"""Regression contract for station-independent persistent Power Armor."""
import ast
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v17/apply-power-armor-freestanding.py").read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")


class StationIndependence(unittest.TestCase):
 def test_python_and_order(self):
  ast.parse(PATCH)
  self.assertIn("python3 features/v17/apply-power-armor-freestanding.py",WF)
  self.assertLess(WF.index("apply-power-armor-animation.py"),WF.index("apply-power-armor-freestanding.py"))

 def test_no_station_generated_or_consumed_on_exit(self):
  self.assertIn("return PowerArmorSuitWorld.exit(p);",PATCH)
  self.assertIn("new ArmorStand(level,",PATCH)
  self.assertIn("level.addFreshEntity(stand)",PATCH)
  self.assertNotIn("level.setBlock(pos,ObsidianNetwork.ARMOR_STATION",PATCH)
  self.assertNotIn("level.removeBlock(pos",PATCH)
  self.assertIn("Neither entering nor exiting consumes or creates an Armor Station.",PATCH)

 def test_original_armor_is_always_backed_up_first(self):
  self.assertIn("saved.save(player,original)",PATCH)
  self.assertLess(PATCH.index("saved.save(player,original)"),PATCH.index("stand.discard();"))
  self.assertIn("backup.previous().get(i).copy()",PATCH)
  self.assertLess(PATCH.index("if(!spawn(player,suit))return 0;",PATCH.index("public static int exit")),
                  PATCH.index("saved.finish(player);"))
  self.assertIn("ArmorLoadoutData.get(player.level().getServer()).has(player)",PATCH)

 def test_right_click_enter_and_rebindable_exit(self):
  self.assertIn("PlayerInteractEvent.EntityInteract",PATCH)
  self.assertIn("PlayerInteractEvent.EntityInteractSpecific",PATCH)
  self.assertIn("enter(stand,event.getEntity())",PATCH)
  self.assertIn("event.getTarget()",PATCH)
  self.assertIn("event.setCanceled(true)",PATCH)
  self.assertIn("PowerArmorRuntime.SLOTS[i]",PATCH)
  self.assertIn("saved.has(player)",PATCH)
  self.assertIn("Press the rebindable Exit Power Armor key",PATCH)

 def test_station_only_manages_own_suit_upgrades(self):
  self.assertIn("PowerArmorSuitWorld.findNearby(level,pos,p)",PATCH)
  self.assertIn("stand.getTags().contains(owner(player))",PATCH)
  self.assertIn("suits.size()==1",PATCH)
  self.assertIn("suitStand.setItemSlot(",PATCH)
  self.assertIn("Armor Station manages upgrades only.",PATCH)
  self.assertIn("Armor Station is for upgrades.",PATCH)


if __name__=="__main__":
 unittest.main()
