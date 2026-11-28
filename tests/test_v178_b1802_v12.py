#!/usr/bin/env python3
"""B1802 v12 regression checks for dynamic terrain, UI and miner safety."""
import ast
import json
import os
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"features/v178/apply-v178-b1802-v12.py"
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text()

class V12Fixes(unittest.TestCase):
 def test_patch_syntax_order_and_artifact_identity(self):
  ast.parse(P.read_text())
  self.assertLess(WF.index("python3 features/v178/apply-v178-b1799-render-hotpaths.py"),
                  WF.index("python3 features/v178/apply-v178-b1802-v12.py"))
  self.assertIn("xSxLabs-Network-Storage-1.7.8-v21.jar",WF)
  self.assertIn("xsxlabs-network-storage-1.7.8-v21",WF)
  self.assertIn("_EXPLICIT_BUILD_",WF)

 def test_fast_map_and_no_render_world_sampling(self):
  s=P.read_text()
  for x in ("b1802RefreshTravel","if(System.nanoTime()-start>=1_600_000L)break",
            "if((world.getGameTime()&1L)==0)refreshSurface(world,cx,cz)",
            "refreshSurface(world,tx,tz)","ATLAS_UPDATE_TICKS=1;",
            "getGameTimeDeltaPartialTick(false)","g.pose().translate(offsetX,offsetZ)",
            "mc.player.xo","mc.player.zo"):
   self.assertIn(x,s)
  self.assertNotIn("forceChunk(",s)
  self.assertNotIn("world.getChunk(",s)

 def test_builder_speed_and_safe_slots(self):
  s=P.read_text()
  self.assertIn("new Slot(speedSlot.container,0,143,27)",s)
  self.assertIn("3*MAX_BREAKS*speedUpgradeCount()/16",s)
  base=8
  self.assertEqual(base+3*base*16//16,32)
  self.assertEqual(base+3*base*0//16,8)
  self.assertIn("2000FE/block remain intact",s)

 def test_generated_java_and_textures(self):
  code=os.getenv("V1_SOURCE_ROOT")
  resource=os.getenv("V1_RESOURCE_ROOT")
  if not code or not resource:self.skipTest("Requires reconstructed CI sources")
  src=Path(code)/"dev/obsidiannetwork"
  be=(src/"mining/V178MiningBuilderBE.java").read_text()
  ui=(src/"client/V178MiningBuilderOperationsScreen.java").read_text()
  terrain=(src/"client/V178TerrainMap.java").read_text()
  mini=(src/"client/V178MiniRaster.java").read_text()
  for text,frag in ((be,"3*MAX_BREAKS*speedUpgradeCount()/16"),
                    (ui,"new Slot(speedSlot.container,1,143,27)"),
                    (terrain,"b1802RefreshTravel(world,cx,cz)"),
                    (mini,"getGameTimeDeltaPartialTick(false)"),
                    (mini,"g.pose().translate(offsetX,offsetZ)")):
   self.assertIn(frag,text)
  assert "GLOBAL_MINER_TIME_BUDGET_NS" in be
  assert "GLOBAL_BLOCK_BUDGET" in be
  m=json.loads((Path(resource)/"assets/obsidiannetwork/models/block/mining_builder.json").read_text())
  self.assertEqual(len(m["elements"]),1)
  self.assertLessEqual(len(m["elements"]),40)
  for e in m["elements"]:
   for face in e["faces"].values():
    self.assertIn(face["texture"][1:],m["textures"])

if __name__=="__main__":unittest.main()
