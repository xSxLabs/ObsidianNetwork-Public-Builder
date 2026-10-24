#!/usr/bin/env python3
"""Build119: compact FE meter to the right, above vanilla hunger icons."""
import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v17/apply-power-armor-compact-hud-119.py").read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")
class CompactHud119(unittest.TestCase):
 def test_valid_patch(self):ast.parse(PATCH)
 def test_right_side_above_food(self):
  for m in ('BUILD119_HUNGER_ALIGNED_COMPACT_HUD',
            'getGuiScaledWidth()/2+10','getGuiScaledHeight()-59',
            'final int width=80;','mc.font.width(percent)',
            'g.fill(x,y+8,x+width,y+10',
            'stored+=Math.max(0L,EnergyTool.energy(item));'):
   self.assertIn(m,PATCH,m)
  self.assertNotIn("PowerArmorEnergyShield.java",PATCH)
  self.assertNotIn("PowerArmorSuitWorld.java",PATCH)
 def test_overlay_follows_existing_features(self):
  self.assertLess(WF.index('apply-power-armor-exit-facing-117.py'),
                  WF.index('apply-power-armor-compact-hud-119.py'))
  self.assertIn("BUILD119_HUNGER_ALIGNED_COMPACT_HUD PASS",WF)
if __name__=="__main__":unittest.main()
