#!/usr/bin/env python3
"""B739: top-mounted single right-arm gun, never below right arm.

During a forward 80deg right-arm aim, the *negative local Z surface* of the
Humanoid right-arm cube is the upward-facing (dorsal) surface. Keep the gun
parallel to the right wrist but put its geometry and opening armor panel
entirely above that upper surface. Also align actual physical muzzle height.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def edit(rel,before,after):
 p=J/rel
 s=p.read_text(encoding="utf8")
 assert s.count(before)==1,("V176_B739_SOURCE_DRIFT",rel,s.count(before),before[:125])
 p.write_text(s.replace(before,after,1),encoding="utf8")

rel="client/V176MicroMgVisualClient.java"
edit(rel,
 '''      // Miniature rifle housing INSIDE the forearm; arm local +Y is forward
      // after the right arm raises. Old 9px shoulder-overhanging barrel removed.
      .texOffs(0,0).addBox(-0.8F,6.0F,-1.6F,1.6F,5.5F,1.8F)
      .texOffs(0,9).addBox(-1.1F,10.5F,-1.9F,2.2F,1.3F,2.4F)
      .texOffs(0,15).addBox(-1.25F,6.0F,-1.9F,2.5F,2.8F,2.8F),''',
 '''      // TOP of extended RIGHT arm: -Z is the upper/dorsal surface at xRot=-80deg.
      // Slim mounted housing, completely above arm's z=-2px surface.
      .texOffs(0,0).addBox(-0.65F,6.0F,-3.55F,1.3F,5.0F,1.0F)
      .texOffs(0,9).addBox(-0.85F,10.5F,-3.85F,1.7F,1.0F,1.65F)
      .texOffs(0,15).addBox(-1.05F,6.0F,-3.70F,2.10F,2.2F,1.30F),''')
edit(rel,
 '''      .texOffs(12,0).addBox(-1.6F,6.0F,1.65F,3.2F,4.6F,0.65F),''',
 '''      // Upper armor cover, hinged 19deg outward, not the underside/rear face.
      .texOffs(12,0).addBox(-1.35F,6.0F,-3.05F,2.7F,4.3F,0.65F),''')
edit(rel,
 '''  // First the actual rear forearm shell hinges out by only 19 degrees.
  pose.pushPose();
  pose.translate(0.0F,7.0F/16.0F,2.1F/16.0F);
  pose.mulPose(com.mojang.math.Axis.XP.rotationDegrees(-19.0F*extension));
  pose.translate(0.0F,-7.0F/16.0F,-2.1F/16.0F);''',
 '''  // The top armor hatch opens only 19 degrees; the gun slides along its top.
  pose.pushPose();
  pose.translate(0.0F,7.0F/16.0F,-2.25F/16.0F);
  pose.mulPose(com.mojang.math.Axis.XP.rotationDegrees(-19.0F*extension));
  pose.translate(0.0F,-7.0F/16.0F,2.25F/16.0F);''')
edit(rel,
 '''  // Only the right first-person forearm; compact arm-mounted muzzle.
  pose.translate(0.14F,0.12F,-0.10F);''',
 '''  // Camera-side right arm: raise top-mounted gun above the forearm surface.
  pose.translate(0.14F,-0.035F,-0.12F);''')
edit(rel,
 '''  pose.mulPose(com.mojang.math.Axis.XP.rotationDegrees(-19.0F));''',
 '''  pose.mulPose(com.mojang.math.Axis.XP.rotationDegrees(-19.0F));''') if False else None
edit("powerarmor/V176MicroMgFire.java",
 '''  // Only the wearer's RIGHT wrist has a muzzle. Left arm remains unarmed.
  Vec3 origin=p.getEyePosition().add(dir.scale(0.50D))
             .add(right.scale(0.34D)).add(0,-0.35D,0);''',
 '''  // TOP of the wearer's RIGHT forward arm (left is never armed).
  Vec3 origin=p.getEyePosition().add(dir.scale(0.50D))
             .add(right.scale(0.34D)).add(0,-0.19D,0);''')
edit("powerarmor/V176CompanionMode.java",
 '''   // One muzzle, under the RIGHT wrist of the armor.
   Vec3 muzzle=start.add(right.scale(0.34D)).add(0,-0.13D,0);''',
 '''   // One muzzle mounted on TOP of the RIGHT armored wrist.
   Vec3 muzzle=start.add(right.scale(0.34D)).add(0,0.02D,0);''')
render=(J/rel).read_text(encoding="utf8")
assert "model.leftArm" not in render
assert ".addBox(-0.65F,6.0F,-3.55F,1.3F,5.0F,1.0F)" in render
assert ".addBox(-1.35F,6.0F,-3.05F,2.7F,4.3F,0.65F)" in render
assert "7.0F/16.0F,-2.25F/16.0F" in render
assert "RenderPlayerEvent.Pre<?>" in render
print("V176_B739_RIGHT_ARM_TOP_MOUNT_HATCH_ALIGNMENT_PASS")
