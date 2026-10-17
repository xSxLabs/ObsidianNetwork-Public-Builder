#!/usr/bin/env python3
"""Fail-closed constant hoisting, supporting both known compiled cable source shapes.

Never cache FE, transactions, topology, neighbor state, or EnergyHandler.
"""
import os,re
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/blockentity/EnergyCableBlockEntity.java"
original=p.read_text(encoding="utf-8")
marker="XSXLABS_SPARK_ENERGY_BFS_LOOP_INVARIANTS_V2"
cls="public final class EnergyCableBlockEntity extends BlockEntity implements FacadeCable {"
assert original.count(cls)==1, "EnergyCableBlockEntity class changed"
assert marker not in original, "Already patched"
start=re.search(r'private\s+final\s+class\s+CableEnergyHandler\s+implements\s+EnergyHandler\s*\{',original)
assert start, "Sided energy handler missing"
brace=original.index('{',start.start());depth=1;pos=brace+1
while depth and pos<len(original):
    if original[pos]=='{':depth+=1
    if original[pos]=='}':depth-=1
    pos+=1
assert depth==0, "Energy handler unbalanced"
handler=original[start.start():pos]
loop=r'for\s*\(\s*Direction\s+\w+\s*:\s*Direction\.values\(\)\s*\)'
found=list(re.finditer(loop,handler))
print("ENERGY_SOURCE_SHAPE_V2 direction_bfs_loops="+str(len(found))+
      " legacy_neighbor_checks="+str(original.count("nextState.is((Block)ObsidianNetwork.ENERGY_CABLE.get())"))+
      " named_energy_helpers="+str("energyCable(" in original and "energyOpen(" in original))
assert len(found)==3, "Expected three separate Direction.values() BFS loops; refusing unsafe patch"
assert handler.count("getAmountAsLong() {")==1
assert len(re.findall(r'\bextract\s*\(\s*int\s+amount\s*,',handler))==1
assert len(re.findall(r'\binsert\s*\(\s*int\s+amount\s*,',handler))==1
check="nextState.is((Block)ObsidianNetwork.ENERGY_CABLE.get())"
native_count=handler.count(check)
assert native_count in (0,3), "Partial changed native cable routing"
# Legacy source shape: the exact same source/capability guards are required.
if native_count==3:
    for name,anchor,count in (
        ("visited","HashSet visited = new HashSet();",3),
        ("sided capability","server.getCapability(Energy.BLOCK, next, side.getOpposite())",3),
        ("fallback capability","server.getCapability(Energy.BLOCK, next, null)",3),
        ("budget","cableBudget-- > 0",3)):
        assert handler.count(anchor)==count, "Unsafe legacy BFS guard: "+name
    handler=handler.replace("HashSet visited = new HashSet();",
      "final Block energyCableType = (Block)ObsidianNetwork.ENERGY_CABLE.get();\n            HashSet visited = new HashSet();")
    handler=handler.replace(check,"nextState.is(energyCableType)")
else:
    # New source shape uses dedicated energyCable/energyOpen helpers.
    # Do NOT assume the old block-state or capability access semantics.
    assert "energyCable(" in original and "energyOpen(" in original, "Unrecognized energy traversal shape"
handler=re.sub(loop,lambda m:m.group(0).replace("Direction.values()","ENERGY_SCAN_DIRECTIONS"),handler)
assert len(re.findall(r'for\s*\(\s*Direction\s+\w+\s*:\s*ENERGY_SCAN_DIRECTIONS\s*\)',handler))==3
source=original[:start.start()]+handler+original[pos:]
source=source.replace(cls,cls+"\n   // "+marker+"\n   private static final Direction[] ENERGY_SCAN_DIRECTIONS = Direction.values();",1)
assert source.count(marker)==1
p.write_text(source,encoding="utf-8")
print("SPARK_ENERGY_BFS_INVARIANT_HOIST_V2 PASS (no mutable-world or FE cache)")
