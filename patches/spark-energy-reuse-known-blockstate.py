#!/usr/bin/env python3
"""Reuse already-read BlockState for each ENERGY capability query.

NeoForge ILevelExtension.getCapability(cap,pos,state,blockEntity,context)
allows a known BlockState to avoid another world state lookup. Our three
energy BFS traversals already hold nextState from getBlockState(next).
The capability provider, context, fallback and transaction are unchanged.
Fail-closed on decompiled source shape drift.
"""
import os,re
from pathlib import Path
file=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/blockentity/EnergyCableBlockEntity.java"
s=file.read_text(encoding="utf-8")
marker="XSXLABS_SPARK_ENERGY_REUSE_KNOWN_BLOCKSTATE_V1"
cls="public final class EnergyCableBlockEntity extends BlockEntity implements FacadeCable {"
assert marker not in s and s.count(cls)==1,"wrong ENERGY source class or duplicate patch"
state_guard=r"\bBlockState\s+nextState\s*=\s*server\.getBlockState\(\s*next\s*\)\s*;"
assert len(re.findall(state_guard,s))==3,"Three nextState reads required before capability calls"
sided="server.getCapability(Energy.BLOCK, next, side.getOpposite())"
fallback="server.getCapability(Energy.BLOCK, next, null)"
assert s.count(sided)==3,"Unexpected sided ENERGY capability semantics"
assert s.count(fallback)==3,"Unexpected fallback ENERGY capability semantics"
assert s.count("EnergyCableBlockEntity")>=1
assert s.count("cableBudget-- > 0")==3
s=s.replace(cls,cls+"\n   // "+marker,1)
s=s.replace(sided,"server.getCapability(Energy.BLOCK, next, nextState, null, side.getOpposite())")
s=s.replace(fallback,"server.getCapability(Energy.BLOCK, next, nextState, null, null)")
assert s.count("server.getCapability(Energy.BLOCK, next, nextState, null, side.getOpposite())")==3
assert s.count("server.getCapability(Energy.BLOCK, next, nextState, null, null)")==3
file.write_text(s,encoding="utf-8")
print("SPARK_ENERGY_KNOWN_BLOCKSTATE_REUSE_V1 PASS; same capability, no extra state reads")
