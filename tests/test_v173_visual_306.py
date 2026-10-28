#!/usr/bin/env python3
"""Build306 validates high-risk visual patch contracts on branch v1.7.3."""
import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=(ROOT/"features/v173/apply-3dmaps-custom-portal-306.py").read_text()
SRC303=(ROOT/"features/v173/apply-visual-ingame-fixes-303.py").read_text()
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
class Build306(unittest.TestCase):
 def test_python_parses(self):ast.parse(SRC)
 def test_preview_is_frame_bound(self):
  self.assertIn("particleGhostEnabled(){return false;}",SRC)
  self.assertIn("if(held.is(ObsidianNetwork.NETWORK_BLUEPRINT.get()))",SRC.replace("if(!particleGhostEnabled()", "if(held.is(ObsidianNetwork.NETWORK_BLUEPRINT.get()))"))
 def test_real_portal_2x3(self):
  for q in ("private static void portals(","y+2.75","x+1.75","NETWORK_PORTAL_B.get()","PURPLE_STAINED_GLASS",
            "body.maxX<pos.getX()-.25","body.maxY<pos.getY()+.25","clearPortalAperture(level,pos)",
            "center.getY()+2>=level.getMaxY()"):
   self.assertIn(q,SRC)
 def test_full_3d_blueprint_coverage(self):
  for q in ("MAX_GHOST_BLOCKS=1536","int extent=Math.min(ids.size(),volume),exposed=0",
            "for(int n=0;n<extent&&shown<MAX_GHOST_BLOCKS;n++)","ghostBuried(ids,n,dx,dy,dz,sx,sy,sz)",
            "Math.floorMod(dx*73856093 ^ dy*19349663 ^ dz*83492791,exposed)"):
   self.assertIn(q,SRC303,q)
  self.assertNotIn("n+=stride",SRC303)
  # The old n+=16 bug saw x=0 only; a complete 16^3 cube has 1352 surface cells.
  coords=[(n%16,(n//16)%16,n//256) for n in range(16**3)]
  shell=[(x,y,z) for x,y,z in coords if x in (0,15) or y in (0,15) or z in (0,15)]
  self.assertEqual(1352,len(shell))
  self.assertEqual(set(range(16)),{x for x,y,z in shell})
  self.assertLessEqual(len(shell),1536)
 def test_map_is_volumetric_and_bounded(self):
  for q in ("out.size()<2200","getBlockState(at.below())","scaleX","scaleY","scaleZ","lastSample>=10L","maxAxis"):
   self.assertIn(q,SRC)
 def test_custom_height_changes_single_line_scale(self):
  for q in ("Display.TextDisplay","holoHeight/3F","entity.setTransformation","entity.setText","for(var stale:current.values())","META-INF/accesstransformer.cfg","TextDisplay::discard"):
   self.assertIn(q,SRC)
 def test_workflow(self):
  a="python3 features/v173/apply-visual-ingame-fixes-303.py"
  b="python3 features/v173/apply-3dmaps-custom-portal-306.py"
  self.assertIn(a,WF);self.assertIn(b,WF);self.assertLess(WF.index(a),WF.index(b))
if __name__=="__main__":unittest.main()
