#!/usr/bin/env python3
"""B1170: preserve actual third-person arm pose, with source-drift-safe matching."""
import os,re
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/client/V176MicroMgVisualClient.java"
s=p.read_text(encoding="utf-8")
start=s.index(" @SubscribeEvent public static void wornFallback(")
end=s.index(" public static void drawArm(",start)
w=s[start:end]
# Remove only player Post's hardcoded arm rotations; never touch stand/turret.
pattern=r"renderedArm\\.xRot\\s*=\\s*-1\\.535F\\s*;\\s*renderedArm\\.yRot\\s*=\\s*0\\.0F\\s*;\\s*renderedArm\\.zRot\\s*=\\s*0\\.0F\\s*;"
w,n=re.subn(pattern,"/* B1170: preserve rendered player arm rotation */",w)
if n==0:
 print("B1170_DIAG_PLAYER_POST_ROTATION_ABSENT; snippets:",
       [x.strip()[:180] for x in w.splitlines() if "renderedArm." in x or "drawArm(pose" in x])
 # Another overlay may already have eliminated the forced rotation.
 assert "renderedArm.xRot=-1.535F" not in w
else:
 assert n==1,("B1170_MULTIPLE_PLAYER_ARM_ROTATIONS",n)
s=s[:start]+w+s[end:]
assert "renderedArm=event.getRenderer().getModel().rightArm" in w
assert "drawArm(pose,event.getSubmitNodeCollector()" in w
assert "parent.translateAndRotate(pose);" in s
p.write_text(s,encoding="utf-8")
print("B1170_PLAYER_ONLY_REAL_ARM_ROTATION_PASS replaced=",n)
