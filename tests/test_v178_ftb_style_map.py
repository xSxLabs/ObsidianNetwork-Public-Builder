#!/usr/bin/env python3
"""B1621: FTB-style original claim+chunkloading GUI and terrain map regression contract."""
import os,ast,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
W=(R/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
A=(R/"features/v178/apply-v178-ftb-batch.py").read_text()
B=(R/"features/v178/apply-v178-ftb-map-gui.py").read_text()
class FtbStyleMap(unittest.TestCase):
 def test_source_order_and_previous_full_mod_features(self):
  for filename in ("apply-v178-claims.py","apply-v178-mining-builder.py",
                   "apply-v178-ftb-batch.py","apply-v178-ftb-map-gui.py",
                   "apply-v178-jei-terminal-session.py","apply-v178-jarvis-hud.py",
                   "apply-v178-global-perf.py"):
   self.assertIn("python3 features/v178/"+filename,W)
  self.assertLess(W.index("python3 features/v178/apply-v178-claims.py"),
                  W.index("python3 features/v178/apply-v178-ftb-batch.py"))
  self.assertLess(W.index("python3 features/v178/apply-v178-ftb-batch.py"),
                  W.index("python3 features/v178/apply-v178-ftb-map-gui.py"))
 def test_static_contracts(self):
  ast.parse(A);ast.parse(B)
  for marker in ("GLOBAL", "BATCHES","LAST_BATCH","runBatches",
                 "perPlayer++<8","global=64","queueBatch",
                 "mode<0||mode>3","Math.abs((long)highX-px)>256",
                 "dirty=true","playToServer(TYPE,CODEC"):
   self.assertIn(marker if marker!="GLOBAL" else "global=64",A)
  for marker in ("V178TerrainMap.java","world.hasChunk(cx,cz)",
                 "Heightmap.Types.WORLD_SURFACE","MAX_CACHED=1536",
                 "RES=4","V178ClaimsBatch","e.modifiers()&GLFW.GLFW_MOD_SHIFT",
                 "mouseDragged(MouseButtonEvent","mouseReleased(MouseButtonEvent",
                 "mouseScrolled(double mx,double my,double horizontal,double vertical)",
                 "GLFW.GLFW_KEY_C","GLFW.GLFW_KEY_SPACE",
                 "Button.builder","V178TerrainMap.drawClaim"):
   self.assertIn(marker,B)
  self.assertNotIn("world.getChunk(",B)
  self.assertNotIn("forceChunk(",B)
  self.assertNotIn("sendCommand(",B)
 def test_stale_claim_snapshot_retry_is_tick_bounded(self):
  # A map moved during server-side throttling must recover by retrying.
  for marker in ("pending.cx()!=screen.centerX()",
                 "pending.cz()!=screen.centerZ()",
                 "!pending.dimension().equals",
                 "now-lastRequestTime>=25",
                 "request(screen.centerX(),screen.centerZ())"):
   self.assertIn(marker,B)
  self.assertIn("V178TerrainMap.tick(mc.level,playerCx,playerCz)",B)
 def test_compiled_source_contract(self):
  if not os.environ.get("V1_SOURCE_ROOT"):return
  j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
  for f in ("claims/V178Claims.java","claims/V178ClaimsBatch.java",
            "client/V178TerrainMap.java","client/V178ClaimsMapScreen.java",
            "client/V178ClaimsClient.java"):
   self.assertTrue((j/f).exists(),f)
  claims=(j/"claims/V178Claims.java").read_text()
  self.assertIn("perPlayer++<8",claims)
  self.assertIn("global=64",claims)
  gui=(j/"client/V178ClaimsMapScreen.java").read_text()
  self.assertIn("e.modifiers()&GLFW.GLFW_MOD_SHIFT",gui)
  self.assertIn("V178TerrainMap.draw(world,g",gui)
  terrain=(j/"client/V178TerrainMap.java").read_text()
  self.assertIn("world.hasChunk(cx,cz)",terrain)
  self.assertNotIn("loadChunk(",terrain)
if __name__=="__main__":unittest.main()
