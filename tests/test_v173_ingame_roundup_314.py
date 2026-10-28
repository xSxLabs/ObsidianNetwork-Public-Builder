#!/usr/bin/env python3
"""Regression contract for user-reported v1.7.3 Build313 field defects."""
import ast
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v173/apply-ingame-roundup-314.py").read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")

class IngameRoundup314(unittest.TestCase):
 def test_syntax(self):
  ast.parse(PATCH)
 def test_screen_no_vanilla_menu_hover(self):
  for marker in ('HologramConfigScreen extends Screen',
                 'V173_HOLO_SLOT_FREE_314',
                 'minecraft.player.closeContainer()',
                 'HEIGHT 1 = 1 block below holo table'):
   self.assertIn(marker,PATCH,marker)
  self.assertNotIn('extends AbstractContainerScreen',PATCH)
 def test_map_is_terrain_and_radius_is_chunks(self):
  for marker in ('radiusChunks*16','Heightmap.Types.WORLD_SURFACE',
                'double footprint=2.5D+radiusChunks*1.25D',
                'radius=radiusChunks*16','originY=t.getY()-be.holoHeight()',
                'min<y&&out.size()<4200'):
   self.assertIn(marker,PATCH,marker)
 def test_height_vs_size(self):
  for marker in ('holoWidth/3F','worldPosition.getY()-holoHeight+.5',
                'holoRadius=Math.max(1,Math.min(12,radius))',
                'size.visible=!map','radius.visible=map',
                'content.visible=custom'):
   self.assertIn(marker,PATCH,marker)
 def test_portal_no_legacy_double_and_fast_spawn(self):
  for marker in ('RenderShape.INVISIBLE','lastPortalScan>=2L',
                 'One continuous tinted membrane','1.5,2.5,.055'):
   self.assertIn(marker,PATCH,marker)
 def test_wheel_release_and_owner_only_rename(self):
  for marker in ('activate(selected)','RELEASE G','PortalRenamePayload',
                'index.rename(player.getUUID(),a.uid(),clean)',
                'Only the owner can rename this Portal A.'):
   self.assertIn(marker,PATCH,marker)
 def test_workflow_contract(self):
  a='python3 features/v173/apply-3dmaps-custom-portal-306.py'
  b='python3 features/v173/apply-ingame-roundup-314.py'
  self.assertIn(a,WF);self.assertIn(b,WF)
  self.assertLess(WF.index(a),WF.index(b))
  self.assertIn('test_v173_ingame_roundup_314.py',WF)

if __name__=="__main__":unittest.main()
