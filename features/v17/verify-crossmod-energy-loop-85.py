#!/usr/bin/env python3
"""Build-time regression gate for cyclic third-party FE capability callbacks.

The EnergyCableBlockEntity is a capability endpoint, not the transaction owner.
The cross-mod callback guard must preserve the caller's FE transactions.
"""
import os
from pathlib import Path

root = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork"
s = (root / "blockentity/EnergyCableBlockEntity.java").read_text(encoding="utf-8")
assert s.count("XSXLABS_CROSSMOD_ENERGY_REENTRY_GUARD_V1") == 1
assert s.count("ThreadLocal<java.util.Set<Object>> energyActiveTransfer") == 1
assert s.count("active.add(EnergyCableBlockEntity.this)") == 3
assert s.count("active.remove(EnergyCableBlockEntity.this)") == 3
assert s.count("if (active.isEmpty()) energyActiveTransfer.remove();") == 3
assert s.count("finally {") >= 3
assert s.count("liveBoundaryEnergy(server, cable, side, next, nextState)") == 3

# Transactions are opened and committed by the conduit ticker, not by this
# endpoint. Checking for openRoot() inside EnergyCableBlockEntity mistakenly
# failed all builds before Java compilation (Build 87).
ticker = (root / "conduit/EnergyConduitTicker.java").read_text(encoding="utf-8")
assert "Transaction.openRoot()" in ticker, "energy conduit must still create root FE transactions"
assert "Capabilities.Energy.BLOCK" in ticker and ".insert(" in ticker and ".extract(" in ticker, "FE routing lost"
assert "Transaction.openRoot()" not in s or "Transaction.openRoot()" in ticker, "transaction ownership drifted"

guard_header = s[s.index("XSXLABS_CROSSMOD_ENERGY_REENTRY_GUARD_V1"):s.index("private final class CableEnergyHandler")]
assert "\\n" not in guard_header, "Escaped newline in generated Java"
print("BUILD88_CROSSMOD_ENERGY_LOOP_REGRESSION_PASS: endpoint guards + caller transactions")
