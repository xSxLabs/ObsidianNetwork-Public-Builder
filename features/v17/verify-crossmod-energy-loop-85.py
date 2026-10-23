#!/usr/bin/env python3
"""Build-time regression gate for cyclic third-party FE capability callbacks."""
import os,re
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/blockentity/EnergyCableBlockEntity.java"
s=p.read_text()
assert s.count("XSXLABS_CROSSMOD_ENERGY_REENTRY_GUARD_V1")==1
assert s.count("ThreadLocal<java.util.Set<Object>> energyActiveTransfer")==1
assert s.count("active.add(EnergyCableBlockEntity.this)")==3
assert s.count("active.remove(EnergyCableBlockEntity.this)")==3
assert s.count("if (active.isEmpty()) energyActiveTransfer.remove();")==3
assert s.count("finally {")>=3
assert s.count("liveBoundaryEnergy(server, cable, side, next, nextState)")==3
assert s.count("Transaction.openRoot()")>=1
assert "\\n" not in s[s.index("XSXLABS_CROSSMOD_ENERGY_REENTRY_GUARD_V1"):s.index("private final class CableEnergyHandler")], "Escaped newline in generated Java"
print("BUILD85_CROSSMOD_ENERGY_LOOP_REGRESSION_PASS")
