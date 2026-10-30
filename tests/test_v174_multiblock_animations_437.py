#!/usr/bin/env python3
"""B437: bounded visuals only when powered and operating."""
import ast,os
from pathlib import Path
r=Path(__file__).resolve().parents[1]
p=(r/"features/v174/apply-multiblock-animations-437.py").read_text()
w=(r/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
ast.parse(p)
for x in ("V174_REACTOR_BOUNDED_ANIMATION_437",
          "V174_POWERBANK_BOUNDED_ANIMATION_437",
          "V174_PUMP_BOUNDED_ANIMATION_437",
          "rand.nextInt(6)","rand.nextInt(9)",
          "reactor.guiFuelTicks()<=0","bank.guiEnergy()<=0L",
          "ParticleTypes.END_ROD","ParticleTypes.ELECTRIC_SPARK",
          "ParticleTypes.SPLASH","@Override public void animateTick("):
 assert x in p,x
assert p.count("level.addParticle(")==1
assert p.count("world.addParticle(")==1
assert p.count("l.addParticle(")==1
for x in ("python3 features/v174/apply-multiblock-animations-437.py",
          "python3 tests/test_v174_multiblock_animations_437.py"):assert x in w,x
assert w.index("python3 features/v174/apply-machine-guis-436.py")<w.index("python3 features/v174/apply-multiblock-animations-437.py")
if os.environ.get("V1_SOURCE_ROOT"):
 j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
 for file in ("reactor/ReactorControllerBlock.java",
              "powerbank/PowerbankBlock.java",
              "pump/ElectricWaterPumpBlock.java"):
  s=(j/file).read_text()
  assert "animateTick(BlockState" in s,file
print("V174_MULTIBLOCK_ANIMATIONS_437_CI_PASS")
