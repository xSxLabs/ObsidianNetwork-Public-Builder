#!/usr/bin/env python3
"""B1181 player-only visual fixes, with suit/world/turret/FE unchanged."""
from pathlib import Path
import os,re
p=Path(os.environ['V1_SOURCE_ROOT'])/'dev/obsidiannetwork/client/V176MicroMgVisualClient.java'
s=p.read_text(encoding='utf-8')
a=s.index(' @SubscribeEvent public static void firstPerson(RenderHandEvent event){')
b=s.index(' @SubscribeEvent public static void xsxlabs$aimVisibleFirstPersonArm(',a)
hand=s[a:b]
assert 'XSX_POWER_LOWER' in hand and hand.count('nodes.submitModelPart(BARREL,pose')==1
# B1028 deliberately keeps RenderHandEvent uncanceled or deferred draw nodes
# vanish. Remove the redundantly drawn vanilla-skin upper/lower segments
# in that SAME event. The PowerArmor forearm and gun remain submitted.
count=0
for part in ('upper','upperSleeve','lower','lowerSleeve'):
 pattern=r'(?m)^\s*nodes\.submitModelPart\('+part+r',pose,skin,light,OverlayTexture\.NO_OVERLAY,\s*\n\s*null,false,false,0xFFFFFFFF,null,0\);'
 hand,n=re.subn(pattern,'\n    ; // B1181 hidden duplicate skin segment '+part,hand)
 assert n<=1,('B1181_MULTIPLE_SKIN_SUBMISSIONS',part,n)
 count+=n
# B1028 already replaces vanilla submissions in some render branches;
# an absent legacy call is correct and must not make the build red.
if count==0:
 print('B1183_FIRST_PERSON_LEGACY_SKIN_ALREADY_ABSENT')
assert 'nodes.submitModelPart(XSX_POWER_LOWER' in hand
assert hand.count('nodes.submitModelPart(BARREL,pose')==1
s=s[:a]+hand+s[b:]
# B1183: third-person player ONLY. A constant BODY-space offset would
# float separately from a rotating arm. Instead position the barrel AFTER
# rightArm.translateAndRotate, in the same LOCAL forearm attachment frame.
a=s.index(' @SubscribeEvent public static void wornFallback(')
b=s.index(' public static void drawArm(',a)
w=s[a:b]
root='   pose.scale(-1.0F,-1.0F,1.0F);'
assert w.count(root)==1,('B1181_PLAYER_MODEL_ROOT_DRIFT',w.count(root))
assert 'V176ThirdPersonArmSnapshot.apply(' in w
# Body root remains untouched: no independent world-space gun movement.
assert 'pose.translate(0.0F,0.30F,0.0F)' not in w
s=s[:a]+w+s[b:]
# The private worn overload is the only one to receive the local seat.
# The six-parameter shared turret/world API still forwards worn=false.
old='if(worn)pose.translate(0.0F,-0.012F,0.052F); // B1178_WORN_ONLY_FOREARM'
new='if(worn)pose.translate(0.0F,-0.012F,0.18F); // B1183_RIGID_ARM_SURFACE_MOUNT'
assert s.count(old)==1,('B1183_LOCAL_WORN_MOUNT_DRIFT',s.count(old))
assert 'drawArm(pose,nodes,light,parent,tier,extension,false);' in s
assert 'parent.translateAndRotate(pose);' in s
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
print('B1183_FIRST_PERSON_NO_EXTRA_VANILLA_MESH_RIGID_LOCAL_ARM_MOUNT_PASS')
