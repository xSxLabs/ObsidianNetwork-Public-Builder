#!/usr/bin/env python3
"""New v1.7 must be clean and user old equipment always backed up."""
import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v17/apply-power-armor-stage1.py").read_text()
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
class CleanV17Armor(unittest.TestCase):
 def test_real_python_syntax(self):ast.parse(PATCH)
 def test_new_only_and_no_legacy_generator(self):
  self.assertIn("apply-power-armor-stage1.py",WF)
  self.assertNotIn("private/v1.7/",WF)
  self.assertIn("branches: [v1.7]",WF)
 def test_backup_before_wear_or_removal(self):
  self.assertLess(PATCH.index("loadouts.save(p,old)"),PATCH.index("station.clear();"))
  self.assertIn("saved backup",PATCH)
  self.assertIn('Commands.literal("recover")',PATCH)
  self.assertIn("if(!p.getItemBySlot(slot).isEmpty())return false;",PATCH)
  self.assertIn("ItemStack.OPTIONAL_CODEC.listOf()",PATCH)
 def test_energy_and_four_pieces(self):
  for piece in ("helmet","chestplate","leggings","boots"):
   self.assertIn('("'+piece+'",',PATCH)
  self.assertIn('ITEMS.registerItem("power_armor_{name}"',PATCH)
  self.assertIn("ENERGY_TOOL_FE.get(),0L",PATCH)
  self.assertIn("EnergyTool.consume(",PATCH)
  self.assertIn("ARMOR_STATION",PATCH)
 def test_station_does_not_lose_or_misslot_armor(self):
  self.assertIn("BreakBlockEvent",PATCH)
  self.assertIn("station.occupied()",PATCH)
  self.assertIn("3600000.0F",PATCH)
  self.assertIn("ArmorStationBlockEntity.expected(i)",PATCH)
  self.assertIn("POWER_ARMOR_HELMET.get()",PATCH)
  self.assertIn("POWER_ARMOR_BOOTS.get()",PATCH)
  self.assertLess(PATCH.index("p.getInventory().add(returned)"),PATCH.index("station.take(i)"))
 def test_hotkey_is_rebindable_and_server_verified(self):
  self.assertIn("RegisterKeyMappingsEvent",PATCH)
  self.assertIn("GLFW.GLFW_KEY_V",PATCH)
  self.assertIn("playToServer(TYPE,STREAM_CODEC",PATCH)
  self.assertIn("ClientPacketDistributor.sendToServer(new PowerArmorExitPayload())",PATCH)
  self.assertIn("PowerArmorCommands.exit(p)",PATCH)
  self.assertIn("if(backup==null||!PowerArmorRuntime.full(p))return 0;",PATCH)
 def test_station_flight_card_is_reversible(self):
  self.assertIn('String upgrades=chest.get(',PATCH)
  self.assertIn('"flight"',PATCH)
  self.assertIn("POWER_ARMOR_UPGRADE.get()",PATCH)
  self.assertIn("Flight Upgrade returned.",PATCH)
  self.assertLess(PATCH.index("p.getInventory().add(card)"),PATCH.index("chest.remove("))
 def test_only_owned_flight_is_revoked(self):
  self.assertIn("OWNED_FLIGHT.add(p.getUUID())",PATCH)
  self.assertIn("OWNED_FLIGHT.remove(p.getUUID())",PATCH)
  self.assertNotIn("if(!canFly&&!natural&&p.getAbilities().mayfly)",PATCH)

if __name__=="__main__":unittest.main()
