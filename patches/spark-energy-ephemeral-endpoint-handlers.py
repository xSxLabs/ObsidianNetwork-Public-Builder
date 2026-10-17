#!/usr/bin/env python3
"""Reduce repeated ENERGY conduit endpoint capability lookups per dispatch.

The live endpoint list is built afresh on EVERY tick() call. FE, topology,
and TransactionContext are NEVER cached across transfers/ticks. Original
pair order and transactional extraction/insertion remain unchanged.
Reject anything but the verified active ticker source shape.
"""
import os
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/conduit/EnergyConduitTicker.java"
original=p.read_text(encoding="utf-8")
marker="XSXLABS_SPARK_ENERGY_EPHEMERAL_ENDPOINT_HANDLERS_V1"
assert marker not in original, "Already patched"
def substitute(before,after,description):
    global src
    count=src.count(before)
    assert count==1, f"Unsafe energy ticker source: {description}, matches={count}"
    src=src.replace(before,after,1)
src=original
assert "public final class EnergyConduitTicker implements ConduitTicker" in src
assert "if(network.type()!=ConduitType.ENERGY||level.getGameTime()%5!=0)return;" in src
assert src.count("Transaction.openRoot()")==1
assert src.count("from.extract(1000,tx)")==1
assert src.count("to.insert(got,tx)")==1
assert src.count("from.insert(got-put,tx)")==1
assert src.count("tx.commit();return;")==1
substitute("java.util.ArrayList<ConduitRuntime.Endpoint> connected=new java.util.ArrayList<>();",
    "// "+marker+"\n  // Handlers are valid only for this single dispatch, never across ticks.\n  java.util.ArrayList<ConduitRuntime.Endpoint> connected=new java.util.ArrayList<>();\n  java.util.ArrayList<EnergyHandler> liveHandlers=new java.util.ArrayList<>();",
    "endpoint list allocation")
substitute(
    "if(level.getCapability(Capabilities.Energy.BLOCK,bundle.getBlockPos().relative(d),d.getOpposite())==null)continue;connected.add(new ConduitRuntime.Endpoint(bundle,d,node.config(d)));",
    "EnergyHandler candidate=level.getCapability(Capabilities.Energy.BLOCK,bundle.getBlockPos().relative(d),d.getOpposite());if(candidate==null)continue;connected.add(new ConduitRuntime.Endpoint(bundle,d,node.config(d)));liveHandlers.add(candidate);",
    "initial live capability discovery")
substitute(
    "for(var src:connected){\n   EnergyHandler from=level.getCapability(Capabilities.Energy.BLOCK,src.bundle().getBlockPos().relative(src.side()),src.side().getOpposite());if(from==null)continue;",
    "for(int sourceIndex=0;sourceIndex<connected.size();sourceIndex++){var src=connected.get(sourceIndex);\n   EnergyHandler from=liveHandlers.get(sourceIndex);",
    "source capability rediscovery")
substitute(
    "for(var dst:connected){if(dst.bundle()==src.bundle()&&dst.side()==src.side())continue;\n    EnergyHandler to=level.getCapability(Capabilities.Energy.BLOCK,dst.bundle().getBlockPos().relative(dst.side()),dst.side().getOpposite());if(to==null)continue;",
    "for(int destinationIndex=0;destinationIndex<connected.size();destinationIndex++){var dst=connected.get(destinationIndex);if(dst.bundle()==src.bundle()&&dst.side()==src.side())continue;\n    EnergyHandler to=liveHandlers.get(destinationIndex);",
    "inner quadratic capability rediscovery")
assert src.count(marker)==1
assert src.count("level.getCapability(Capabilities.Energy.BLOCK,")==1, "Unexpected remaining capability lookup"
assert src.count("Transaction.openRoot()")==1
assert src.count("tx.commit();return;")==1
assert src.count("liveHandlers.get(")==2
assert src.count("for(var node:network.nodes())")==1
assert src.count("if(connected.size()<2)return;")==1
p.write_text(src,encoding="utf-8")
print("SPARK_ENERGY_EPHEMERAL_ENDPOINT_HANDLERS_V1 PASS; 1 capability lookup per endpoint per dispatch")
