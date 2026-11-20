#!/usr/bin/env python3
"""B1725: map button hitbox isolation + discoverable three-tab minimap UI."""
import ast
import os
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATCH="features/v178/apply-v178-b1725-map-settings-navigation.py"
SRC=(ROOT/PATCH).read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")

class MapOptionsNavigation1725(unittest.TestCase):
 def test_patch_runs_after_old_overlays(self):
  ast.parse(SRC,filename=PATCH)
  self.assertEqual(WF.count("python3 "+PATCH),1)
  self.assertLess(WF.index("python3 features/v178/apply-v178-b1716-minimap-settings-and-keys.py"),
                  WF.index("python3 "+PATCH))
  self.assertIn('nav("Minimap-Optionen",154',SRC)
  self.assertIn('nav("Team (alt)",87',SRC)
  self.assertIn('nav("Teams",70',SRC)
  self.assertIn('nav("Wegpunkte",91',SRC)
  self.assertIn('nav("Zentrieren",94',SRC)
  self.assertIn("toolbarBottom+27",SRC)
  self.assertIn("WELTKARTE",SRC)
  self.assertIn("ANZEIGEN",SRC)
  self.assertIn("MINIMAP",SRC)
  self.assertIn("Zurueck zur Karte",SRC)
  self.assertNotIn("ClientPacketDistributor",SRC)
  self.assertNotIn("world.getChunk(",SRC)

 def test_responsive_toolbar_boxes_do_not_overlap(self):
  # Mirrors nav button layout, including 320px minimum scaled MC width.
  widths=[82,65,94,97,96,91,70,87,154,55]
  for width in (320,400,480,700,900,1280):
   boxes=[]
   x,y=8,6
   for w in widths:
    if x+w>width-8:x,y=8,y+25
    self.assertLessEqual(x+w,width-8)
    rect=(x,y,x+w,y+20)
    self.assertTrue(all(a[2]<=x or rect[2]<=a[0] or
                        a[3]<=y or rect[3]<=a[1] for a in boxes),
                    (width,rect,boxes))
    boxes.append(rect)
    x+=w+5
   self.assertEqual(len(boxes),10)

 def test_generated_java_has_clear_access(self):
  root=os.environ.get("V1_SOURCE_ROOT")
  if not root:self.skipTest("CI generated Java only")
  java=Path(root)/"dev/obsidiannetwork/client"
  world=(java/"V178ClaimsMapScreen.java").read_text()
  settings=(java/"V178MapSettingsScreen.java").read_text()
  self.assertIn('nav("Minimap-Optionen",154',world)
  self.assertIn('new V178MapSettingsScreen(this)',world)
  self.assertIn("toolbarBottom=Math.max(toolbarBottom",world)
  self.assertIn("Math.max(toolbarBottom+27",world)
  self.assertIn("private void adapt(){",world)
  self.assertIn("V178ClaimsClient::toggleMinimap",world)
  self.assertIn("V178ClaimTeamScreen(this)",world)
  self.assertIn("V178ClaimsTeamScreen(this)",world)
  self.assertIn("V178WaypointEditorScreen(this",world)
  self.assertIn("V178WaypointManagerScreen(this",world)
  self.assertNotIn(".bounds(Math.max(5,width-82),5,77,20)",world)
  self.assertNotIn(".bounds(347,5,47,20)",world)
  self.assertIn("V178ClaimsClient.toggleOption(key)",settings)
  for token in ("V178MiniPreferences::cycleZoom","V178MiniPreferences::cycleCorner",
                "V178MiniPreferences::toggleMobs",
                "V178MiniPreferences::cycleMobRange","V178MiniPreferences::toggleShape",
                "V178MiniPreferences::cycleSize",
                "V178UiTheme.panel","Zurueck zur Karte"):
   self.assertIn(token,settings)
  self.assertIn("Minecraft.getInstance().setScreen(previous)",settings)
  self.assertIn('{"minimap","terrain","player"}',settings)
  self.assertIn('{"claims","loaded","waypoints","coords","chunk","daytime"}',settings)
  self.assertIn('{"map_terrain","map_claims","map_waypoints","map_player"}',settings)

if __name__=="__main__":unittest.main()
