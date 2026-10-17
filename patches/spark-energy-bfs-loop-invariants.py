#!/usr/bin/env python3
"""Safe energy-cable BFS invariant hoisting: no caching of FE, endpoints or capabilities."""
import os
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/blockentity/EnergyCableBlockEntity.java"
s=p.read_text(encoding="utf-8")
marker="XSXLABS_SPARK_ENERGY_BFS_LOOP_INVARIANTS_V1"
cls="public final class EnergyCableBlockEntity extends BlockEntity implements FacadeCable {"
visited="HashSet visited = new HashSet();"
check="nextState.is((Block)ObsidianNetwork.ENERGY_CABLE.get())"
dirs="for (Direction side : Direction.values())"
assert marker not in s,"already patched"
for name,what,count in (
    ("class",cls,1),("visited",visited,3),("cable type",check,3),
    ("direction loop",dirs,3),
    ("sided capability","server.getCapability(Energy.BLOCK, next, side.getOpposite())",3),
    ("fallback capability","server.getCapability(Energy.BLOCK, next, null)",3),
    ("BFS bound","cableBudget-- > 0",3),
    ("queue","new ArrayDeque()",3),
    ("amount method","getAmountAsLong() {",1),
    ("extract method","extract(int amount, TransactionContext transaction)",1),
    ("insert method","insert(int amount, TransactionContext transaction)",1)):
    assert s.count(what)==count, "Unsafe source drift: "+name+" expected "+str(count)+" found "+str(s.count(what))
s=s.replace(cls,cls+"\n   // "+marker+"\n   private static final Direction[] ENERGY_SCAN_DIRECTIONS = Direction.values();",1)
s=s.replace(visited,"final Block energyCableType = (Block)ObsidianNetwork.ENERGY_CABLE.get();\n            "+visited)
s=s.replace(check,"nextState.is(energyCableType)")
s=s.replace(dirs,"for (Direction side : ENERGY_SCAN_DIRECTIONS)")
assert s.count(marker)==1 and s.count("nextState.is(energyCableType)")==3 and s.count("for (Direction side : ENERGY_SCAN_DIRECTIONS)")==3
p.write_text(s,encoding="utf-8")
print("SPARK_ENERGY_BFS_INVARIANT_HOIST_V1 PASS")
