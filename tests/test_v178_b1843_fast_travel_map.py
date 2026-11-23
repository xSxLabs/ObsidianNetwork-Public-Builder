#!/usr/bin/env python3
"""v18 fast travel terrain loading: static source and reconstructed Java contract."""
import ast, os, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"features/v178/apply-v178-v18-b1843-fast-travel-map.py"
WORKFLOW=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text("utf-8")

class B1843(unittest.TestCase):
 def test_patch_compiles_and_runs_after_v17(self):
  src=SCRIPT.read_text("utf-8")
  ast.parse(src)
  self.assertIn("python3 features/v178/apply-v178-v18-b1843-fast-travel-map.py",WORKFLOW)
  self.assertLess(WORKFLOW.index("python3 features/v178/apply-v178-v17-b1829.py"),
                  WORKFLOW.index("python3 features/v178/apply-v178-v18-b1843-fast-travel-map.py"))
  self.assertIn("xSxLabs-Network-Storage-1.7.8-v19.jar",WORKFLOW)
  self.assertIn("xsxlabs-network-storage-1.7.8-v19",WORKFLOW)
 def test_only_loaded_missing_chunks_and_bounded_client_tick(self):
  src=SCRIPT.read_text("utf-8")
  for token in ("b1843FillVisible(world,cx,cz,start);",
    "known.containsKey(pos(x,z))||!world.hasChunk(x,z)",
    "System.nanoTime()-start>=2_000_000L","done>=8",
    "b1843Near(world,known,playerCx,playerCz,start,0)",
    "Math.hypot(vx,vz)",
    "V178MiniPreferences.cropPixels()","n<64&&done<8",
    "Math.floorMod(b1843ExploreCursor++,count)"):
   self.assertIn(token,src,token)
  self.assertNotIn("world.getChunk(",src)
  self.assertNotIn("world.getHeight(",src)
  self.assertNotIn("world.setBlock(",src)
 def test_reconstructed_client_sources(self):
  root=os.environ.get("V1_SOURCE_ROOT")
  if not root:self.skipTest("requires built CI sources")
  j=Path(root)/"dev/obsidiannetwork"
  terrain=(j/"client/V178TerrainMap.java").read_text("utf-8")
  mini=(j/"client/V178MiniRaster.java").read_text("utf-8")
  for token in ("b1843FillVisible(world,cx,cz,start)",
     "if(known.containsKey(pos(x,z))||!world.hasChunk(x,z))return done;",
     "b1843Near(world,known,playerCx,playerCz,start,0)",
     "V178MiniPreferences.cropPixels()",
     "V178MiniRaster.tick(world);",
     "updateAtlas(world,cx,cz);",
     "private static final int ATLAS_UPDATE_TICKS=1;"):
   self.assertIn(token,terrain,token)
  self.assertIn("lastCrop*0.50D",mini)
  self.assertIn("B1831_SKIN_ONLY_ROTATING_HEAD",
     (j/"client/V178MapMarkers.java").read_text("utf-8"))

if __name__=="__main__":unittest.main()
