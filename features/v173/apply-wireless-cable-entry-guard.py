#!/usr/bin/env python3
"""v1.7.3: wireless NETWORK runtime requires a real attached NETWORK cable.

A terminal/drive/printer cannot silently use the receiver merely because
it is adjacent to the machine: at least one actual NETWORK conductor must
attach the queried device to the wireless receiver's cable graph.
ENERGY-only cable bundles remain excluded by networkWire().
"""
import os
from pathlib import Path

root = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork"
path = root / "network/NetworkSignalRelayBridge.java"
source = path.read_text(encoding="utf-8")

old = """   Set<BlockPos> seen=new HashSet<>();
   ArrayDeque<BlockPos> queue=new ArrayDeque<>();
   queue.add(queried);
   int hops=0;"""
new = """   Set<BlockPos> seen=new HashSet<>();
   ArrayDeque<BlockPos> queue=new ArrayDeque<>();
   // V173_WIRELESS_CABLE_ENTRY_GUARD: start only at physical NETWORK wires.
   // Never treat the queried machine itself as a cable or accept a bare RX.
   if(networkWire(level,queried))queue.add(queried);
   else for(Direction entry:Direction.values()){
    BlockPos first=queried.relative(entry);
    if(networkWire(level,first))queue.addLast(first);
   }
   if(queue.isEmpty())return null;
   int hops=0;"""
assert source.count(old) == 1, ("unexpected relay BFS initialization", source.count(old))
assert "ConduitBundleBlockEntity.Layer.NETWORK" in source
assert "ConduitBundleBlockEntity.Layer.ENERGY" not in source
assert "if(RESOLVING.get()||queried==null)return null;" in source
updated = source.replace(old, new, 1)
assert updated.count("V173_WIRELESS_CABLE_ENTRY_GUARD") == 1
path.write_text(updated, encoding="utf-8")
print("V173_WIRELESS_CABLE_ENTRY_GUARD_PASS: wireless NETWORK requires an actual attached conductor")
