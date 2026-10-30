#!/usr/bin/env python3
"""B464: Darkness immunity must be strictly linked to activated armor nightvision."""
import ast,os
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=(root/"features/v174/apply-nightvision-warden-darkness-464.py").read_text()
ast.parse(p)
for marker in (
 "B464_NIGHTVISION_WARDEN_DARKNESS",
 "PlayerTickEvent.Post",
 "p.hasEffect(net.minecraft.world.effect.MobEffects.DARKNESS)",
 'powered(p)', 'hasCard(p,"night_vision")','hasCard(p,"nightvision_on")',
 "p.removeEffect(net.minecraft.world.effect.MobEffects.DARKNESS);",
 "p.isSpectator()"):
 assert marker in p,marker
guard=p.index('if(!powered(p)||!hasCard(p,"night_vision")||!hasCard(p,"nightvision_on"))return;')
assert p.index("if(!p.hasEffect(net.minecraft.world.effect.MobEffects.DARKNESS))return;")<guard
assert guard<p.index("p.removeEffect(net.minecraft.world.effect.MobEffects.DARKNESS);")
# Never restore Darkness on disable or erase real Night Vision.
assert "removeEffect(net.minecraft.world.effect.MobEffects.NIGHT_VISION)" not in p
assert "MobEffects.BLINDNESS" not in p
wf=(root/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
assert "python3 features/v174/apply-nightvision-warden-darkness-464.py" in wf
assert "python3 tests/test_v174_nightvision_darkness_464.py" in wf
if os.environ.get("V1_SOURCE_ROOT"):
 s=(Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/powerarmor/PowerArmorRuntime.java").read_text()
 assert "B464_NIGHTVISION_WARDEN_DARKNESS" in s
 assert "p.removeEffect(net.minecraft.world.effect.MobEffects.DARKNESS);" in s
print("V174_NIGHTVISION_DARKNESS_464_TEST_PASS")
