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
assert count>=1,('B1181_NO_LEGACY_SKIN_FOUND',count)
assert 'nodes.submitModelPart(XSX_POWER_LOWER' in hand
assert hand.count('nodes.submitModelPart(BARREL,pose')==1
s=s[:a]+hand+s[b:]
# B1181 third-person ONLY. Shift after root inverted-Y model transform,
# BEFORE the right-arm pivot: true world down, preserves aim/arm rotation.
a=s.index(' @SubscribeEvent public static void wornFallback(')
b=s.index(' public static void drawArm(',a)
w=s[a:b]
root='   pose.scale(-1.0F,-1.0F,1.0F);'
assert w.count(root)==1,('B1181_PLAYER_MODEL_ROOT_DRIFT',w.count(root))
assert 'V176ThirdPersonArmSnapshot.apply(' in w
w=w.replace(root,root+'\n   pose.translate(0.0F,0.30F,0.0F); // B1181_DOWN_ONLY_WORN_3P',1)
s=s[:a]+w+s[b:]
p.write_text(s,encoding='utf-8')
print('B1181_SINGLE_ARMORED_FP_FOREARM_3P_RIGHT_ARM_MOUNT_DOWN_PASS')
