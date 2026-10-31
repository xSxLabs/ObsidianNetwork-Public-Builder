#!/usr/bin/env python3
"""B575: nonblocking immutable cable cut-mask reads; same FE transactions."""
import os
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/blockentity/EnergyCableBlockEntity.java"
s=p.read_text()
for marker in ("B541_IMMUTABLE_ENERGY_CABLE_CUT_MASK","B568_PER_TICK_LIVE_CABLE_BE_LOOKUP",
 "TransactionContext transaction","target.insert(","source.extract(",
 "cableBudget-- > 0","private static boolean xsxEnergyCut("):
 assert marker in s,("B575_HOTPATH_SOURCE_DRIFT",marker)
old="java.util.Collections.synchronizedMap(new java.util.IdentityHashMap<>());"
assert s.count(old)==1 and "java.util.Map<BlockState,Integer> XSX_CUT_MASKS" in s
s=s.replace(old,"new java.util.concurrent.ConcurrentHashMap<>(); // B575_LOCK_FREE_CUT_MASK_READ",1)
assert "EnergyCableBlock.isCut(st,side)" in s
p.write_text(s)
print("B575_SAFE_ENERGY_CABLE_LOCK_FREE_CUT_STATE_CACHE_PASS")
