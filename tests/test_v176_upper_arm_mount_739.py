#!/usr/bin/env python3
"""B739 top surface must get the compact single right-arm gun and hatch."""
import os,subprocess,sys,tempfile,unittest
from pathlib import Path
PATCH=Path(__file__).resolve().parents[1]/"features/v176/apply-v176-upper-arm-mount-739.py"

class UpperRightArmFixture(unittest.TestCase):
 def test_actual_top_side_mount(self):
  with tempfile.TemporaryDirectory() as td:
   j=Path(td)/"dev/obsidiannetwork"
   srcs={
    "client/V176MicroMgVisualClient.java":'''
      // Miniature rifle housing INSIDE the forearm; arm local +Y is forward
      // after the right arm raises. Old 9px shoulder-overhanging barrel removed.
      .texOffs(0,0).addBox(-0.8F,6.0F,-1.6F,1.6F,5.5F,1.8F)
      .texOffs(0,9).addBox(-1.1F,10.5F,-1.9F,2.2F,1.3F,2.4F)
      .texOffs(0,15).addBox(-1.25F,6.0F,-1.9F,2.5F,2.8F),
      .texOffs(12,0).addBox(-1.6F,6.0F,1.65F,3.2F,4.6F,0.65F),
  // First the actual rear forearm shell hinges out by only 19 degrees.
  pose.pushPose();
  pose.translate(0.0F,7.0F/16.0F,2.1F/16.0F);
  pose.mulPose(com.mojang.math.Axis.XP.rotationDegrees(-19.0F*extension));
  pose.translate(0.0F,-7.0F/16.0F,-2.1F/16.0F);
  // Only the right first-person forearm; compact arm-mounted muzzle.
  pose.translate(0.14F,0.12F,-0.10F);
 @SubscribeEvent public static void aimRight(RenderPlayerEvent.Pre<?> event){
''',
    "powerarmor/V176MicroMgFire.java":'''
  // Only the wearer's RIGHT wrist has a muzzle. Left arm remains unarmed.
  Vec3 origin=p.getEyePosition().add(dir.scale(0.50D))
             .add(right.scale(0.34D)).add(0,-0.35D,0);
''',
    "powerarmor/V176CompanionMode.java":'''
   // One muzzle, under the RIGHT wrist of the armor.
   Vec3 muzzle=start.add(right.scale(0.34D)).add(0,-0.13D,0);
'''
   }
   for rel,src in srcs.items():
    path=j/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(src)
   env={**os.environ,"V1_SOURCE_ROOT":td}
   run=subprocess.run([sys.executable,str(PATCH)],env=env,capture_output=True,text=True)
   self.assertEqual(run.returncode,0,run.stdout+run.stderr)
   render=(j/"client/V176MicroMgVisualClient.java").read_text()
   self.assertIn(".addBox(-0.65F,6.0F,-3.55F,1.3F,5.0F,1.0F)",render)
   self.assertIn(".addBox(-1.35F,6.0F,-3.05F,2.7F,4.3F,0.65F)",render)
   self.assertNotIn(".addBox(-1.6F,6.0F,1.65F",render)
   self.assertNotIn("model.leftArm",render)
   self.assertIn("7.0F/16.0F,-2.25F/16.0F",render)
   self.assertIn(".add(0,-0.19D,0)",(j/"powerarmor/V176MicroMgFire.java").read_text())
   self.assertIn(".add(0,0.02D,0)",(j/"powerarmor/V176CompanionMode.java").read_text())
   # A duplicate patch must not silently produce a new misaligned mount.
   rerun=subprocess.run([sys.executable,str(PATCH)],env=env,capture_output=True,text=True)
   self.assertNotEqual(rerun.returncode,0)
if __name__=="__main__":unittest.main()
