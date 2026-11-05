#!/usr/bin/env python3
"""B1167: align 3P gun with the actual rendered right arm; leave turret untouched."""
import os
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/client/V176MicroMgVisualClient.java"
s=p.read_text(encoding="utf-8")
old="""    renderedArm.xRot=-1.535F;renderedArm.yRot=0.0F;renderedArm.zRot=0.0F;
    drawArm(pose,event.getSubmitNodeCollector(),state.lightCoords,renderedArm,variant,1.0F);"""
new="""    // The model already contains the arm's rendered animation/attack pose.
    // Forcing xRot=-1.535 and yaw=0 detached the gun from the visible forearm.
    drawArm(pose,event.getSubmitNodeCollector(),state.lightCoords,renderedArm,variant,1.0F);"""
assert s.count(old)==1,("B1167_THIRD_PERSON_ARM_ANCHOR_DRIFT",s.count(old))
s=s.replace(old,new,1)
assert "renderedArm=event.getRenderer().getModel().rightArm" in s
assert "parent.translateAndRotate(pose);" in s
assert "pose.translate(0.0F,-(1.0F-gunOut)*0.26F,0.006F)" in s
p.write_text(s,encoding="utf-8")
print("B1167_3P_WEAPON_USES_ACTUAL_RIGHT_ARM_PIVOT_TURRET_UNTOUCHED_PASS")
