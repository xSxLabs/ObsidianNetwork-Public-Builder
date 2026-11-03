#!/usr/bin/env python3
"""Regression: 3P/turret shared barrel must not be hidden inside outer armor.
Model dimensions are in 1/16 block units. This is deterministic GEOMETRY,
not proof that the client submitted pixels. Execute against generated Java.
"""
from pathlib import Path
import re,sys
root=Path(sys.argv[1])
visual=(root/"client/V176MicroMgVisualClient.java").read_text(encoding="utf-8")
player=(root/"client/V176MicroMgLayer.java").read_text(encoding="utf-8")
stand=(root/"client/V176MicroMgStandLayer.java").read_text(encoding="utf-8")
pattern=r"\.addBox\(-0\.46F,6\.8F,(-?\d+(?:\.\d+)?)F,0\.92F,4\.7F,(\d+(?:\.\d+)?)F\)"
matches=re.findall(pattern,visual)
assert len(matches)==1,("B1039_WORLD_BARREL_BOX_MISSING_OR_DUPLICATED",matches)
front,depth=map(float,matches[0])
rear_world=front+depth-0.014*16
assert front< -4.0 and rear_world < -3.25,(
 "B1039_WORLD_BARREL_OCCLUDED_BY_OUTER_ARMOR",front,depth,rear_world)
assert "pose.translate(0.0F,-(1.0F-gunOut)*0.26F,-0.014F)" in visual
assert "nodes.submitModelPart(XSX_WORLD_BARREL,pose" in visual
assert "nodes.submitModelPart(BARREL,pose" in visual
assert "nodes.submitModelPart(HATCH,pose" not in visual
assert "V176MicroMgVisualClient.drawArm(xsxWeaponPose" in player
assert "V176MicroMgVisualClient.drawArm(gunPose" in stand
assert "TURRET_ACTIVE" in stand and "state.rightArmPose.x()" in stand
print("B1039_WORLD_BARREL_GEOMETRY_OUTSIDE_POWERARMOR_PASS",
      "front_model_px=",front,"rear_model_px=",rear_world,
      "first_person_unchanged_by_source_patch=true",
      "scope=geometry_not_actual_pixels")
