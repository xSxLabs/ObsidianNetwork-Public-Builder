#!/usr/bin/env python3
"""B750 regression fixture covers the actual post-B745 contracts."""
import ast,os,subprocess,sys,tempfile,unittest
from pathlib import Path
PATCH=Path(__file__).resolve().parents[1]/"features/v176/apply-v176-ingame-visual-follow-750.py"

class InGameFeedback750(unittest.TestCase):
 def test_sync_visual_and_walk_patch(self):
  tree=ast.parse(PATCH.read_text(encoding="utf-8"))
  calls=[x.value for x in tree.body if isinstance(x,ast.Expr) and
         isinstance(x.value,ast.Call) and isinstance(x.value.func,ast.Name)
         and x.value.func.id=="edit"]
  self.assertEqual(len(calls),9)
  per={}
  for x in calls:
   rel,old=[ast.literal_eval(z) for z in x.args[:2]]
   per.setdefault(rel,[]).append(old)
  with tempfile.TemporaryDirectory() as td:
   for rel,olds in per.items():
    p=Path(td)/"dev/obsidiannetwork"/rel
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text("\n".join(olds),encoding="utf-8")
   env={**os.environ,"V1_SOURCE_ROOT":td}
   run=subprocess.run([sys.executable,str(PATCH)],env=env,capture_output=True,text=True)
   self.assertEqual(run.returncode,0,run.stdout+run.stderr)
   self.assertIn("V176_B750_VISIBLE_AIM_WEAPON_AND_FOLLOW_WALK_POSES_PASS",run.stdout)
   j=Path(td)/"dev/obsidiannetwork"
   w=(j/"client/V176MicroMgVisualClient.java").read_text()
   a=(j/"powerarmor/V176AttackModeServer.java").read_text()
   c=(j/"powerarmor/V176CompanionMode.java").read_text()
   self.assertIn("submitModelPart(model.rightArm",w)
   self.assertIn("firstPersonWithItem(RenderHandEvent event)",w)
   self.assertIn("wornArmorTexture(tier)",w)
   self.assertIn("walkingPose(suit,walking",c)
   self.assertIn("setLeftLegPose",c)
   self.assertIn("setRightLegPose",c)
   self.assertIn("setRightArmPose",c)
   self.assertIn("p.setItemSlot(EquipmentSlot.CHEST,chest.copy());",a)
   again=subprocess.run([sys.executable,str(PATCH)],env=env,capture_output=True,text=True)
   self.assertNotEqual(again.returncode,0)
 def test_follow_swing_and_turret_aim_contract(self):
  import math
  for tick in (0,1,2,3,4,5,6,7,8,9,10):
   swing=math.sin(tick*.72)*24
   self.assertTrue(-24.01<=swing<=24.01)
   left_leg=swing;right_leg=-swing
   self.assertAlmostEqual(left_leg+right_leg,0)
  src=PATCH.read_text()
  self.assertIn("turret?-80F:swing*0.75F",src)
  self.assertIn("near>3.5D*3.5D && near<14D*14D",src)
  self.assertIn("if(was)walkingPose(suit,false,false",src)
if __name__=="__main__":unittest.main()
