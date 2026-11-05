#!/usr/bin/env python3
"""B1185: raise worn Third-Person barrel 0.03 blocks in arm-local space.

Player only; turret uses worn=false, first-person uses separate BARREL code.
"""
import os
from pathlib import Path
p=Path(os.environ['V1_SOURCE_ROOT'])/'dev/obsidiannetwork/client/V176MicroMgVisualClient.java'
s=p.read_text(encoding='utf-8')
old='if(worn)pose.translate(0.0F,-0.012F,0.18F); // B1183_RIGID_ARM_SURFACE_MOUNT'
new='if(worn)pose.translate(0.0F,-0.012F,0.15F); // B1185_RIGID_ARM_SURFACE_MOUNT_RAISED'
assert s.count(old)==1,('B1185_WORN_MOUNT_DRIFT',s.count(old))
assert 'drawArm(pose,nodes,light,parent,tier,extension,false);' in s
assert 'parent.translateAndRotate(pose);' in s
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
print('B1185_WORN_3P_BARREL_RAISED_0_03_ARM_PIVOT_PRESERVED_PASS')
