#!/usr/bin/env python3
"""B1014 source guardrails for user-reported v1.7.6 Build 1013 regressions."""
from pathlib import Path
import ast
import unittest
ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v176/apply-v176-b1014-cell-forearm-bullets.py"

class B1014Checks(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.s=PATCH.read_text(encoding="utf-8")

 def test_script_parses_without_regex_or_first_person_edits(self):
  ast.parse(self.s,str(PATCH))
  self.assertIn('B1014_SOURCE_DRIFT',self.s)
  self.assertNotIn('firstPerson(RenderHandEvent',self.s)
  self.assertNotIn('xsxlabs$aimVisibleFirstPersonArm(',self.s)
  self.assertIn('B1014_FIRST_PERSON_GUN_LOST',self.s)

 def test_front_embedded_in_existing_geometry(self):
  for x in ('screens[0]["faces"]["north"]["texture"]="#xsx_cell_front"',
            'obj["elements"].remove(panels[0])',
            'len(obj["elements"])==prior-1',
            'screens[0]["from"][2]>0.0'):
   self.assertIn(x,self.s)

 def test_cell_terminal_item_view_as_3d_model(self):
  for x in ('"parent":"obsidiannetwork:block/cell_terminal"',
            'models/item/cell_terminal.json',
            '"firstperson_righthand"',
            '"thirdperson_righthand"',
            'obsidiannetwork:item/cell_terminal'):
   self.assertIn(x,self.s)

 def test_eight_live_slots_backed_by_actual_drives(self):
  for x in ('range(8)','pad%4','pad/4','if(slotId>=0&&slotId<8)',
            'if(slotId>=8&&slotId<54)',
            'xsxRefresh(world)','xsxRefresh(ServerLevel server)',
            '8 LIVE CELL INPUTS'):
   self.assertIn(x,self.s)
  old=(ROOT/"features/v176/apply-v176-b982-cell-gun-sound-ingame.py").read_text()
  self.assertIn('DriveMenu.xsxCellTerminalBacking(drive)',old)
  self.assertIn('carried.shrink(1); // after the real drive confirms',old)

 def test_world_barrel_and_turret_activation(self):
  for x in ('XSX_WORLD_BARREL','rotationDegrees(4.0F)',
            '6.1F,-2.85F','textures/entity/micro_mg_world_barrel.png',
            'has(chest,"micro_mg_turret_on")',
            'stand.getRightArmPose().x()<-35F',
            'nodes.submitModelPart(BARREL,pose'):
   self.assertIn(x,self.s)

 def test_pointed_projectile_not_iron_nugget(self):
  for x in ('MICRO_MG_ROUND','getDefaultItem(){return ObsidianNetwork.MICRO_MG_ROUND.get();}',
            'models/item/micro_mg_round.json',
            'items/micro_mg_round.json',
            'ctx,0.28F,true'):
   self.assertIn(x,self.s)
  self.assertIn('assert "Items.IRON_NUGGET" not in',self.s)

if __name__=="__main__":unittest.main()
