#!/usr/bin/env python3
"""Build431 regression: no stale powerbank port permission after topology changes."""
import ast,os
from pathlib import Path
r=Path(__file__).resolve().parents[1]
p=(r/"features/v174/apply-multiblock-recovery-431.py").read_text()
w=(r/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
ast.parse(p)
for x in ("V174_REACTOR_AUTO_RECOVERY_431","V174_POWERBANK_AUTO_RECOVERY_431",
 "V174_POWERBANK_AUTHORIZED_PORTS_431","activePorts.clear()",
 "activePorts.add(p.asLong())","activePorts.contains(worldPosition.asLong())",
 "restorePending=in.getBooleanOr","Math.floorMod(pos.asLong(),10L)*20L",
 "Math.floorMod(at.asLong(),400L)","!world.hasChunkAt","formed=false"):
 if x=="!world.hasChunkAt":continue
 assert x in p,x
assert "python3 features/v174/apply-multiblock-recovery-431.py" in w
assert "python3 tests/test_v174_multiblock_recovery_431.py" in w
assert w.index("python3 features/v174/apply-powerbank-core-429.py")<w.index("python3 features/v174/apply-multiblock-recovery-431.py")
if os.environ.get("V1_SOURCE_ROOT"):
 j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
 a=(j/"reactor/ReactorControllerBlockEntity.java").read_text()
 b=(j/"powerbank/PowerbankBlockEntity.java").read_text()
 c=(j/"powerbank/PowerbankBlock.java").read_text()
 assert "getBooleanOr(\"reactorFormed\",false)" in a
 assert "restorePending" in a
 assert "activePorts.contains(worldPosition.asLong())" in b
 assert "activePorts.clear()" in b
 assert "PowerbankBlockEntity::tick" in c
print("V174_MULTIBLOCK_RECOVERY_431_CI_PASS")
