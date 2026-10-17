#!/usr/bin/env python3
"""Reuse a single neighbor BlockPos for ENERGY conduit bundle and capability probes.

Keep one live capability lookup per connected face per dispatch. Never retain
positions/handlers across ticks, and preserve all FE transfer transactions.
"""
import os
from pathlib import Path

p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/conduit/EnergyConduitTicker.java"
s=p.read_text(encoding="utf-8")
marker="XSXLABS_SPARK_TICKER_NEIGHBOR_POS_REUSE_V1"
old_bundle="if(ConduitRuntime.bundle(level,bundle.getBlockPos().relative(d),ConduitType.ENERGY)!=null)continue;"
old_cap="EnergyHandler candidate=level.getCapability(Capabilities.Energy.BLOCK,bundle.getBlockPos().relative(d),d.getOpposite());"
assert marker not in s
for token in (
 "XSXLABS_SPARK_ENERGY_EPHEMERAL_ENDPOINT_HANDLERS_V1",
 "XSXLABS_SPARK_CONDUIT_STATIC_DIRECTIONS_V1",
 "Transaction.openRoot()",
 "from.extract(1000,tx)",
 "to.insert(got,tx)",
 "from.insert(got-put,tx)",
 "tx.commit();return;",
 old_bundle,old_cap):
    assert s.count(token)==1,"Ticker drift: "+token
s=s.replace(old_bundle,"// "+marker+"\n    net.minecraft.core.BlockPos neighborPos=bundle.getBlockPos().relative(d);\n    if(ConduitRuntime.bundle(level,neighborPos,ConduitType.ENERGY)!=null)continue;",1)
s=s.replace(old_cap,"EnergyHandler candidate=level.getCapability(Capabilities.Energy.BLOCK,neighborPos,d.getOpposite());",1)
assert s.count("bundle.getBlockPos().relative(d)")==1
assert s.count("level.getCapability(Capabilities.Energy.BLOCK,")==1
p.write_text(s,encoding="utf-8")
print("SPARK_TICKER_NEIGHBOR_POS_REUSE_V1 PASS; live capability/transaction behavior retained")
