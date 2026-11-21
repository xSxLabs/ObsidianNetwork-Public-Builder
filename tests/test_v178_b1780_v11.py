#!/usr/bin/env python3
"""B1780 / v11: static and generated client/server regression contract."""
import ast,os,unittest,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"features/v178/apply-v178-b1780-v11.py"
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
class V11MapBuilderHud(unittest.TestCase):
 def test_v11_script_installed_after_previous_miner(self):
  source=P.read_text()
  ast.parse(source)
  a="python3 features/v178/apply-v178-b1765-map-builder.py"
  b="python3 features/v178/apply-v178-b1780-v11.py"
  self.assertIn(a,WF)
  self.assertIn(b,WF)
  self.assertLess(WF.index(a),WF.index(b))
 def test_compact_skin_and_accurate_surface(self):
  source=P.read_text()
  for key in ("B1780_COMPACT_SKIN_ARROW","x-3,y-3,6",
              "for(int t=5;t<=9;t++","vegetation<4",
              "Blocks.SHORT_GRASS","Blocks.TALL_GRASS",
              "Blocks.DANDELION","refreshTick%4L==0L"):
   self.assertIn(key,source,key)
  self.assertNotIn("forceChunk(",source)
 def test_real_builder_speed_and_model(self):
  source=P.read_text()
  for key in ("ObsidianNetwork.SPEED_UPGRADE.get()",
              "moveItemStackTo(held,1,2,false)",
              "moveItemStackTo(held,27,63,true)",
              "slot==0||(slot>1&&slot<27)",
              "models/block/mining_builder.json",
              "textures/block","ambientocclusion"):
   self.assertIn(key,source,key)
 def test_independent_saved_hud_editing(self):
  source=P.read_text()
  for key in ("V178HudPlacement.java","V178HudEditorScreen.java",
              "setMap(int x,int y","setInfo(int x,int y",
              "infoScale()","setProperty(","mouseDragged(MouseButtonEvent",
              "mouseReleased(MouseButtonEvent","mouseScrolled(",
              "V178MiniPreferences.adjustSize(delta)",
              "V178HudPlacement.changeInfoSize(delta*5)"):
   self.assertIn(key,source,key)
 def test_artifact_version(self):
  self.assertIn("xSxLabs-Network-Storage-1.7.8-v11.jar",WF)
  self.assertIn("xsxlabs-network-storage-1.7.8-v11",WF)
 def test_generated_java_and_model(self):
  root=os.getenv("V1_SOURCE_ROOT")
  resource=os.getenv("V1_RESOURCE_ROOT")
  if not root or not resource:self.skipTest("Generated source only exists inside CI")
  j=Path(root)/"dev/obsidiannetwork"
  java=lambda rel:(j/rel).read_text()
  markers=java("client/V178MapMarkers.java")
  self.assertIn("B1780_COMPACT_SKIN_ARROW",markers)
  self.assertIn("g,mc.player.getSkin(),x-3,y-3,6",markers)
  terrain=java("client/V178TerrainMap.java")
  self.assertIn("while(vegetation<4",terrain)
  menu=java("mining/V178MiningBuilderMenu.java")
  self.assertIn("moveItemStackTo(held,1,2,false)",menu)
  self.assertIn("moveItemStackTo(held,27,63,true)",menu)
  hud=java("client/V178ClaimsClient.java")
  self.assertIn("V178HudPlacement.infoX(",hud)
  self.assertIn("V178HudPlacement.mapX(",hud)
  self.assertIn("setInfo(int x,int y",java("client/V178HudPlacement.java"))
  self.assertIn("mouseDragged(MouseButtonEvent",java("client/V178HudEditorScreen.java"))
  model=json.loads((Path(resource)/"assets/obsidiannetwork/models/block/mining_builder.json").read_text())
  self.assertGreaterEqual(len(model["elements"]),20)
  self.assertLessEqual(len(model["elements"]),40)
if __name__=="__main__":unittest.main()
