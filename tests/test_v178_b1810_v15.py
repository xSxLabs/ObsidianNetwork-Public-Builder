#!/usr/bin/env python3
"""v1.7.8 v15: seven requested repairs and existing live terrain regression."""
import ast,json,os,struct,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"features/v178/apply-v178-b1810-v15.py"
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text()

class B1810V15(unittest.TestCase):
 def test_build_order(self):
  ast.parse(P.read_text())
  self.assertLess(WF.index("python3 features/v178/apply-v178-b1807-v14.py"),
                  WF.index("python3 features/v178/apply-v178-b1810-v15.py"))
  self.assertIn("xSxLabs-Network-Storage-1.7.8-v15.jar",WF)
  self.assertIn("xsxlabs-network-storage-1.7.8-v15",WF)
 def test_terrain_radius_and_live_cache(self):
  s=P.read_text()
  self.assertIn("b1810WideCursor++%169",s)
  self.assertIn("if(System.nanoTime()-start>=2_400_000L)break",s)
  self.assertIn("world.hasChunk(cx,cz)?null:archiveLookup(cx,cz)",s)
  self.assertNotIn("forceChunk(",s)
 def test_speed_removal_and_drop_conservation(self):
  s=P.read_text()
  for t in ("installedSpeedUpgrades().copy()","source.setByPlayer(held)",
            "speedUpgrades.split(Math.min(16,amount))",
            "Containers.dropItemStack","mining_builder.json"):
   self.assertIn(t,s)
 def test_legacy_charger_and_one_cube(self):
  s=P.read_text()
  for t in ('len(wc["elements"])==116', '==696',
            'wc["textures"]={"main":"obsidiannetwork:block/wireless_charger"',
            'model["textures"]' if False else 'mining_builder_case_v15',
            'mining_builder_front_v15'):
   self.assertIn(t,s)
 def test_screen_zoom_and_popup(self):
  s=P.read_text()
  for t in ("mapSide()","25-(zoom-6)*3/2","V178ClaimAreaNotice",
            "B1810_LAST_AREAS","teamName(leader)","Claim-Popup:",
            "Gebiet von: ","cycleDuration","cyclePosition"):
   self.assertIn(t,s)
 def test_generated_source_contracts(self):
  root=os.getenv("V1_SOURCE_ROOT"); resources=os.getenv("V1_RESOURCE_ROOT")
  if not root or not resources:self.skipTest("reconstructed CI Java/resources required")
  j=Path(root)/"dev/obsidiannetwork"
  a=Path(resources)/"assets/obsidiannetwork"
  terrain=(j/"client/V178TerrainMap.java").read_text()
  self.assertIn("b1810WideCursor++%169",terrain)
  self.assertIn("world.hasChunk(cx,cz)?null:archiveLookup(cx,cz)",terrain)
  menu=(j/"mining/V178MiningBuilderMenu.java").read_text()
  self.assertIn("return be.installedSpeedUpgrades().copy()",menu)
  self.assertIn("source.setByPlayer(held)",menu)
  model=json.loads((a/"models/block/mining_builder.json").read_text())
  self.assertEqual(len(model["elements"]),1)
  self.assertEqual(model["elements"][0]["faces"]["north"]["texture"],"#front")
  self.assertEqual(set(model["textures"]),{"case","front","particle"})
  for tex in ("mining_builder_case_v15.png","mining_builder_front_v15.png"):
   raw=(a/"textures/block"/tex).read_bytes()
   self.assertEqual(raw[:8],b"\x89PNG\r\n\x1a\n")
   self.assertEqual(struct.unpack(">II",raw[16:24]),(16,16))
  wc=json.loads((a/"models/block/wireless_charger.json").read_text())
  self.assertEqual(len(wc["elements"]),116)
  self.assertEqual(sum(len(e["faces"]) for e in wc["elements"]),696)
  self.assertEqual(wc["textures"]["main"],"obsidiannetwork:block/wireless_charger")
  map_screen=(j/"client/V178ClaimsMapScreen.java").read_text()
  self.assertIn("mapSide()",map_screen)
  self.assertIn("25-(zoom-6)*3/2",map_screen)
  self.assertIn("V178ClaimAreaNotice", (j/"claims/V178Claims.java").read_text())
  self.assertIn("playToClient(TYPE,CODEC)",
   (j/"claims/V178ClaimAreaNotice.java").read_text())
  self.assertIn("Gebiet von: ",(j/"client/V178ClaimAreaHud.java").read_text())
  loot=json.loads((Path(resources)/"data/obsidiannetwork/loot_table/blocks/mining_builder.json").read_text())
  names=[e.get("name") for pool in loot["pools"] for e in pool["entries"]]
  self.assertIn("obsidiannetwork:mining_builder",names)

if __name__=="__main__":unittest.main()
