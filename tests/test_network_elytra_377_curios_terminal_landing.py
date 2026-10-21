#!/usr/bin/env python3
"""Build 377 regression checks: Curios terminal remains equippable, Elytra grounds correctly."""
import ast, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HOT=(ROOT/"features/wireless-energy/apply-network-elytra-hotfix.py").read_text()
FLIGHT=(ROOT/"features/wireless-energy/apply-network-elytra-landing.py").read_text()
WF=(ROOT/".github/workflows/networkstorage-v1.6.yml").read_text()
class CuriosTerminalElytra377(unittest.TestCase):
 def test_wireless_terminal_slot_does_not_get_overwritten(self):
  self.assertIn('players_data=json.loads(players_file.read_text', HOT)
  self.assertIn('for name in ("network_terminal","back")', HOT)
  self.assertIn('players_data["replace"]=False', HOT)
  self.assertIn('terminal_tag=res/"data/curios/tags/item/network_terminal.json"',HOT)
  self.assertNotIn('{"entities":["minecraft:player"],"slots":["back"]}',HOT)
 def test_elytra_landing_and_takeoff_gates(self):
  ast.parse(FLIGHT)
  self.assertIn('if (player.onGround()) {',FLIGHT)
  self.assertIn('player.stopFallFlying();',FLIGHT)
  self.assertIn('if(player.onGround())return;',FLIGHT)
  self.assertIn('!player.isFallFlying() && player.getDeltaMovement().y>=-0.02D',FLIGHT)
  self.assertIn('mc.player.stopFallFlying()',FLIGHT)
  self.assertNotIn('EnergyTool.consume(',FLIGHT)
 def test_actual_pipeline_and_no_meter_edits(self):
  self.assertEqual(WF.count("python3 features/wireless-energy/apply-network-elytra-landing.py"),1)
  self.assertLess(WF.index("python3 features/wireless-energy/apply-network-elytra-hotfix.py"),WF.index("python3 features/wireless-energy/apply-network-elytra-landing.py"))
  self.assertNotIn("terminal-live-storage-meter.py",FLIGHT)
if __name__=="__main__":unittest.main()
