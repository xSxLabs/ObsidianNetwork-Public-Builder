#!/usr/bin/env python3
"""Three fail-closed Spark hotpath optimizations; no cached FE, block states or world references."""
import os
from pathlib import Path
root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
wp=root/"network/WorldTopologyBridge.java"
cp=root/"conduit/ConduitRuntime.java"
w=wp.read_text(encoding="utf-8")
c=cp.read_text(encoding="utf-8")
marker="XSXLABS_SPARK_LIVE_SCAN_GUARDS_V1"
assert marker not in w and marker not in c
assert "XSXLABS_AUTOCRAFTER_COMPONENT_ONCE_V1" in w
assert "XSXLABS_CONTROLLER_EXTERNAL_ONCE_PER_CALL_V1" in w
assert "XSXLABS_SPARK_CONDUIT_RUNTIME_REUSE_V1" in c
def replace(s,old,new,label):
    assert s.count(old)==1,(label,s.count(old))
    return s.replace(old,new,1)
def edit_scope(s,start,end,op,label):
    assert s.count(start)==1 and s.count(end)==1,label
    a=s.index(start);b=s.index(end,a)
    return s[:a]+op(s[a:b])+s[b:]
def autocrafter(s):
    s=replace(s,"BlockPos bp = new BlockPos(px.x(), px.y(), px.z());",
      "BlockPos bp = new BlockPos(px.x(), px.y(), px.z());\n"
      "            // "+marker+": one live chunk check per graph node.\n"
      "            boolean xsxCenterChunkLoaded=level.hasChunkAt(bp);","auto center declaration")
    s=replace(s,"if (level.hasChunkAt(bp) && level.getBlockState(bp).is((Block)ObsidianNetwork.AUTOCRAFTER.get()))",
      "if (xsxCenterChunkLoaded && level.getBlockState(bp).is((Block)ObsidianNetwork.AUTOCRAFTER.get()))","auto center")
    s=replace(s,"if (level.hasChunkAt(q) && level.getBlockState(q).is((Block)ObsidianNetwork.AUTOCRAFTER.get()))",
      "if (((((q.getX() >> 4) == (bp.getX() >> 4)) && "
      "((q.getZ() >> 4) == (bp.getZ() >> 4))) ? xsxCenterChunkLoaded : "
      "level.hasChunkAt(q)) && level.getBlockState(q).is((Block)ObsidianNetwork.AUTOCRAFTER.get()))","auto neighbor")
    assert s.count("xsxCenterChunkLoaded")==3 and s.count("level.hasChunkAt(q)")==1
    return s
w=edit_scope(w,
  "public static int autocrafterCount(ServerLevel level, NetworkRuntime runtime) {",
  "public static int autoChiselerCount(ServerLevel level, NetworkRuntime runtime) {",
  autocrafter,"auto method")
def devices(s):
    s=replace(s,"BlockPos p = new BlockPos(node.x(), node.y(), node.z());",
      "BlockPos p = new BlockPos(node.x(), node.y(), node.z());\n"
      "               // "+marker+": cross-chunk neighbors use live probe.\n"
      "               boolean xsxCenterChunkLoaded=level.hasChunkAt(p);","device center declaration")
    s=replace(s,"if (level.hasChunkAt(q) && !component.contains(toCore(q)) && checkedExternal.add(q.immutable()))",
      "if (((((q.getX() >> 4) == (p.getX() >> 4)) && "
      "((q.getZ() >> 4) == (p.getZ() >> 4))) ? xsxCenterChunkLoaded : "
      "level.hasChunkAt(q)) && !component.contains(toCore(q)) && checkedExternal.add(q.immutable()))",
      "device neighbor")
    for x in ("checkedExternal.add(q.immutable())","level.hasChunkAt(q)","xsxCenterChunkLoaded"):
        assert x in s
    return s
w=edit_scope(w,
  "public static WorldTopologyBridge.DeviceCounts connectedDeviceCounts(ServerLevel level, NetworkRuntime runtime) {",
  "public static List<BlockPos> externalCandidates(ServerLevel level, NetworkRuntime runtime) {",
  devices,"device method")
def conduit(s):
    s=replace(s,
      "ArrayList<Endpoint> out=new ArrayList<>();ConduitType type=network.type();var layer=layer(type);",
      "ArrayList<Endpoint> out=new ArrayList<>();ConduitType type=network.type();var layer=layer(type);\n"
      "   // "+marker+": only memoize immutable registered block IDs within THIS scan.\n"
      "   java.util.IdentityHashMap<net.minecraft.world.level.block.Block,String> xsxPathMemo=null;",
      "conduit local memo")
    s=replace(s,
      "String adjacentId=net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(level.getBlockState(neighborPos).getBlock()).getPath();",
      "var xsxNeighborBlock=level.getBlockState(neighborPos).getBlock();\n"
      "            if(xsxPathMemo==null)xsxPathMemo=new java.util.IdentityHashMap<>();\n"
      "            String adjacentId=xsxPathMemo.get(xsxNeighborBlock);\n"
      "            if(adjacentId==null){\n"
      "              adjacentId=net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(xsxNeighborBlock).getPath();\n"
      "              xsxPathMemo.put(xsxNeighborBlock,adjacentId);\n"
      "            }","conduit registry path")
    for x in ('adjacentId.endsWith("_cable")','adjacentId.equals("conduit_bundle")',
              'adjacentId.equals("multi_cable")',
              'if(traversable(level,neighborPos,type))continue;',
              'if(!level.hasChunkAt(neighborPos))continue;'):
        assert s.count(x)==1,("conduit safety",x)
    return s
c=edit_scope(c,
  "public static List<Endpoint> scanEndpoints(ServerLevel level,ConduitNetwork network,boolean extract){",
  "public static List<Endpoint> endpoints(",
  conduit,"conduit method")
assert w.count(marker)==2 and c.count(marker)==1
# Publish only once all three independent safety checks passed.
wp.write_text(w,encoding="utf-8")
cp.write_text(c,encoding="utf-8")
print("XSXLABS_SPARK_LIVE_SCAN_GUARDS_V1 PASS: 2 same-chunk availability reuses + 1 local block registry memo")
