#!/usr/bin/env python3
"""B541 Spark-safe ENERGY cable cut-bit optimization.

The profile shows costly ferritecore StateHolder.getValue() via
EnergyCableBlock.isCut() while solar->EnergyCableHandler insert walks BFS.
A BlockState is canonical and immutable: cache its six cut bits once,
without caching topology, energy, FE handlers or transactions.
Replacing each isCut(state, side) with a mask lookup never changes
routing or FE and is safe even when connections change (new BlockState key).
"""
import os,re
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/blockentity/EnergyCableBlockEntity.java"
s=p.read_text(encoding="utf-8")
marker="B541_IMMUTABLE_ENERGY_CABLE_CUT_MASK"
cls="public final class EnergyCableBlockEntity extends BlockEntity implements FacadeCable {"
assert s.count(cls)==1 and marker not in s,("B541_CABLE_CLASS_DRIFT",s.count(cls))
assert "XSXLABS_SPARK_BFS_PRIMITIVE_VISITED_V1" in s
assert "XSXLABS_SPARK_CABLE_ENDPOINT_CAPABILITY_CACHE_V1" in s
assert "XSXLABS_SPARK_ENERGY_BFS_LOOP_INVARIANTS_V2" in s
assert "ENERGY_SCAN_DIRECTIONS = Direction.values();" in s
for invariant in ("TransactionContext transaction","target.insert(","source.extract(","cableBudget-- > 0"):
 assert invariant in s,("B541_ENERGY_SEMANTIC_DRIFT",invariant)
# No traversal, cut-face logic or capability resolution is changed.
old=r"EnergyCableBlock\.isCut\(\s*([A-Za-z_$][A-Za-z0-9_$]*)\s*,\s*([A-Za-z_$][A-Za-z0-9_$]*(?:\.getOpposite\(\))?)\s*\)"
matches=list(re.finditer(old,s))
# Current cable BFS uses energyOpen() helper rather than the old inline
# 3 traversals. Keep exactly the actual calls of current source.
assert 1<=len(matches)<=12,("B542_CUT_CALL_SHAPE_CHANGED",len(matches))
helper=r'''
 // B541_IMMUTABLE_ENERGY_CABLE_CUT_MASK: 6 face properties are permanent
 // attributes of each immutable canonical BlockState; use a bounded cache
 // of the *states that actually occur* (never cache a dynamic network).
 private static final java.util.Map<BlockState,Integer> XSX_CUT_MASKS =
  java.util.Collections.synchronizedMap(new java.util.IdentityHashMap<>());
 private static boolean xsxEnergyCut(BlockState st,Direction face){
  Integer mask=XSX_CUT_MASKS.get(st);
  if(mask==null){
   int bits=0;
   for(Direction side:ENERGY_SCAN_DIRECTIONS)
    if(EnergyCableBlock.isCut(st,side))bits|=1<<side.get3DDataValue();
   XSX_CUT_MASKS.put(st,bits);
   mask=bits;
  }
  return (mask&(1<<face.get3DDataValue()))!=0;
 }
'''
s,n=re.subn(old,lambda m:"xsxEnergyCut("+m.group(1)+","+m.group(2)+")",s)
assert n==len(matches)
# Insert helper only after transforming originals, never rewrite its fallback!
s=s.replace(cls,cls+"\n"+helper,1)
assert "source.extract(" in s and "target.insert(" in s
assert "XSXLABS_SPARK_CABLE_ENDPOINT_CAPABILITY_CACHE_V1" in s
assert s.count("xsxEnergyCut(")==len(matches)+1,("B542_CUT_COUNT",s.count("xsxEnergyCut("))
p.write_text(s,encoding="utf-8")
print("B541_SPARK_ENERGY_IMMUTABLE_CUT_MASK_PASS: 6 face check cached per immutable state, BFS and FE conserved")
