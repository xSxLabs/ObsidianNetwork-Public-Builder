#!/usr/bin/env python3
"""Fail-closed gates for v1.7.3 postpatch visual fixes."""
import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v173/apply-visual-ingame-fixes-303.py"
WORK=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
class VisualFix303(unittest.TestCase):
 def test_source_contract(self):
  src=PATCH.read_text()
  ast.parse(src)
  for marker in ('V173_ANTENNA_NO_FACE_CULL','noOcclusion()','Shapes.empty()',
       'V173_REAL_3D_GHOST','SubmitCustomGeometryEvent','BlockModelRenderState',
       'extractSlots(GuiGraphicsExtractor','super(menu,inventory,title,286,242);',
       'force_translucent','world.getGameTime()%("map".equals(be.holoMode)?10:40)'):
   self.assertIn(marker,src,marker)
 def test_workflow_order(self):
  self.assertIn("python3 features/v173/apply-visual-ingame-fixes-303.py",WORK)
  self.assertIn("test_v173_visual_ingame_303.py",WORK)
  self.assertLess(WORK.index("python3 features/v173/apply-printer-canonical-materials.py"),
                  WORK.index("python3 features/v173/apply-visual-ingame-fixes-303.py"))
if __name__=="__main__":unittest.main()
