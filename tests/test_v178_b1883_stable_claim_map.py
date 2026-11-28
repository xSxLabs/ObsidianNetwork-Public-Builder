#!/usr/bin/env python3
"""B1883 v20 regressions: moving terrain/claims GPU projection stays identical."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v178/apply-v178-v20-b1883-stable-claim-map.py").read_text("utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text("utf-8")

class StableClaimProjection(unittest.TestCase):
 def test_server_chunks_are_cached_across_snapshot_recenters(self):
  for text in ("B1883_STATUS", "B1883_DIMENSION",
               "B1883_STATUS.remove(key)", "B1883_STATUS.put(key,(byte)st)",
               "B1883_STATUS.clear()", "b1883Receive(message)",
               "Byte.toUnsignedInt(data[(dz+r)*side+dx+r])"):
   self.assertIn(text,PATCH)
 def test_minimap_tint_is_pixel_aligned_with_moving_gpu_terrain(self):
  for text in ("byte[] b1883Claims", "V178ClaimsClient.claimStatus(",
               "claimRev==b1883LastClaimRevision",
               "claimOption==b1883LastClaimsOption",
               "b1883Tint(color,claim,b1883ZBorder||b1883XBorder[px])",
               "img.setPixel(px,py,color)",
               "if(drawClaims&&!drawTerrain)V178TerrainMap.drawClaim"):
   self.assertIn(text,PATCH)
 def test_fullscreen_map_does_not_hide_claims_on_pan_or_grid_toggle(self):
  self.assertIn("V178ClaimsClient.claimStatus(world,cxWorld,czWorld)",PATCH)
  self.assertIn("if(!showClaims)continue; // grid toggle never hides",PATCH)
  self.assertNotIn("if(!grid||!showClaims)continue; //",PATCH)
 def test_preserve_server_protocol_and_client_render_budget(self):
  self.assertNotIn('server/V178Claims.java',PATCH)
  self.assertNotIn("world.getChunk(",PATCH)
  self.assertNotIn("forceChunk(",PATCH)
  self.assertIn("B1799_COLUMN_CHUNK",PATCH)
  self.assertIn("V178MiniRaster.java",PATCH)
 def test_v20_workflow_patch_order_and_version(self):
  self.assertIn("apply-v178-v20-b1883-stable-claim-map.py",WF)
  self.assertIn("test_v178_b1883_stable_claim_map.py",WF)
  self.assertLess(WF.index("apply-v178-v19-b1855-claim-overlay.py"),
                  WF.index("apply-v178-v20-b1883-stable-claim-map.py"))
  self.assertIn("xSxLabs-Network-Storage-1.7.8-v21.jar",WF)
  self.assertIn("xsxlabs-network-storage-1.7.8-v21",WF)
if __name__=="__main__":unittest.main()
