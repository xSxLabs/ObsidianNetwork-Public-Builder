#!/usr/bin/env python3
"""Build 94 source-contract gates. The main CI build compiles reconstructed Java."""
import ast, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STATION=(ROOT/"features/v17/apply-power-armor-freestanding.py").read_text()
ELYTRA=(ROOT/"features/v17/apply-power-armor-network-elytra-94.py").read_text()
BUNDLE=(ROOT/"features/v17/apply-power-armor-bundle-93.py").read_text()
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text()

class Build94(unittest.TestCase):
 def test_python_is_valid(self):
  for path in (
    "features/v17/apply-power-armor-freestanding.py",
    "features/v17/apply-power-armor-bundle-93.py",
    "features/v17/apply-power-armor-network-elytra-94.py"):
   ast.parse((ROOT/path).read_text(), filename=path)

 def test_all_upgrade_disks_keep_matching_original_style(self):
  tree=ast.parse(STATION)
  icons=None
  for node in ast.walk(tree):
   if isinstance(node,ast.Assign) and any(
      isinstance(target,ast.Name) and target.id=="icons" for target in node.targets):
    icons=ast.literal_eval(node.value)
    break
  self.assertEqual(len(icons),25)
  for item in ("strength","resistance","speed","haste","regeneration",
               "fire_resistance","jump_boost","network_elytra"):
   self.assertIn(item,icons)
   self.assertEqual(len(icons[item]),8)
   self.assertTrue(all(len(row)==8 for row in icons[item]))
  self.assertIn("obsidiannetwork:item/{name}",STATION)

 def test_network_elytra_is_same_server_physics_not_a_separate_flight_grant(self):
  for required in (
     "PowerArmorElytraBridge.java","PowerArmorRuntime.tier(",
     "network_elytra","FLIGHT_COST_PER_5_TICKS",
     "SHIFT_COST_PER_5_TICKS","BOOST_MAX_SPEED = 2.4D",
     "NetworkElytraSpeedCheckMixin.java",
     "NetworkElytraCuriosGlideMixin.java","NetworkElytraBoostClient.java",
     "if (!armorElytra) chest.remove(DataComponents.GLIDER);"):
   self.assertIn(required,ELYTRA)
  self.assertIn('if(!candidate.equals(origin))continue;',BUNDLE)

 def test_build_executes_all_fixes_in_order(self):
  self.assertLess(WF.index("apply-power-armor-bundle-93.py"),
                  WF.index("apply-power-armor-network-elytra-94.py"))
  self.assertIn("BUILD94_ALL_EIGHT_NEW_DISK_TEXTURES PASS",WF)

if __name__=="__main__": unittest.main()
