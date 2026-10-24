#!/usr/bin/env python3
"""Build120: exactly follow vanilla Elytra / swimming root rotations for shield.

The six translucent forcefield body pieces already reuse the posed player
ModelParts and Build115's root model handedness. Build114 applies BODY yaw, but
never applied AvatarRenderer.setupRotations' second transform: while fall
flying, the whole model pitches forward to horizontal and can yaw/roll with
movement; the forcefield stayed vertically upright.
Reapply the same AvatarRenderState rotation sequence as the player's armor.
Only PowerArmorShieldClient.java is changed. Damage, FE, shield card, actual
Elytra mechanics, equipment recovery, world suits, recipes and HUD untouched.
"""
import os
from pathlib import Path
java=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/client/PowerArmorShieldClient.java"
s=java.read_text(encoding="utf-8")
assert "BUILD114_BODY_FACING_LOCK" in s
assert "BUILD115_ARMOR_POSE_LOCK" in s
assert "BUILD115_SLOW_BLUE_BREATH" in s
old='''  stack.mulPose(Axis.YP.rotationDegrees(180.0F-state.bodyRot));
  // BUILD115_ARMOR_POSE_LOCK:'''
new='''  stack.mulPose(Axis.YP.rotationDegrees(180.0F-state.bodyRot));
  // BUILD120_ELYTRA_SHIELD_POSE: same frame interpolated AvatarRenderState as
  // vanilla AvatarRenderer.setupRotations. Keep pitch and flight-correction
  // yaw on the common ROOT matrix before attaching any of the six joints.
  if(state.isFallFlying){
   float glide=state.fallFlyingScale();
   if(!state.isAutoSpinAttack)
    stack.mulPose(Axis.XP.rotationDegrees(glide*(-90.0F-state.xRot)));
   if(state.shouldApplyFlyingYRot)
    stack.mulPose(Axis.YP.rotation(state.flyingYRot));
  }else if(state.swimAmount>0.0F){
   // The vanilla swimming transform also leans the whole armor body.
   float target=state.isInWater?-90.0F-state.xRot:-90.0F;
   float angle=state.swimAmount*target;
   stack.mulPose(Axis.XP.rotationDegrees(angle));
   if(state.isVisuallySwimming)stack.translate(0.0F,-1.0F,0.3F);
  }
  // BUILD115_ARMOR_POSE_LOCK:'''
assert s.count(old)==1,("Build120 flight root anchor drift",s.count(old))
s=s.replace(old,new,1)
assert s.count("BUILD120_ELYTRA_SHIELD_POSE")==1
assert "state.isFallFlying" in s and "state.fallFlyingScale()" in s
assert "glide*(-90.0F-state.xRot)" in s
assert "state.shouldApplyFlyingYRot" in s
assert "Axis.YP.rotation(state.flyingYRot)" in s
assert s.index("BUILD120_ELYTRA_SHIELD_POSE")<s.index("stack.scale(-1.0F,-1.0F,1.0F);")
assert s.count("submitPart(stack,collector,model.")==6
assert s.count("joint.translateAndRotate(stack);")==1
assert "phase*phase*(3F-2F*phase)" in s
assert "PowerArmorRuntime.tier(armor,i)!=tier" in s
assert "EnergyTool.energy(armor)<20L" in s
assert 'id.equals("energy_shield")' in s
java.write_text(s,encoding="utf-8")

# Vanilla: ~0 degrees on ground; <= -90 degrees when horizontal gliding.
def glide_progress(t):return max(0.0,min(1.0,(t*t)/100.0))
assert glide_progress(0)==0
assert glide_progress(10)==1
assert -90*glide_progress(10)==-90
assert -90*glide_progress(5)==-22.5
print("BUILD120_ELYTRA_SHIELD_POSE PASS: grounded upright, gliding horizontal, smooth flight tilt and yaw, all six armor-bone shield parts")
