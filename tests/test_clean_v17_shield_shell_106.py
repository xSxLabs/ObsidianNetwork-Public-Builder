#!/usr/bin/env python3
"""Build106 visual-only Draconic-inspired shell regression gates."""
import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v17/apply-power-armor-shield-shell-106.py").read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")
class TestVisual106(unittest.TestCase):
 def test_valid_python(self):ast.parse(PATCH)
 def test_full_3d_mesh_and_actual_render_path(self):
  for k in ('RenderPlayerEvent.Post<?>','submitCustomGeometry(',
            'RenderTypes.entityTranslucent(SKIN)','LATITUDE=16','LONGITUDE=28',
            'for(int y=0;y<LATITUDE;y++)','for(int x=0;x<LONGITUDE;x++)',
            'float impact=Math.min','wearer.hurtTime','alpha+(int)(hit*25F*ripple)',
            'setUv(u,v)','setNormal(pose,nx,s,nz)','FULL_BRIGHT',
            'PowerArmorRuntime.tier(armor,i)!=tier','EnergyTool.energy(armor)<20L',
            'id.equals("energy_shield")','assert not tex.exists()',
            'power_armor_shield_hex.png'):
   self.assertIn(k,PATCH,k)
  self.assertNotIn('mc.level.addParticle(',PATCH)
  self.assertNotIn('ItemStack.EMPTY',PATCH)
 def test_does_not_touch_server_damage_or_restore_pipeline(self):
  self.assertNotIn('PowerArmorEnergyShield.java',PATCH)
  self.assertNotIn('ArmorLoadoutData',PATCH)
  self.assertIn('python3 features/v17/apply-power-armor-shield-shell-106.py',WF)
  self.assertLess(WF.index('apply-power-armor-air-mining-105.py'),WF.index('apply-power-armor-shield-shell-106.py'))
  self.assertIn('BUILD106_3D_HEX_ENERGY_SHELL',WF)
if __name__=="__main__":unittest.main()
