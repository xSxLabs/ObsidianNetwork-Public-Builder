#!/usr/bin/env python3
"""Build114: lock the six-piece Power Armor shield to the PLAYER's body yaw.

RenderPlayerEvent.Post supplies an entity-local PoseStack after the renderer
has restored its own model transform. Build113 follows individual joints,
but its parent model frame never rotates with AvatarRenderState.bodyRot.
North (player bodyRot=180) happened to match; south and east/west did not.
Apply the same 180-bodyRot Y rotation as vanilla LivingEntityRenderer before
the unchanged Build113 model-space flip, position, and six joint submissions.

Client-only visual correction. No damage/FE, saved data, recipes, items,
armor station, GeckoLib, or gameplay modifications.
"""
import os
import math
from pathlib import Path

p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/client/PowerArmorShieldClient.java"
s=p.read_text(encoding="utf-8")
assert "BUILD111_POSED_ARMOR_SHIELD" in s
assert "BUILD112_MODEL_COORDS" in s
assert "BUILD113_UNMIRRORED_ANIMATION" in s
assert "com.mojang.math.Axis;" not in s
s=s.replace("import com.mojang.blaze3d.vertex.VertexConsumer;\n",
            "import com.mojang.blaze3d.vertex.VertexConsumer;\nimport com.mojang.math.Axis;\n",1)
old='''  stack.pushPose();
  // BUILD113_UNMIRRORED_ANIMATION:'''
new='''  stack.pushPose();
  // BUILD114_BODY_FACING_LOCK: Post runs with the player's model yaw already
  // popped off the event PoseStack. Vanilla uses (180 - bodyRot) degrees about
  // world Y for the whole humanoid; state.bodyRot is interpolated for smooth
  // rotation, unlike discretized block/cardinal facing or camera rotation.
  // Rotate FIRST so the head/limbs inherit it; then convert MODEL Y-down to
  // world Y-up as Build113 already does.
  stack.mulPose(Axis.YP.rotationDegrees(180.0F-state.bodyRot));
  // BUILD113_UNMIRRORED_ANIMATION:'''
assert s.count(old)==1,("shield pose anchor mismatch",s.count(old))
s=s.replace(old,new,1)
assert s.count("stack.mulPose(Axis.YP.rotationDegrees(180.0F-state.bodyRot));")==1
assert s.count("stack.scale(1.0F,-1.0F,1.0F);")==1
assert s.count("stack.translate(0.0F,-1.501F,0.0F);")==1
assert s.count("submitPart(stack,collector,model.")==6
assert "joint.translateAndRotate(stack);" in s
assert "float impact=Math.min" in s
assert 'id.equals("energy_shield")' in s
assert "EnergyTool.energy(armor)<20L" in s
p.write_text(s,encoding="utf-8")

# Vanilla: north=180 body yaw, south=0, east=-90, west=90.
# Before rotation our capsule's front faces north (model -Z).
# A proper player-relative shield front MUST always match each direction.
def model_front(body_yaw):
 a=math.radians(180-body_yaw)
 return (round(-math.sin(a)),round(-math.cos(a)))
assert model_front(180)==(0,-1),model_front(180)
assert model_front(0)==(0,1),model_front(0)
assert model_front(-90)==(1,0),model_front(-90)
assert model_front(90)==(-1,0),model_front(90)
# Both head and the moving limb joints share this parent transform.
assert s.index("stack.mulPose(Axis.YP.rotationDegrees(180.0F-state.bodyRot));") < s.index("submitPart(stack,collector,model.head")
print("BUILD114_BODY_FACING_LOCK PASS: exact north/south/east/west player-body rotation plus all six animated limbs; energy/damage preserved")
