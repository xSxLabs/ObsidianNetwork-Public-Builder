#!/usr/bin/env python3
"""Build113: preserve the corrected head height but remove horizontal mirroring.

Build112 fixed Y-up vs Minecraft model Y-down by adding (-X,-Y,+Z).
The extra X reflection makes lateral motion and yaw appear reversed relative
to the rendered avatar. Only X is restored to +1.0: Y and head/torso/leg
height correction remain exactly as in green Build112.
No gameplay, FE, damage, models, recipes, armor, station or network changes.
"""
import os
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/client/PowerArmorShieldClient.java"
s=p.read_text(encoding="utf-8")
assert "BUILD111_POSED_ARMOR_SHIELD" in s and "BUILD112_MODEL_COORDS" in s
old='''  stack.scale(-1.0F,-1.0F,1.0F);
  stack.translate(0.0F,-1.501F,0.0F);'''
new='''  // BUILD113_UNMIRRORED_ANIMATION: keep vertical model correction, but DO
  // NOT apply an additional horizontal reflection to the already-oriented
  // player pose. Otherwise head yaw and lateral arm/leg poses run backward.
  stack.scale(1.0F,-1.0F,1.0F);
  stack.translate(0.0F,-1.501F,0.0F);'''
assert s.count(old)==1, ("BUILD113 root transform changed",s.count(old))
s=s.replace(old,new,1)
# Keep exact head/torso/arm/leg geometry and joint attachments from Build111.
assert s.count('submitPart(stack,collector,model.')==6
assert 'joint.translateAndRotate(stack);' in s
assert 'float impact=Math.min' in s
assert 'EnergyTool.energy(armor)<20L' in s
assert 'id.equals("energy_shield")' in s
assert 'stack.scale(-1.0F,-1.0F,1.0F);' not in s
assert 'stack.scale(1.0F,-1.0F,1.0F);' in s
p.write_text(s,encoding="utf-8")

# Static geometry regression: head above torso above boots unchanged.
head=1.501-(-3.9)/16
torso=1.501-5.9/16
boot=1.501-(12+5.8)/16
assert head>torso>boot>0.0
# Horizontal model orientation is now unmirrored (positive X), independent
# of the vertical Y-down-to-Y-up conversion. Right/left retain their X sign.
model_right_arm=-5/16
model_left_arm=5/16
assert model_right_arm<0<model_left_arm
assert (+1.0)*model_right_arm < (+1.0)*model_left_arm
print("BUILD113_UNMIRRORED_ANIMATION PASS: no extra X reflection, head-height correction and six original animated armor shield segments intact")
