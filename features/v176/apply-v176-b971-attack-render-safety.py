#!/usr/bin/env python3
"""B971: B970 in-game regression repairs. Generated-source patch after B966.

- Bring back the first-person Micro-MG for empty main hand.
- Preserve the vanilla shoulder, yaw only the segmented right forearm.
- Submit the first-person gun exactly once from the main-hand render pass.
- Isolate third-person weapon and backpack model submissions from shared
  player PoseStack state, including an exception path.

The crash report confirms a pose-stack imbalance in LevelRenderer but cannot
prove which rendering mod caused it. This patch does not claim to repair
unrelated renderer mixins. All source edits fail closed on unexpected drift.
"""
import os
from pathlib import Path

ROOT = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork"

def change(path, old, new):
    file = ROOT / path
    text = file.read_text(encoding="utf-8")
    found = text.count(old)
    assert found == 1, ("B971_SOURCE_DRIFT", path, found, old[:150])
    file.write_text(text.replace(old, new, 1), encoding="utf-8")

gun_path = "client/V176MicroMgVisualClient.java"
gun = ROOT / gun_path
source = gun.read_text(encoding="utf-8")
assert source.count("xsxlabs$aimVisibleFirstPersonArm(RenderArmEvent event)") == 1, "B971_MISSING_SEGMENTED_ARM"
assert source.count("firstPerson(RenderHandEvent event)") == 1, "B971_MISSING_HAND_PASS"

# B966 accidentally reintroduced the exact empty-main-hand rejection which
# B933 had removed. The main-hand callback must render in Attack Mode empty hand.
change(gun_path,
       "  if(progress<=0.001F||event.getItemStack().isEmpty())return;",
       "  if(progress<=0.001F)return;")

# The shoulder remains at its stock vanilla position; change only the child
# forearm pivot. The gun in the hand camera pass gets corresponding yaw.
change(gun_path,
       "  pose.mulPose(com.mojang.math.Axis.YP.rotationDegrees(32.0F*bend));",
       "  pose.mulPose(com.mojang.math.Axis.YP.rotationDegrees(42.0F*bend));")
change(gun_path,
       "  pose.translate(0.43F,-0.30F,-0.53F);",
       "  pose.translate(0.43F,-0.30F,-0.53F);\n  pose.mulPose(com.mojang.math.Axis.YP.rotationDegrees(42.0F));")

# Avoid two weapon meshes in the same first-person frame: draw the segmented
# right forearm in RenderArmEvent, and the single barrel in RenderHandEvent.
# This also covers vanilla's empty-hand path when the arm event is skipped.
old_arm_gun = """  float gunOut=phase(progress,7.0F/12.0F,1.0F);
  if(gunOut>0.001F){
   pose.pushPose();
   pose.translate(-5.0F/16.0F,2.0F/16.0F,0.0F);
   pose.translate(0.0F,-(1.0F-gunOut)*0.32F,0.0F);
   nodes.submitModelPart(BARREL,pose,RenderTypes.entitySolid(texture(equippedTier)),
      light,OverlayTexture.NO_OVERLAY,null,false,false,0xFFFFFFFF,null,0);
   pose.popPose();
  }
"""
change(gun_path, old_arm_gun,
       "  // One barrel only: the main-hand renderer submits it for both empty and held hands.\n")

# The attack-mode player layer is a third-person hot path. Always bracket its
# renderer submission, so a partial render cannot leave the caller's matrix
# in its local arm frame. drawArm has its own nested matched push/pop.
layer_path = "client/V176MicroMgLayer.java"
change(layer_path,
       """  V176MicroMgVisualClient.drawArm(pose,nodes,light,
      getParentModel().rightArm,tier,deployment);""",
       """  pose.pushPose();
  try {
   V176MicroMgVisualClient.drawArm(pose,nodes,light,
       getParentModel().rightArm,tier,deployment);
  } finally {
   pose.popPose();
  }""")

# Keep the user's enlarged backpack, but guard the render state independently
# from the player weapon layer. Never modify the backpack's accepted textures.
bag_path = "client/V176BackpackWornRenderer.java"
change(bag_path,
       """  model.submit(pose,event.getSubmitNodeCollector(),
       event.getRenderState().lightCoords,OverlayTexture.NO_OVERLAY,0);
  pose.popPose();""",
       """  try {
   model.submit(pose,event.getSubmitNodeCollector(),
       event.getRenderState().lightCoords,OverlayTexture.NO_OVERLAY,0);
  } finally {
   pose.popPose();
  }""")

source = gun.read_text(encoding="utf-8")
arm_start = source.index(" @SubscribeEvent public static void xsxlabs$aimVisibleFirstPersonArm(RenderArmEvent event){")
arm_end = source.index(" @SubscribeEvent public static void worldSuit(", arm_start)
arm = source[arm_start:arm_end]
hand_start = source.index(" @SubscribeEvent public static void firstPerson(RenderHandEvent event){")
hand_end = source.index(" @SubscribeEvent public static void xsxlabs$aimVisibleFirstPersonArm(", hand_start)
hand = source[hand_start:hand_end]
assert "event.setCanceled(true);" in arm
assert "submitModelPart(BARREL" not in arm
assert "submitModelPart(BARREL" in hand
assert "event.getItemStack().isEmpty())return" not in hand
assert "rotationDegrees(42.0F*bend)" in arm
assert "pose.translate(-5.0F/16.0F,6.0F/16.0F,0.0F);" in arm
assert arm.count("pose.pushPose();") == arm.count("pose.popPose();"), "B971_FIRSTPERSON_STACK_BALANCE"
assert hand.count("pose.pushPose();") == hand.count("pose.popPose();"), "B971_HAND_STACK_BALANCE"
assert "pose.scale(1.00F,1.00F,1.00F);" in (ROOT / bag_path).read_text(encoding="utf-8")
assert "finally" in (ROOT / layer_path).read_text(encoding="utf-8")
print("B971_FIRSTPERSON_EMPTY_HAND_BARREL_ONCE_FOREARM_YAW_POSE_SCOPES_PASS")
