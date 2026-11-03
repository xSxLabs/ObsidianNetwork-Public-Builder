#!/usr/bin/env python3
"""Fast B982 regressions for the November 3 in-game report.

These checks are source/transaction guardrails; Java compile and game-runtime
verification are provided separately by the complete GitHub Actions build.
"""
from pathlib import Path
import ast
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v176/apply-v176-b982-cell-gun-sound-ingame.py"

class B982PatchContracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.code=PATCH.read_text(encoding="utf-8")

 def test_python_patch_parses_and_uses_current_source_roots(self):
  ast.parse(self.code,filename=str(PATCH))
  self.assertIn('V1_SOURCE_ROOT',self.code)
  self.assertIn('V1_RESOURCE_ROOT',self.code)
  self.assertIn('B982_SOURCE_DRIFT',self.code)

 def test_only_front_overlay_changes_crafting_terminal_geometry(self):
  for x in ('original_faces==json.dumps(model["elements"][:-1]',
            '"faces":{"north":{"uv":[0,0,16,16]',
            'cell_terminal_b982_front.png',
            'ns_violet'):
   self.assertIn(x,self.code)

 def test_network_cable_fallback_loaded_and_identity_filtered(self):
  for x in ('xsxCellTerminalNetwork(', 'NetworkSignalRelayBridge.networkWire(level,cable)',
            'level.hasChunkAt(neighbor)','seen.size()<16384',
            'xsxCellTerminalDrives('):
   self.assertIn(x,self.code)

 def test_real_drive_only_click_transfer_no_phantom_storage(self):
  for x in ('if(slotId==0)', 'if(slotId>0&&slotId<54)return;',
            'DriveMenu.xsxCellTerminalBacking(drive)',
            'backing.setItem(target,one);',
            'ItemStack.matches(backing.getItem(target),one)',
            'carried.shrink(1); // after the real drive confirms',
            'setCarried(carried);','80,56','SHIFT-CLICK'):
   self.assertIn(x,self.code)
  self.assertLess(self.code.index('backing.setItem(target,one);'),
                  self.code.index('carried.shrink(1); // after'))

 def test_third_person_only_barrel_turret_stand_and_first_person_unchanged(self):
  for x in ('XSX_WORLD_BARREL','nodes.submitModelPart(HATCH,pose',
            'xsxlabs_v176_turret',
            'drawRight(xsxTurretPose,event.getSubmitNodeCollector(),',
            'nodes.submitModelPart(BARREL,pose'):
   self.assertIn(x,self.code)
  self.assertIn('B982: no floating plate',self.code)

 def test_turret_activation_anchor_matches_existing_b757_source(self):
  previous=(ROOT/"features/v176/apply-v176-ingame-feedback-757.py").read_text(encoding="utf-8")
  self.assertIn('      (has(chest,"micro_mg_turret_on")||stand.getRightArmPose().x()<-45F);',previous)
  self.assertIn('      (has(chest,"micro_mg_turret_on")||stand.getRightArmPose().x()<-45F);',self.code)

 def test_exact_generated_renderer_and_sound_anchors(self):
  source_paths={
   "b980":ROOT/"features/v176/apply-v176-b980-turret-and-cell-terminal-ingame.py",
   "b675":ROOT/"features/v176/apply-v176-projectile-675.py",
   "b676":ROOT/"features/v176/apply-v176-companion-676.py",
  }
  prior={key:path.read_text(encoding="utf-8") for key,path in source_paths.items()}
  snippets={
   "b980":(
     "       .addBox(-0.62F,5.0F,-3.15F,1.24F,8.5F,1.25F),PartPose.ZERO);",
     "  pose.translate(0.0F,0.0F,-0.075F);"
   ),
   "b675":(
     "  world.playSound(null,p.blockPosition(),SoundEvents.CROSSBOW_SHOOT,\n     SoundSource.PLAYERS,0.45F,1.75F);",
   ),
   "b676":(
     "   world.playSound(null,suit.blockPosition(),SoundEvents.CROSSBOW_SHOOT,\n     SoundSource.PLAYERS,0.45F,1.7F);",
   )
  }
  for key,needles in snippets.items():
   for needle in needles:
    with self.subTest(source=key,needle=needle):
     self.assertIn(needle,prior[key])
     self.assertIn(needle,self.code)

 def test_increased_rate_and_server_origin_sounds(self):
  self.assertIn('20 server-authorized rounds',self.code)
  self.assertIn('tick%5L!=4L',self.code)
  self.assertIn('SoundEvents.FIREWORK_ROCKET_BLAST',self.code)
  self.assertIn('SoundEvents.CROSSBOW_SHOOT',self.code)
  self.assertIn('powerarmor/V176CompanionMode.java',self.code)
  self.assertIn('powerarmor/V176MicroMgFire.java',self.code)

if __name__=="__main__":
 unittest.main()
