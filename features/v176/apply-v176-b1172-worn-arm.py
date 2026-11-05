#!/usr/bin/env python3
"""B1172: track actual drawn right-arm pose, mount player-only gun in arm space.

No changes to ArmorStand/turret, first person, suit entry, or gameplay.
"""
import os
from pathlib import Path
P=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
snap=P/"client/V176ThirdPersonArmSnapshot.java"
assert not snap.exists(), "B1172_SNAPSHOT_CLASS_ALREADY_EXISTS"
snap.write_text(r'''package dev.obsidiannetwork.client;

import java.util.Map;
import java.util.WeakHashMap;
import net.minecraft.client.model.Model;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.player.PlayerModel;

/** Last arm transform that really entered Model.renderToBuffer. */
public final class V176ThirdPersonArmSnapshot {
 private V176ThirdPersonArmSnapshot(){}
 private record Angles(float x,float y,float z){}
 private static final Map<Model<?>,Angles> LAST=new WeakHashMap<>();
 public static void capture(Model<?> model){
  if(model instanceof PlayerModel player){
   ModelPart arm=player.rightArm;
   LAST.put(model,new Angles(arm.xRot,arm.yRot,arm.zRot));
  }
 }
 /** Restore the final drawn arm pose for the Post weapon; do not alter turret. */
 public static boolean apply(Model<?> model,ModelPart arm){
  Angles pose=LAST.get(model);
  if(pose==null)return false;
  arm.xRot=pose.x();arm.yRot=pose.y();arm.zRot=pose.z();
  return true;
 }
}
''',encoding="utf-8")
mixin=P/"mixin/V176FinalArmBufferMixin.java"
m=mixin.read_text(encoding="utf-8")
anchor="  dev.obsidiannetwork.client.V176FinalArmPose.apply((Model<?>)(Object)this);"
assert m.count(anchor)==1,("B1172_VERTEX_CAPTURE_ANCHOR",m.count(anchor))
m=m.replace(anchor,anchor+"\n  dev.obsidiannetwork.client.V176ThirdPersonArmSnapshot.capture((Model<?>)(Object)this);",1)
mixin.write_text(m,encoding="utf-8")
v=P/"client/V176MicroMgVisualClient.java"
s=v.read_text(encoding="utf-8")
start=s.index(" @SubscribeEvent public static void wornFallback(")
end=s.index(" public static void drawArm(",start)
w=s[start:end]
actual="    drawArm(pose,event.getSubmitNodeCollector(),state.lightCoords,renderedArm,variant,1.0F);"
assert w.count(actual)==1,("B1172_PLAYER_SUBMIT",w.count(actual))
assert w.count("pose.translate(0.0F,0.065F,0.0F);")==1
w=w.replace("    pose.translate(0.0F,0.065F,0.0F);\n","",1)
w=w.replace(actual,'''    // Snapshot is captured at the actual PlayerModel vertex submission.
    // Post can see a reset rightArm; never use that stale neutral pose.
    var xsxPlayerModel=event.getRenderer().getModel();
    if(!V176ThirdPersonArmSnapshot.apply(xsxPlayerModel,renderedArm))
     renderedArm.xRot=-1.5707964F; // only if a render skipped the capture
    drawArm(pose,event.getSubmitNodeCollector(),state.lightCoords,renderedArm,variant,1.0F,true);''',1)
s=s[:start]+w+s[end:]
begin=s.index(" public static void drawArm(")
next_open=s.index("{",begin)
header=s[begin:next_open]
assert "ModelPart parent,int tier,float extension)" in header,( "B1172_DRAW_SIGNATURE_DRIFT",header)
assert s.count("parent.translateAndRotate(pose);")==1
old_body=s[next_open:]
# Keep legacy six-parameter API for the world turret and all existing callers.
wrapper='''{
  drawArm(pose,nodes,light,parent,tier,extension,false);
 }
 private static void drawArm(PoseStack pose,SubmitNodeCollector nodes,int light,
     ModelPart parent,int tier,float extension,boolean worn){'''
s=s[:next_open]+wrapper+old_body[1:]
begin2=s.index(" private static void drawArm(",begin)
next2=s.index("parent.translateAndRotate(pose);",begin2)
s=s[:next2]+s[next2:].replace("parent.translateAndRotate(pose);",'''parent.translateAndRotate(pose);
  // B1172: move only the worn gun after arm pivot, in LOCAL forearm axes.
  // -Z is dorsal/up when the actual arm rotates forward (-90 deg x).
  if(worn)pose.translate(0.0F,-0.015F,-0.09F);''',1)
assert s.count("if(worn)pose.translate(0.0F,-0.015F,-0.09F);")==1
assert s.count("V176ThirdPersonArmSnapshot.apply(")==1
assert "drawArm(pose,nodes,light,parent,tier,extension,false);" in s
v.write_text(s,encoding="utf-8")
print("B1172_3P_PLAYER_TRUE_RENDERED_ARM_POSE_LOCAL_DORSAL_MOUNT_PASS")
