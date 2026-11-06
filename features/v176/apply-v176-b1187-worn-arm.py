#!/usr/bin/env python3
"""B1187: lift ONLY worn 3P gun 0.02 model blocks at its arm-local seat."""
import os
from pathlib import Path
p=Path(os.environ['V1_SOURCE_ROOT'])/'dev/obsidiannetwork/client/V176MicroMgVisualClient.java'
s=p.read_text(encoding='utf-8')
old='if(worn)pose.translate(0.0F,-0.012F,0.15F); // B1185_RIGID_ARM_SURFACE_MOUNT_RAISED'
new='if(worn)pose.translate(0.0F,-0.012F,0.13F); // B1187_RIGID_ARM_SEAT_MINIMALLY_RAISED'
assert s.count(old)==1,('B1187_WORN_ARM_MODEL_DRIFT',s.count(old))
assert s.count('parent.translateAndRotate(pose);')==1
assert 'drawArm(pose,nodes,light,parent,tier,extension,false);' in s
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
print('B1187_THIRDPERSON_WORN_BARREL_RAISED_002_IN_ARM_SPACE_PASS')
