#!/usr/bin/env python3
"""B915: remove floating MG hatch square, align visible first-person right arm."""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
p=J/"client/V176MicroMgVisualClient.java"
s=p.read_text()
replacements=[
 ("      .texOffs(12,0).addBox(-1.25F,3.1F,-3.05F,2.5F,3.15F,0.55F),",
  "      .texOffs(12,0).addBox(-0.70F,3.30F,-2.95F,1.40F,1.55F,0.28F),"),
 ("  event.getPoseStack().translate(0.0F,0.035F,-0.075F);",
  "  event.getPoseStack().translate(-0.025F,0.07F,-0.12F);"),
 ("  event.getPoseStack().mulPose(com.mojang.math.Axis.XP.rotationDegrees(-11.0F));",
  "  event.getPoseStack().mulPose(com.mojang.math.Axis.XP.rotationDegrees(-23.0F));"),
]
for old,new in replacements:
 assert s.count(old)==1,("B915_GUN_DRIFT",s.count(old),old)
 s=s.replace(old,new,1)
assert s.count("void xsxlabs$aimVisibleFirstPersonArm(RenderArmEvent event)")==1
assert "wornFallback(RenderPlayerEvent.Post" not in s
p.write_text(s)
print("B915_NO_FLOATING_BLACK_HATCH_BIG_SQUARE_VISIBLE_FIRSTPERSON_ARM_ALIGNED_PASS")
