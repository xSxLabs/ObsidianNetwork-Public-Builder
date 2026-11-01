#!/usr/bin/env python3
"""B745: gun emerges from the RIGHT UPPER ARM, not from the forearm/wrist.

Sequence (12 game ticks): first raise right arm (4 ticks), then open a narrow
dorsal upper-arm hatch by 16 degrees (3 ticks), then slide out a compact barrel
on a small fixed bracket (5 ticks). On OFF reverse in the opposite order.
Both player and stand render from the same 3D geometry and phase function.
This patch runs strictly AFTER B739 and changes no FE, combat, recall or suit rig.
"""
import os
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
REL="client/V176MicroMgVisualClient.java"

def edit(old,new):
 p=J/REL
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("V176_B745_ANCHOR_DRIFT",s.count(old),old[:160])
 p.write_text(s.replace(old,new,1),encoding="utf-8")

edit("""      // TOP of extended RIGHT arm: -Z is the upper/dorsal surface at xRot=-80deg.
      // Slim mounted housing, completely above arm's z=-2px surface.
      .texOffs(0,0).addBox(-0.65F,6.0F,-3.55F,1.3F,5.0F,1.0F)
      .texOffs(0,9).addBox(-0.85F,10.5F,-3.85F,1.7F,1.0F,1.65F)
      .texOffs(0,15).addBox(-1.05F,6.0F,-3.70F,2.10F,2.2F,1.30F),""",
"""      // RIGHT UPPER ARM (Y=2 shoulder, Y~7 elbow, Y~12 wrist).
      // Compact barrel, short muzzle and small mounting bracket on dorsal -Z.
      .texOffs(0,0).addBox(-0.55F,3.3F,-3.40F,1.10F,4.6F,1.00F)
      .texOffs(0,9).addBox(-0.75F,7.25F,-3.65F,1.50F,0.85F,1.50F)
      .texOffs(0,15).addBox(-0.95F,3.1F,-3.30F,1.90F,1.70F,1.00F),""")
edit("""      // Upper armor cover, hinged 19deg outward, not the underside/rear face.
      .texOffs(12,0).addBox(-1.35F,6.0F,-3.05F,2.7F,4.3F,0.65F),""",
"""      // Small plate on the upper-arm top (never the forearm).
      .texOffs(12,0).addBox(-1.25F,3.1F,-3.05F,2.5F,3.15F,0.55F),""")
edit("""  float step=0.125F*elapsed;""",
"""  // Twelve ticks: shoulder aim 4, upper-arm hatch 3, barrel slide 5.
  float step=elapsed/12.0F;""")
edit(""" private static Identifier texture(int tier){""",
""" private static float phase(float progress,float begin,float end){
  return Math.max(0.0F,Math.min(1.0F,(progress-begin)/(end-begin)));
 }
 private static Identifier texture(int tier){""")
edit("""  // The top armor hatch opens only 19 degrees; the gun slides along its top.
  pose.pushPose();
  pose.translate(0.0F,7.0F/16.0F,-2.25F/16.0F);
  pose.mulPose(com.mojang.math.Axis.XP.rotationDegrees(-19.0F*extension));
  pose.translate(0.0F,-7.0F/16.0F,2.25F/16.0F);
  nodes.submitModelPart(HATCH,pose,RenderTypes.entitySolid(texture(tier)),
      light,OverlayTexture.NO_OVERLAY,null,false,false,0xFFFFFFFF,null,0);
  pose.popPose();
  // The short barrel physically slides out parallel to the right forearm.
  pose.translate(0.0F,-(1.0F-extension)*0.25F,0.0F);
  nodes.submitModelPart(BARREL,pose,RenderTypes.entitySolid(texture(tier)),
      light,OverlayTexture.NO_OVERLAY,null,false,false,0xFFFFFFFF,null,0);
  pose.popPose();""",
"""  // Sequential deployment, not a simultaneous pop-in.
  float hatchOpen=phase(extension,4.0F/12.0F,7.0F/12.0F);
  float gunOut=phase(extension,7.0F/12.0F,1.0F);
  if(hatchOpen>0.001F){
   pose.pushPose();
   pose.translate(0.0F,3.1F/16.0F,-2.25F/16.0F);
   pose.mulPose(com.mojang.math.Axis.XP.rotationDegrees(-16.0F*hatchOpen));
   pose.translate(0.0F,-3.1F/16.0F,2.25F/16.0F);
   nodes.submitModelPart(HATCH,pose,RenderTypes.entitySolid(texture(tier)),
       light,OverlayTexture.NO_OVERLAY,null,false,false,0xFFFFFFFF,null,0);
   pose.popPose();
  }
  if(gunOut>0.001F){
   pose.pushPose();
   // Concealed in upper arm at first; slides out five model pixels towards elbow.
   pose.translate(0.0F,-(1.0F-gunOut)*0.32F,0.0F);
   nodes.submitModelPart(BARREL,pose,RenderTypes.entitySolid(texture(tier)),
       light,OverlayTexture.NO_OVERLAY,null,false,false,0xFFFFFFFF,null,0);
   pose.popPose();
  }
  pose.popPose();""")
edit(""" private static void drawRight(PoseStack pose,SubmitNodeCollector nodes,int light,
      HumanoidModel<?> model,int tier,float extension){
  if(extension<=0.001F)return;
  float original=model.rightArm.xRot;
  model.rightArm.xRot=original*(1F-extension)-1.40F*extension;
  drawArm(pose,nodes,light,model.rightArm,tier,extension);
  model.rightArm.xRot=original;
 }""",
""" private static void drawRight(PoseStack pose,SubmitNodeCollector nodes,int light,
      HumanoidModel<?> model,int tier,float extension,boolean aimHere){
  if(extension<=0.001F)return;
  float original=model.rightArm.xRot;
  // Worn players were already posed by the Pre event; do not aim twice.
  if(aimHere){
   float raised=phase(extension,0.0F,4.0F/12.0F);
   model.rightArm.xRot=original*(1F-raised)-1.40F*raised;
  }
  drawArm(pose,nodes,light,model.rightArm,tier,extension);
  model.rightArm.xRot=original;
 }""")
edit("""  arm.xRot=arm.xRot*(1F-extend)-1.40F*extend;
  arm.yRot*=1F-extend;
  arm.zRot*=1F-extend;""",
"""  float raised=phase(extend,0.0F,4.0F/12.0F);
  arm.xRot=arm.xRot*(1F-raised)-1.40F*raised;
  arm.yRot*=1F-raised;
  arm.zRot*=1F-raised;""")
edit("""event.getRenderState().lightCoords,event.getRenderer().getModel(),tier,amount);""",
"""event.getRenderState().lightCoords,event.getRenderer().getModel(),tier,amount,false);""")
edit("""state.lightCoords,model,tier,amount);""",
"""state.lightCoords,model,tier,amount,true);""")
edit("""  // Camera-side right arm: raise top-mounted gun above the forearm surface.
  pose.translate(0.14F,-0.035F,-0.12F);
  pose.pushPose();
  pose.mulPose(com.mojang.math.Axis.XP.rotationDegrees(-19.0F));
  event.getSubmitNodeCollector().submitModelPart(HATCH,pose,
    RenderTypes.entitySolid(texture(tier)),event.getPackedLight(),
    OverlayTexture.NO_OVERLAY,null,false,false,0xFFFFFFFF,null,0);
  pose.popPose();
  event.getSubmitNodeCollector().submitModelPart(BARREL,pose,
    RenderTypes.entitySolid(texture(tier)),event.getPackedLight(),
    OverlayTexture.NO_OVERLAY,null,false,false,0xFFFFFFFF,null,0);
  pose.popPose();""",
"""  // First-person weapon sits higher, at the shoulder/upper arm, not the wrist.
  pose.translate(0.14F,-0.18F,-0.08F);
  float progress=extension(player.getId(),true);
  float hatchOpen=phase(progress,4.0F/12.0F,7.0F/12.0F);
  float gunOut=phase(progress,7.0F/12.0F,1.0F);
  if(hatchOpen>0.001F){
   pose.pushPose();
   pose.mulPose(com.mojang.math.Axis.XP.rotationDegrees(-16.0F*hatchOpen));
   event.getSubmitNodeCollector().submitModelPart(HATCH,pose,
     RenderTypes.entitySolid(texture(tier)),event.getPackedLight(),
     OverlayTexture.NO_OVERLAY,null,false,false,0xFFFFFFFF,null,0);
   pose.popPose();
  }
  if(gunOut>0.001F){
   pose.pushPose();
   pose.translate(0.0F,-(1.0F-gunOut)*0.32F,0.0F);
   event.getSubmitNodeCollector().submitModelPart(BARREL,pose,
     RenderTypes.entitySolid(texture(tier)),event.getPackedLight(),
     OverlayTexture.NO_OVERLAY,null,false,false,0xFFFFFFFF,null,0);
   pose.popPose();
  }
  pose.popPose();""")

render=(J/REL).read_text(encoding="utf-8")
assert "model.leftArm" not in render
assert render.count("drawRight(")==3
assert "1.10F,4.6F,1.00F" in render
assert "2.5F,3.15F,0.55F" in render
assert "phase(extension,4.0F/12.0F,7.0F/12.0F)" in render
assert "phase(extension,7.0F/12.0F,1.0F)" in render
assert "amount,false" in render and "amount,true" in render
print("V176_B745_UPPER_RIGHT_ARM_SEQUENTIAL_HATCH_GUN_PASS")
