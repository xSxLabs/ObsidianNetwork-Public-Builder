#!/usr/bin/env python3
"""B1096: player-only third-person world barrel seats above right forearm.

The video from B1095 shows the silver barrel below the lifted right forearm.
Turret is correct: preserve the entire shared drawArm() mesh, ArmorStand
post renderer, and all first-person methods byte-for-byte. Correct only the
player's wornFallback POST model-space submission offset. Do not create a
second projectile or move the actual player's arm by this visual patch.
"""
import os
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/client/V176MicroMgVisualClient.java"
s=p.read_text(encoding="utf-8")
start=s.index(" @SubscribeEvent public static void wornFallback(")
end=s.index(" public static void drawArm(",start)
worn=s[start:end]
old="    drawArm(pose,event.getSubmitNodeCollector(),state.lightCoords,renderedArm,variant,1.0F);"
new="""    // B1096_PLAYER_ONLY_FOREARM_CONTACT: restore the barrel to the raised
    // right forearm's dorsal face in POST model-space (not world/turret space).
    // With the inherited -Y humanoid transform, negative Y is above the arm.
    pose.translate(0.0F,-0.135F,0.0F);
    drawArm(pose,event.getSubmitNodeCollector(),state.lightCoords,renderedArm,variant,1.0F);"""
assert worn.count(old)==1,("B1096_PLAYER_POST_DRAW_ANCHOR",worn.count(old))
assert worn.count("pose.scale(-1.0F,-1.0F,1.0F);")==1
assert "renderedArm=event.getRenderer().getModel().rightArm" in worn
assert "180.0F-player.yBodyRot" in worn
worn=worn.replace(old,new,1)
# The world-suit is correct in-game; it must remain IDENTICAL.
assert "pose.translate(0.0F,-0.135F,0.0F);" not in s[end:]
s=s[:start]+worn+s[end:]
assert "B1096_PLAYER_ONLY_FOREARM_CONTACT" in s[start:s.index(" public static void drawArm(",start)]
assert s.count("nodes.submitModelPart(XSX_WORLD_BARREL,pose")==1
assert s.count("nodes.submitModelPart(BARREL,pose")==1
assert s.count("parent.translateAndRotate(pose);")==1
assert s.count("B1093_WORLD_GUN_ARM_CONTACT")==1
p.write_text(s,encoding="utf-8")
stand=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/client/V176MicroMgStandLayer.java"
v=stand.read_text(encoding="utf-8")
assert "RIGHT_ARM_PIVOT,variant,1.0F" in v
assert "180.0F-xsxStand.getYRot()" in v
print("B1096_PLAYER_ONLY_3P_BARREL_ON_FOREARM_TURRET_RENDER_UNCHANGED_PASS")
