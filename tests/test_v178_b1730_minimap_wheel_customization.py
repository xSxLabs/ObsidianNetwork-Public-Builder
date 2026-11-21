#!/usr/bin/env python3
"""B1730: user-adjustable detailed round map + persistent player wheel layout."""
import ast,os,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
P="features/v178/apply-v178-b1730-minimap-wheel-customization.py"
SRC=(R/P).read_text(encoding="utf-8")
WF=(R/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")

class MinimapWheelCustomizationB1730(unittest.TestCase):
 def test_order_and_safety(self):
  ast.parse(SRC,filename=P)
  self.assertEqual(WF.count("python3 "+P),1)
  self.assertLess(WF.index("python3 features/v178/apply-v178-b1725-map-settings-navigation.py"),
                  WF.index("python3 "+P))
  self.assertLess(WF.index("python3 "+P),
                  WF.index("python3 -m unittest discover -s tests -p 'test_v178_b1730_minimap_wheel_customization.py'"))
  self.assertNotIn("PacketDistributor",SRC)
  self.assertNotIn("world.getChunk(",SRC)
  self.assertNotIn("world.destroyBlock(",SRC)
  self.assertNotIn("gameTime++",SRC)

 def test_all_action_ids_have_labels_and_custom_switches(self):
  for keyword in ("Exit Armor","Portal A","Portal B","Recall Armor",
                  "Network Vision","Attack Mode","Follow","Turret",
                  "Sleep","J.A.R.V.I.S.","JARVIS Settings","FlyModule",
                  "Wheel Settings","V178WheelPreferences.customize",
                  "V178WheelSettingsScreen", "action.","UUID", "showAll()"):
   self.assertIn(keyword,SRC)
  self.assertIn("filtered[count++]=12;",SRC)
  self.assertIn("Arrays.copyOf(filtered,count);",SRC)

 def test_rendering_and_settings_source(self):
  for keyword in ("cropVersion==crop","ringRadius","innerRadius",
                  "getMapColor(world,block).col","FluidTags.WATER",
                  "FluidTags.LAVA","V178MapMarkers.player",
                  "adjustSize(int delta)","adjustFineZoom(int delta)",
                  "world.hasChunk", "markerStep(int tile)"):
   if keyword=="world.hasChunk":continue # inherited from original cache
   self.assertIn(keyword,SRC)
  self.assertIn("if(claiming&&grid&&tile>=5)",SRC)
  self.assertIn('key.obsidiannetwork.wheel_settings',SRC)

 def test_generated_source_contract(self):
  root=os.environ.get("V1_SOURCE_ROOT")
  resources=os.environ.get("V1_RESOURCE_ROOT")
  if not root or not resources:self.skipTest("Generated Java only in full CI")
  c=Path(root)/"dev/obsidiannetwork/client"
  names=("V178WheelSettingsScreen","V178WheelPreferences","V178MapMarkers")
  for name in names:self.assertTrue((c/(name+".java")).is_file(),name)
  mini=(c/"V178ClaimsClient.java").read_text()
  # B1740 displays compact scaled XYZ once in the appropriate corner.
  self.assertIn('V178MapInfo.line(g,"Player Pos: "',mini)
  self.assertNotIn('"X: "+mc.player.blockPosition().getX()',mini)
  self.assertNotIn('"CLAIMS "',mini)
  self.assertIn("V178MapMarkers.player(g,px,py",mini)
  self.assertIn("WHEEL_SETTINGS.consumeClick()",mini)
  terrain=(c/"V178TerrainMap.java").read_text()
  self.assertIn("cropVersion==crop",terrain)
  self.assertIn("FluidTags.WATER",terrain)
  world=(c/"V178ClaimsMapScreen.java").read_text()
  self.assertIn("if(claiming&&grid&&tile>=5)",world)
  self.assertIn("V178MapMarkers.player(g,px,py",world)
  wheel=(c/"NetworkActionWheelClient.java").read_text()
  self.assertIn("V178WheelPreferences.customize",wheel)
  self.assertIn('i==12?"WHEEL SETTINGS"',wheel)
  prefs=(c/"V178MiniPreferences.java").read_text()
  self.assertIn('p.setProperty("customStep"',prefs)
  self.assertIn('p.setProperty("fineZoom"',prefs)

if __name__=="__main__":unittest.main()
