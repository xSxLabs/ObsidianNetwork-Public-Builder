#!/usr/bin/env python3
"""B1039: fix invisible 3P/turret barrel geometry being buried inside armor.
B1019's world barrel z=-2.95..-2.30 is INSIDE vanilla thick outer-arm armor
(z front about -3.0 in model pixels), so both renderlayers may submit an
entirely occluded part! Move ONLY the world barrel z out beyond armor face.
The first-person BARREL mesh, camera, skin, arm rotations, FE and cells
are preserved byte-for-byte.
"""
import os
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/client/V176MicroMgVisualClient.java"
s=p.read_text(encoding="utf-8")
old='.addBox(-0.46F,6.8F,-2.95F,0.92F,4.7F,0.65F)'
new='.addBox(-0.46F,6.8F,-4.15F,0.92F,4.7F,1.05F)'
assert s.count(old)==1,("B1039_BARREL_GEOMETRY_DRIFT",s.count(old))
assert s.count('nodes.submitModelPart(XSX_WORLD_BARREL,pose')==1
assert s.count('nodes.submitModelPart(BARREL,pose')==1
# The first-person submission is independent and untouched by this one-
# occurrence replacement; do not depend on Java source method ordering.
assert 'nodes.submitModelPart(BARREL,pose' in s
s=s.replace(old,new,1)
assert s.count(new)==1
# Model coordinates are 16px/block. Current drawArm offset is -0.014 block:
# outer z of barrel is -3.10 -0.224 = -3.324px, outside >= -3px
# outer-arm surface. No new floating hatch or detached transform.
outer_rear=-4.15+1.05-(0.014*16)
assert outer_rear<-3.25,("B1039_BARREL_REAR_INSIDE_ARMOR",outer_rear)
assert "pose.translate(0.0F,-(1.0F-gunOut)*0.26F,-0.014F)" in s
assert 'submitModelPart(HATCH,pose' not in s
p.write_text(s,encoding="utf-8")
print("B1039_WORLD_BARREL_REAR_CLEAR_OF_POWERARMOR_3P_TURRET_ONLY_PASS rear_z_px=",outer_rear)
