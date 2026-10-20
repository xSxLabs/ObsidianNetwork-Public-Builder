#!/usr/bin/env python3
"""Spark 345: eliminate repeated DeferredHolder.get from the ENERGY BFS helpers.

Spark server thread: energyCable spent ~14s in DeferredHolder.get and
energyOpen another ~8s over the captured profile. Minecraft Block objects
registered by the mod are stable for the JVM lifetime. Resolve the two
registry holders lazily ONCE on first live BFS use, not eagerly at class load.
No FE, capability, face, item, transaction or network topology caching.
"""
import os
import re
from pathlib import Path

p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/blockentity/EnergyCableBlockEntity.java"
src=p.read_text(encoding="utf-8")
marker="XSXLABS_ENERGY_REGISTERED_BLOCK_LAZY_TYPES_V1"
cls="public final class EnergyCableBlockEntity extends BlockEntity implements FacadeCable {"
assert src.count(cls)==1 and marker not in src
assert src.count("XSXLABS_ENERGY_HELPER_DUPLICATE_BLOCKTYPE_ELISION_V1")==2
assert src.count("XSXLABS_SPARK_CABLE_ENDPOINT_CAPABILITY_CACHE_V1")==1
assert "import net.minecraft.world.level.block.Block;" in src, "Block import drift"

def bounds(text,name):
    direction=(r"\s*,\s*(?:net\.minecraft\.core\.)?Direction\s+\w+" if name=="energyOpen" else "")
    pattern=(r"private\s+static\s+boolean\s+"+name+
        r"\s*\(\s*(?:net\.minecraft\.server\.level\.)?ServerLevel\s+\w+\s*,"
        r"\s*(?:net\.minecraft\.core\.)?BlockPos\s+\w+\s*,"
        r"\s*(?:net\.minecraft\.world\.level\.block\.state\.)?BlockState\s+\w+"
        +direction+r"\s*\)\s*\{")
    matches=list(re.finditer(pattern,text))
    assert len(matches)==1,(name,"signature drift",len(matches))
    m=matches[0]
    pos=m.end()
    depth=1
    while pos<len(text) and depth:
        if text[pos]=="{": depth+=1
        if text[pos]=="}": depth-=1
        pos+=1
    assert depth==0
    return m.end(),pos-1

modified=src
for name in ("energyCable","energyOpen"):
    start,end=bounds(modified,name)
    body=modified[start:end]
    originalEnergy="(Block)ObsidianNetwork.ENERGY_CABLE.get()"
    originalBundle="(Block)ObsidianNetwork.CONDUIT_BUNDLE.get()"
    assert body.count("physicalEnergyCable")==3,(name,"previous same-state hoist changed")
    assert body.count(originalEnergy)==1,(name,"energy type read drift")
    assert body.count(originalBundle)==1,(name,"bundle type read drift")
    assert body.count("getBlockEntity(")==1,(name,"live topology lookup drift")
    if name=="energyOpen":
        assert "EnergyCableBlock.isCut(" in body and ".enabled(" in body
    else:
        assert ".has(" in body
    body=body.replace(originalEnergy,"XsxRegisteredEnergyBlocks.ENERGY",1)
    body=body.replace(originalBundle,"XsxRegisteredEnergyBlocks.BUNDLE",1)
    modified=modified[:start]+body+modified[end:]

# Lazily loaded by the helper only after the mod's block registration is ready.
# Nested class initialization is guaranteed by the JVM and happens once.
cache="""
   // XSXLABS_ENERGY_REGISTERED_BLOCK_LAZY_TYPES_V1
   private static final class XsxRegisteredEnergyBlocks {
      static final Block ENERGY = (Block)ObsidianNetwork.ENERGY_CABLE.get();
      static final Block BUNDLE = (Block)ObsidianNetwork.CONDUIT_BUNDLE.get();
   }
"""
modified=modified.replace(cls,cls+"\n"+cache,1)
assert modified.count(marker)==1
assert modified.count("static final Block ENERGY")==1
assert modified.count("static final Block BUNDLE")==1
assert modified.count("XsxRegisteredEnergyBlocks.ENERGY")==2
assert modified.count("XsxRegisteredEnergyBlocks.BUNDLE")==2
for anchor in ("source.extract(","target.insert(","Transaction.openRoot()","EnergyCableBlock.isCut(",
               "getBlockEntity(","BlockCapabilityCache.create("):
    assert modified.count(anchor)==src.count(anchor),(anchor,"transfer topology contract changed")
p.write_text(modified,encoding="utf-8")
print("ENERGY_REGISTERED_BLOCK_LAZY_TYPES_V1 PASS: no per-neighbor DeferredHolder lookups")