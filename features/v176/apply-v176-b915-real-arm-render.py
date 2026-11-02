#!/usr/bin/env python3
"""B915: apply Attack Mode pose to actual rendered PlayerModel/armor geometry.
Uses the final Model vertex pass, not the earlier independent gun layer.
"""
import os,json
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])
def edit(rel,old,new):
 p=J/rel;s=p.read_text()
 assert s.count(old)==1,("B915_ARM_SOURCE_DRIFT",rel,s.count(old),old[:75])
 p.write_text(s.replace(old,new,1))
def add(rel,text):
 p=J/rel
 assert not p.exists(),("B915_DUPLICATE_CLASS",rel)
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(text)
add("client/V176FinalArmPose.java",'''package dev.obsidiannetwork.client;
import net.minecraft.client.model.Model;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.player.PlayerModel;
import net.minecraft.client.renderer.entity.state.HumanoidRenderState;
import java.util.Map;
import java.util.WeakHashMap;
/** Store exact mode from this model's most recent animation state.
 * Render submission may be deferred; the weapon layer is not the player arm.
 */
public final class V176FinalArmPose {
 private V176FinalArmPose(){}
 private static final Map<Model<?>,Boolean> ACTIVE=new WeakHashMap<>();
 public static void track(Model<?> model,HumanoidRenderState state){
  ACTIVE.put(model,V176AttackPoseContext.aim(state));
 }
 public static void apply(Model<?> model){
  if(!Boolean.TRUE.equals(ACTIVE.get(model)) || !(model instanceof HumanoidModel<?> h))return;
  h.rightArm.xRot=-1.5707964F;
  h.rightArm.yRot=0F;h.rightArm.zRot=0F;
  h.rightArm.visible=true;
  if(model instanceof PlayerModel p){
   p.rightSleeve.xRot=h.rightArm.xRot;
   p.rightSleeve.yRot=0F;p.rightSleeve.zRot=0F;
   p.rightSleeve.visible=true;
  }
 }
}
''')
add("mixin/V176FinalArmBufferMixin.java",'''package dev.obsidiannetwork.mixin;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraft.client.model.Model;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
/** Pose the REAL right arm when the model's vertices are emitted. */
@Mixin(Model.class)
public abstract class V176FinalArmBufferMixin {
 @Inject(method="renderToBuffer(Lcom/mojang/blaze3d/vertex/PoseStack;Lcom/mojang/blaze3d/vertex/VertexConsumer;III)V",at=@At("HEAD"),require=1)
 private void xsxlabs$lastArmPose(PoseStack pose,VertexConsumer vc,
             int light,int overlay,int color,CallbackInfo ci){
  dev.obsidiannetwork.client.V176FinalArmPose.apply((Model<?>)(Object)this);
 }
}
''')
edit("mixin/V176AttackPlayerModelMixin.java",
 " private void xsxlabs$aimRightArmLast(AvatarRenderState state,CallbackInfo callback){",
 " private void xsxlabs$aimRightArmLast(AvatarRenderState state,CallbackInfo callback){\n  dev.obsidiannetwork.client.V176FinalArmPose.track((Model<?>)(Object)this,state);")
edit("mixin/V176AttackRightArmMixin.java",
 " private void xsxlabs$forwardArmedRightArm(HumanoidRenderState state,CallbackInfo callback){",
 " private void xsxlabs$forwardArmedRightArm(HumanoidRenderState state,CallbackInfo callback){\n  dev.obsidiannetwork.client.V176FinalArmPose.track((Model<?>)(Object)this,state);")
mx=R/"obsidiannetwork.mixins.json"
data=json.loads(mx.read_text())
assert "V176FinalArmBufferMixin" not in data["client"]
data["client"].append("V176FinalArmBufferMixin")
mx.write_text(json.dumps(data,indent=2)+"\n")
print("B915_REAL_PLAYER_RIGHT_ARM_BUFFER_POSE_AND_ARMOR_MODEL_GUARD_PASS")
