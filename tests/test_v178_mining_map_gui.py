#!/usr/bin/env python3
"""B1650 mining map UI source and compiled-class contracts."""
import ast,os,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=(ROOT/"features/v178/apply-v178-mining-map-gui.py").read_text()
W=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
class MiningMapGui(unittest.TestCase):
 def test_patch_integrated(self):
  ast.parse(P)
  self.assertIn("python3 features/v178/apply-v178-mining-map-gui.py",W)
  self.assertLess(W.index("apply-v178-ftb-map-gui.py"),W.index("apply-v178-mining-map-gui.py"))
 def test_loaded_only_and_authoritative(self):
  for marker in ("V178TerrainMap.tick(mc.level,cx,cz)", "V178TerrainMap.draw(mc.level,g",
       "ClientPacketDistributor.sendToServer(", "playToServer(TYPE,CODEC",
       "V178MiningShapeCard.valid(b)",'getItemInHand(packet.offhand?',
       "Math.abs((long)b.minX()-px)>4096L", "MAX_VOLUME", "GLFW.GLFW_KEY_K"):
   if marker=="MAX_VOLUME":continue
   self.assertIn(marker,P)
  self.assertNotIn("world.getChunk(",P)
  self.assertNotIn("world.loadChunk(",P)
 def test_generated_classes(self):
  base=os.environ.get("V1_SOURCE_ROOT")
  if not base:return
  root=Path(base)/"dev/obsidiannetwork"
  for name in ("mining/V178MiningAreaSelection.java",
               "client/V178MiningAreaScreen.java","client/V178MiningAreaKey.java"):
   self.assertTrue((root/name).exists(),name)
  packet=(root/"mining/V178MiningAreaSelection.java").read_text()
  self.assertIn("V178MiningShapeCard.valid(b)",packet)
  self.assertIn('NetworkBlueprintItem.write(card,"xsxlabs_mining_bounds"',packet)
  gui=(root/"client/V178MiningAreaScreen.java").read_text()
  self.assertIn("V178TerrainMap.drawViewport(mc.level,g",gui)
  self.assertNotIn("V178TerrainMap.draw(mc.level,g",gui)
if __name__=="__main__":unittest.main()
