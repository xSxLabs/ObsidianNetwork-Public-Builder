#!/usr/bin/env python3
"""B624: cheap, semantics-identical per-node BlockPos hoist for the Cable Bundle
ENERGY ticker. No topology, endpoint, FE, transaction or transfer cadence cache.
This builds on the already proven B227/B232 Spark conduit patches.
"""
import os
from pathlib import Path

p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/conduit/EnergyConduitTicker.java"
s=p.read_text(encoding="utf-8")
mark="V175_B624_CABLE_BUNDLE_NODE_POSITION_HOIST"
loop="for(net.minecraft.core.Direction d:CONDUIT_SCAN_SIDES){"
old="net.minecraft.core.BlockPos neighborPos=bundle.getBlockPos().relative(d);"
guard="XSXLABS_SPARK_TICKER_NEIGHBOR_POS_REUSE_V1"
assert mark not in s
for anchor in (
    "public final class EnergyConduitTicker implements ConduitTicker",
    "XSXLABS_SPARK_ENERGY_EPHEMERAL_ENDPOINT_HANDLERS_V1",
    "XSXLABS_SPARK_CONDUIT_STATIC_DIRECTIONS_V1",
    guard,
    "for(var node:network.nodes())",
    "Transaction.openRoot()",
    "from.extract(1000,tx)",
    "to.insert(got,tx)",
    "from.insert(got-put,tx)",
    "tx.commit();return;",
    "if(connected.size()<2)return;",
    "level.getCapability(Capabilities.Energy.BLOCK,",
):
    assert anchor in s,("B624_PRESERVE_LIVE_FE_CONTRACT",anchor)
assert s.count(loop)==1,("B624_LOOP_CHANGED",s.count(loop))
assert s.count(old)==1,("B624_NEIGHBOR_POSITION_CHANGED",s.count(old))
assert s.index("for(var node:network.nodes())") < s.index(loop) < s.index(old)
assert s.count("level.getCapability(Capabilities.Energy.BLOCK,")==1,("B624_EXISTING_EPHEMERAL_CAPABILITY",s.count("level.getCapability(Capabilities.Energy.BLOCK,"))
# One read per valid node, same exact BlockPos.relative(Direction), side order
# and capability query. The owned BE is already validated before this loop.
s=s.replace(loop,"// "+mark+": immutable position read once per node.\n   net.minecraft.core.BlockPos xsxBundleNodePos=bundle.getBlockPos();\n   "+loop,1)
s=s.replace(old,"net.minecraft.core.BlockPos neighborPos=xsxBundleNodePos.relative(d);",1)
assert s.count(mark)==1
assert s.index("xsxBundleNodePos=bundle.getBlockPos();") < s.index("xsxBundleNodePos.relative(d)")
assert s.count("bundle.getBlockPos().relative(d)")==0
for anchor in ("from.extract(1000,tx)","to.insert(got,tx)","from.insert(got-put,tx)","tx.commit();return;"):
    assert s.count(anchor)==1
p.write_text(s,encoding="utf-8")
print("V175_B624_CABLE_BUNDLE_ENERGY_NODE_POS_PASS: same live endpoints, same six faces, same FE/tx; fewer BE position reads")
