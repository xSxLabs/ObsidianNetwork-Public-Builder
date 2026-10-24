#!/usr/bin/env python3
"""Build124: multiplayer jet particles for all visible Power Armor flyers."""
import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v17/apply-power-armor-multiplayer-jets-124.py").read_text(encoding="utf-8")
BUILD98=(ROOT/"features/v17/apply-power-armor-build98.py").read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")
class MultiplayerJets124(unittest.TestCase):
 def test_syntax(self):ast.parse(PATCH)
 def test_existing_gate_matches_generated_java(self):
  before=PATCH.split("old='''",1)[1].split("'''",1)[0]
  self.assertIn(before,BUILD98)
 def test_all_players_not_local_only(self):
  for value in ("BUILD124_SHARED_ELYTRA_PARTICLES",
    "for(var p:mc.level.players())","p.distanceToSqr(mc.player)>64D*64D",
    "PowerArmorElytraBridge.chest(p)","p.isFallFlying()",
    "p.isShiftKeyDown()","ParticleTypes.END_ROD",
    "ParticleTypes.CLOUD","for(int limb=0;limb<4;limb++)"):
   self.assertIn(value,PATCH,value)
  self.assertNotIn("ServerLevel.java",PATCH)
  self.assertNotIn("PowerArmorEnergyShield.java",PATCH)
 def test_workflow_order(self):
  self.assertLess(WF.index("apply-power-armor-shader-cutout-122.py"),
                  WF.index("apply-power-armor-multiplayer-jets-124.py"))
  self.assertIn("BUILD124_SHARED_ELYTRA_PARTICLES PASS",WF)
if __name__=="__main__":unittest.main()
