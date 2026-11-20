#!/usr/bin/env python3
"""B1716: GPU-cropped minimap controls and unified custom keybind category."""
import ast
import json
import os
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATCH="features/v178/apply-v178-b1716-minimap-settings-and-keys.py"
SCRIPT=(ROOT/PATCH).read_text(encoding="utf-8")
WORKFLOW=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")

class MinimapConfiguration1716(unittest.TestCase):
 def test_injection_order_and_static_source(self):
  ast.parse(SCRIPT,filename=PATCH)
  self.assertEqual(WORKFLOW.count("python3 "+PATCH),1)
  self.assertLess(WORKFLOW.index("python3 features/v178/apply-v178-b1715-miner-visuals.py"),
                  WORKFLOW.index("python3 "+PATCH))
  for token in (
    "V178MiniPreferences.java","V178ClaimsClient.java","V178MapMobCache.java",
    "V178Waypoints.java","V178TerrainMap.java","V178KeybindCategory.java",
    "V178MapSettingsScreen.java","visibleChunks()","mobRange()",
    "registerCategory(XSXLABS)","MINIMAP_SETTINGS.consumeClick()",
    "KeyMapping.Category", "V178ClaimsClient.toggleOption(key)"
  ):
   self.assertIn(token,SCRIPT)
  self.assertNotIn("ClientPacketDistributor",SCRIPT)
  self.assertNotIn("world.getChunk(",SCRIPT)
  self.assertNotIn("texture.upload()",SCRIPT)

 def test_generated_preferences_and_screen(self):
  java=os.environ.get("V1_SOURCE_ROOT")
  res=os.environ.get("V1_RESOURCE_ROOT")
  if not java or not res:self.skipTest("Generated work source exists only in CI")
  j=Path(java)/"dev/obsidiannetwork/client"
  p=(j/"V178MiniPreferences.java").read_text()
  claims=(j/"V178ClaimsClient.java").read_text()
  terrain=(j/"V178TerrainMap.java").read_text()
  mob=(j/"V178MapMobCache.java").read_text()
  settings=(j/"V178MapSettingsScreen.java").read_text()
  category=(j/"V178KeybindCategory.java").read_text()
  for k in ("zoom","mobRange","size","corner","circle","hostileOnly"):
   self.assertIn('p.setProperty("'+k+'"',p,k)
  for key in ("visibleChunks()", "cycleZoom()", "cycleMobRange()", "mobRange()"):
   self.assertIn(key,p)
  self.assertIn("int source=diameter==7",terrain)
  self.assertIn("int markerStep=7*step/view;",claims)
  self.assertIn("MINIMAP_SETTINGS.consumeClick()",claims)
  self.assertIn("event.register(MINIMAP_SETTINGS)",claims)
  self.assertIn("inflate(V178MiniPreferences.mobRange())",mob)
  self.assertIn("V178ClaimsClient.toggleOption(key)",settings)
  self.assertIn("V178MiniPreferences::cycleZoom",settings)
  self.assertIn("V178MiniPreferences::cycleCorner",settings)
  self.assertIn("V178MiniPreferences::toggleMobs",settings)
  self.assertIn("V178UiTheme.panel",settings)
  self.assertIn("event.registerCategory(XSXLABS)",category)
  for path in ("en_us","de_de"):
   lang=json.loads((Path(res)/f"assets/obsidiannetwork/lang/{path}.json").read_text())
   self.assertEqual(lang["key.category.obsidiannetwork.network_storage"],
                    "xSxLabs Network Storage")
   self.assertTrue(lang["key.obsidiannetwork.minimap_settings"])

if __name__=="__main__":
 unittest.main()
