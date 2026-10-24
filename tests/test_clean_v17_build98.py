#!/usr/bin/env python3
"""Build 98 combined safety contract test (generated Java compiled in Actions)."""
import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=(ROOT/"features/v17/apply-power-armor-build98.py").read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")
class Build98(unittest.TestCase):
 def test_patch_parses(self):ast.parse(SRC)
 def test_exit_does_not_clear_arbitrary_blocks(self):
  for q in ("Blocks.LIGHT","Blocks.SNOW","Blocks.SHORT_GRASS","Blocks.TALL_GRASS",
            "Blocks.DEAD_BUSH","BlockTags.FLOWERS",
            "suitVolumeClearable(level,pos)","if(!level.addFreshEntity(stand))",
            "level.setBlock(pos,oldLower,3)","level.setBlock(pos.above(),oldUpper,3)"):
   self.assertIn(q,SRC)
  self.assertNotIn("BlockTags.REPLACEABLE)",SRC)
  self.assertNotIn("level.destroyBlock(",SRC)
 def test_actionbar_not_chat(self):
  self.assertIn("ClientboundSetActionBarTextPacket(",SRC)
  self.assertIn('"message.obsidiannetwork.power_armor.night_on"',SRC)
  self.assertIn('"message.obsidiannetwork.power_armor.night_off"',SRC)
 def test_particles_and_percent(self):
  for q in ("RenderGuiEvent.Post","EnergyTool.capacity(item)","EnergyTool.energy(item)",
   "pct+\"%\"","ParticleTypes.END_ROD","ParticleTypes.CLOUD",
   "PowerArmorElytraBridge.chest(p)","p.isFallFlying()",
   "boolean boost=p.isShiftKeyDown()"):
   self.assertIn(q,SRC)
 def test_real_mk_arm_texture_not_player_skin(self):
  for q in ("RenderArmEvent","PowerArmorRuntime.tier(","event.setCanceled(true)",
            "textures/entity/equipment/humanoid","power_armor_firstperson_mk",
            "image[16+y][40+x]","image[16+y][55-x]"):
   self.assertIn(q,SRC)
  self.assertIn("for tier in range(1,25):",SRC)
 def test_ci_order(self):
  self.assertLess(WF.index("python3 features/v17/apply-power-armor-jade-95.py"),
                  WF.index("python3 features/v17/apply-power-armor-build98.py"))
  self.assertIn("BUILD102_24_FIRST_PERSON_ARM_ASSETS PASS",WF)
if __name__=="__main__":unittest.main()
