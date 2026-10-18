#!/usr/bin/env python3
"""One transmitter may feed many receivers without a per-call TX throughput cap.

Runs after the smooth-six-face patch. NeoForge EnergyHandler uses int amounts;
a transaction still cannot transfer more than the API's int request. Energy is
always debited from a real, loaded TX buffer and compensated on rollback.
Receivers stay capped to 64k FE per dispatch and per FE extraction call.
No new blocks, force-loaded chunks, or global scans.
"""
import os
from pathlib import Path

entity = (Path(os.environ["V1_SOURCE_ROOT"]) /
          "dev/obsidiannetwork/blockentity/WirelessNetworkBlockEntity.java")
source = entity.read_text(encoding="utf-8")

def change(old, new):
    global source
    assert source.count(old) == 1, (
        "WIRELESS_TX_FANOUT anchor drift", old[:100], source.count(old))
    source = source.replace(old, new, 1)

# Stored FE remains finite and persistent. 64M gives 100 receivers at 64k FE/t
# ten ticks of headroom; *throughput* has no additional TX-side per-call cap.
change("public static final long CAPACITY=1000000L;",
       "public static final long CAPACITY=64000000L;")
change("int taken=(int)Math.min(Math.min(stored,(long)requested),MAX_TRANSFER);",
       "// Source is limited by actual stored FE and API request, not a sender rate cap.\n"
       "   int taken=(int)Math.min(stored,(long)requested);")
change("int accepted=(int)Math.min((long)amount,Math.min(CAPACITY-stored,MAX_TRANSFER));",
       "// Allow upstream FE cables to refill at their supported rate.\n"
       "    int accepted=(int)Math.min((long)amount,CAPACITY-stored);")
change("return WirelessEnergyRuntime.pull(world.getServer(),networkId,Math.min(amount,MAX_TRANSFER),tx);",
       "// Receivers retain the 64k FE ceiling for individual extraction requests.\n"
       "    return WirelessEnergyRuntime.pull(world.getServer(),networkId,Math.min(amount,64000),tx);")

assert "int remainingBudget=Math.min(MAX_TRANSFER,64000);" in source
assert "if(accepted==withdrawn){tx.commit();remainingBudget-=accepted;remainingSupply-=accepted;}" in source
assert "handler.journal.updateSnapshots(tx);" in source
assert "journal.updateSnapshots(tx);stored+=accepted;" in source
assert "private static final int MAX_TRANSFER=320000;" in source
entity.write_text(source, encoding="utf-8")
print("WIRELESS_UNLIMITED_TX_THROUGHPUT_V1 PASS; MULTI_RECEIVER_64K_CAP_V1 PASS")
