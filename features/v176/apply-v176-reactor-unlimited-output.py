#!/usr/bin/env python3
"""v1.7.6: remove the artificial reactor power-port active-push FE budget.

The B497 port used to push at most 262144 FE every 5 server ticks. That
throttled a charged 1-billion-FE reactor even when the connected sink could
take more. NeoForge's EnergyHandler API accepts an int per transaction, so
Integer.MAX_VALUE is the API maximum, not a new gameplay rate limiter.
Never bypass the sink's returned acceptance or transaction rollback.
"""
import os
from pathlib import Path

src = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork/reactor/ReactorControllerBlockEntity.java"
s = src.read_text(encoding="utf-8")
old = "    int budget=(int)Math.min(262144L,storedFe);"
new = (
    "    // V176_REACTOR_UNCAPPED_PORT_PUSH: accept the full stored balance,\n"
    "    // bounded only by the EnergyHandler int request and live sink acceptance.\n"
    "    int budget=(int)Math.min((long)Integer.MAX_VALUE,storedFe);"
)
assert s.count(old) == 1, ("V176_REACTOR_PUSH_SOURCE_DRIFT", s.count(old))
for invariant in (
    "private void pushToPowerPort(ServerLevel world)",
    "if(!formed||!enabled||storedFe<=0L)return;",
    "int accepted=sink.insert(budget,tx);",
    "if(accepted>0&&energyPort.extract(accepted,tx)==accepted)",
    "tx.commit();",
    "public net.neoforged.neoforge.transfer.energy.EnergyHandler energyPort()",
    "int paid=(int)Math.min((long)demand,storedFe);",
):
    assert invariant in s, ("V176_REACTOR_FE_TRANSACTION_CHANGED", invariant)
# The real Reactor shutdown must halt the active POWER-port pusher, not
# merely generation and passive EnergyHandler.extract. Otherwise an externally
# disabled Reactor still probes and attempts to export its remaining buffer.
old_guard = "if(!formed||!enabled||storedFe<=0L)return;"
new_guard = "if(!formed||!enabled||!xsxNetworkEnabled||storedFe<=0L)return;"
assert s.count(old_guard) == 1, ("V176_REACTOR_ACTIVE_PUSH_GUARD_DRIFT", s.count(old_guard))
s = s.replace(old_guard, new_guard, 1)
assert "V176_REACTOR_UNCAPPED_PORT_PUSH" in new
s = s.replace(old, new, 1)
assert "262144L" not in s[s.index("private void pushToPowerPort("):s.index("private void pushToPowerPort(")+2000]
src.write_text(s, encoding="utf-8")

port = src.parent / "ReactorPortBlockEntity.java"
body = port.read_text(encoding="utf-8")
assert "return x==null?0:x.extract(n,tx);" in body, "V176_REACTOR_PORT_CANNOT_FORWARD_FULL_REQUEST"
assert "return mode()==ReactorPortBlock.Mode.POWER?powerHandler:null;" in body
print("V176_REACTOR_POWER_PORT_ACTIVE_PUSH_UNCAPPED_API_MAX_TRANSACTIONAL_PASS")
