#!/usr/bin/env python3
"""Use NeoForge's invalidation-aware cache for solar neighbor ENERGY capabilities."""
import os
from pathlib import Path

p = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork/blockentity/SolarGeneratorBlockEntity.java"
s = p.read_text(encoding="utf-8")
cls = "public final class SolarGeneratorBlockEntity extends BlockEntity {"
lookup = "EnergyHandler target = (EnergyHandler)server.getCapability(Energy.BLOCK, pos.relative(side), side.getOpposite());"
marker = "XSXLABS_SOLAR_BLOCK_CAPABILITY_CACHE_V1"
assert marker not in s and s.count(cls) == 1 and s.count(lookup) == 1
for required in ("be.energyJournal.updateSnapshots(tx);", "tx.commit();",
                 "budget -= accepted;", "int start = be.nextSide++ % sides.length;"):
    assert s.count(required) == 1, "Solar behavior changed: " + required
assert "void onLoad(" not in s and "void setRemoved(" not in s
member = """
 // XSXLABS_SOLAR_BLOCK_CAPABILITY_CACHE_V1
 private final java.util.EnumMap<Direction,
  net.neoforged.neoforge.capabilities.BlockCapabilityCache<EnergyHandler,Direction>> energyNeighbors =
  new java.util.EnumMap<>(Direction.class);
 private ServerLevel energyCacheLevel;
 @Override public void onLoad() {
  super.onLoad();
  energyNeighbors.clear();
  energyCacheLevel=null;
 }
 @Override public void setRemoved() {
  energyNeighbors.clear();
  energyCacheLevel=null;
  super.setRemoved();
 }
 private EnergyHandler neighborEnergy(ServerLevel server,Direction side) {
  if(energyCacheLevel!=server){energyNeighbors.clear();energyCacheLevel=server;}
  var cache=energyNeighbors.get(side);
  if(cache==null){
   cache=net.neoforged.neoforge.capabilities.BlockCapabilityCache.create(
    Energy.BLOCK,server,worldPosition.relative(side),side.getOpposite(),
    () -> !isRemoved() && level==server, () -> {});
   energyNeighbors.put(side,cache);
  }
  return cache.getCapability();
 }
"""
s = s.replace(cls, cls + member, 1)
s = s.replace(lookup, "EnergyHandler target = be.neighborEnergy(server, side);", 1)
assert s.count(marker) == 1 and s.count("BlockCapabilityCache.create(") == 1
p.write_text(s, encoding="utf-8")
print("SPARK_SOLAR_BLOCK_CAPABILITY_CACHE PASS")
