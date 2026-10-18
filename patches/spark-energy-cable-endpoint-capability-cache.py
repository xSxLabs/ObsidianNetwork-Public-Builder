#!/usr/bin/env python3
"""Cache each physical ENERGY-cable endpoint via NeoForge BlockCapabilityCache.

The current Spark profile attributes a large amount of solar->cable CPU to
ILevelExtension.getCapability. A per-cable, per-face cache is invalidated by
NeoForge's capability lifecycle; the real world/topology checks, orientation,
face-cut rules, current BlockState, exact endpoint scan order and FE transaction
are all retained. Only the repeated *capability resolution* at an already
verified non-cable boundary is replaced. Null-sided fallback is preserved.

Patch must run LAST of the ENERGY cable source patches and fail closed.
"""
import os
from pathlib import Path

path=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/blockentity/EnergyCableBlockEntity.java"
original=path.read_text(encoding="utf-8")
cls="public final class EnergyCableBlockEntity extends BlockEntity implements FacadeCable {"
marker="XSXLABS_SPARK_CABLE_ENDPOINT_CAPABILITY_CACHE_V1"
assert marker not in original and original.count(cls)==1, "Energy cable type changed"
assert original.count("XSXLABS_SPARK_ENERGY_REUSE_KNOWN_BLOCKSTATE_V1")==1
assert original.count("XSXLABS_SPARK_BFS_PRIMITIVE_VISITED_V1")==1
assert original.count("private final class CableEnergyHandler implements EnergyHandler")==1
assert "public void onLoad()" not in original and "public void setRemoved()" not in original, "Lifecycle override drift"
sided="server.getCapability(Energy.BLOCK, next, nextState, null, side.getOpposite())"
fallback="server.getCapability(Energy.BLOCK, next, nextState, null, null)"
assert original.count(sided)==3 and original.count(fallback)==3, "Sided/null FE lookup contract changed"
assert original.count("nextState = server.getBlockState(next)")==3
assert original.count("cableBudget-- > 0")==3
assert original.count("TransactionContext transaction")==2, "Unknown FE method signature"
# Never change fee debit, credit, transaction or BFS guards as part of this patch.
for anchor in ("source.extract(", "target.insert(", "if (var18 == 0)", "energyOpen("):
    assert anchor in original, "Missing FE invariant: "+anchor

field = r'''
   // XSXLABS_SPARK_CABLE_ENDPOINT_CAPABILITY_CACHE_V1
   // One cache per physical six-face boundary, instantiated lazily. This keeps
   // sparse, long cable networks from allocating endpoint caches at every node.
   @SuppressWarnings("unchecked")
   private final net.neoforged.neoforge.capabilities.BlockCapabilityCache<EnergyHandler,Direction>[]
       cachedFaces = (net.neoforged.neoforge.capabilities.BlockCapabilityCache<EnergyHandler,Direction>[])
       new net.neoforged.neoforge.capabilities.BlockCapabilityCache[6];
   @SuppressWarnings("unchecked")
   private final net.neoforged.neoforge.capabilities.BlockCapabilityCache<EnergyHandler,Direction>[]
       cachedNullFaces = (net.neoforged.neoforge.capabilities.BlockCapabilityCache<EnergyHandler,Direction>[])
       new net.neoforged.neoforge.capabilities.BlockCapabilityCache[6];
   private ServerLevel cachedCapabilityLevel;

   private void clearEnergyEndpointCaches() {
      java.util.Arrays.fill(cachedFaces, null);
      java.util.Arrays.fill(cachedNullFaces, null);
      cachedCapabilityLevel = null;
   }
   @Override public void onLoad() {
      super.onLoad();
      clearEnergyEndpointCaches();
   }
   @Override public void setRemoved() {
      clearEnergyEndpointCaches();
      super.setRemoved();
   }

   private EnergyHandler cachedEnergyEndpoint(ServerLevel server, Direction side) {
      if (cachedCapabilityLevel != server) {
         clearEnergyEndpointCaches();
         cachedCapabilityLevel = server;
      }
      int slot = side.get3DDataValue();
      var sided = cachedFaces[slot];
      if (sided == null) {
         sided = net.neoforged.neoforge.capabilities.BlockCapabilityCache.create(
            Energy.BLOCK, server, worldPosition.relative(side), side.getOpposite(),
            () -> !isRemoved() && level == server, () -> {});
         cachedFaces[slot] = sided;
      }
      EnergyHandler handler = sided.getCapability();
      if (handler != null) return handler;
      // Respect exactly the old opposite-face-then-null fallback semantics.
      var unsided = cachedNullFaces[slot];
      if (unsided == null) {
         unsided = net.neoforged.neoforge.capabilities.BlockCapabilityCache.create(
            Energy.BLOCK, server, worldPosition.relative(side), null,
            () -> !isRemoved() && level == server, () -> {});
         cachedNullFaces[slot] = unsided;
      }
      return unsided.getCapability();
   }

   private EnergyHandler liveBoundaryEnergy(
       ServerLevel server, BlockPos cable, Direction side, BlockPos next, BlockState nextState) {
      // The BFS may traverse many cable BEs. Attribute each endpoint cache to
      // its OWN cable BE, never to a distant root whose neighborhood differs.
      EnergyCableBlockEntity segment = null;
      if (cable.equals(worldPosition)) {
         segment = this;
      } else {
         var be = server.getBlockEntity(cable);
         if (be instanceof EnergyCableBlockEntity found) segment = found;
      }
      if (segment != null && !segment.isRemoved() && segment.level == server
          && segment.worldPosition.equals(cable)) {
         return segment.cachedEnergyEndpoint(server, side);
      }
      // If an unloaded/invalid/replaced BE cannot own the cache, use the exact
      // previous live, state-aware capability resolution including null side.
      EnergyHandler handler = (EnergyHandler)server.getCapability(
          Energy.BLOCK, next, nextState, null, side.getOpposite());
      return handler != null ? handler :
          (EnergyHandler)server.getCapability(Energy.BLOCK, next, nextState, null, null);
   }

'''
# Exact source-shape replacement, not regex/AST guesswork:
# valid decompiler emits the same local pair for getAmount/extract/insert.
s=original
for name,count in (("source",2),("target",1)):
    before=(f"EnergyHandler {name} = (EnergyHandler){sided};\n"
            f"                        if ({name} == null) {{\n"
            f"                           {name} = (EnergyHandler){fallback};\n"
            f"                        }}")
    after=f"EnergyHandler {name} = EnergyCableBlockEntity.this.liveBoundaryEnergy(server, cable, side, next, nextState);"
    assert s.count(before)==count, f"Unexpected energy {name} capability pair: {s.count(before)}, expected {count}"
    s=s.replace(before,after)
assert s.count(sided)==0 and s.count(fallback)==0
assert s.count("liveBoundaryEnergy(server, cable, side, next, nextState)")==3
assert s.count("Transaction.openRoot()")==original.count("Transaction.openRoot()")
assert s.count("source.extract(")==original.count("source.extract(")
assert s.count("target.insert(")==original.count("target.insert(")
assert s.count("energyOpen(")==original.count("energyOpen(")
s=s.replace(cls,cls+"\n"+field,1)
assert s.count(marker)==1 and s.count("BlockCapabilityCache.create(")==2
path.write_text(s, encoding="utf-8")
print("SPARK_CABLE_ENDPOINT_CAPABILITY_CACHE_V1 PASS: live topology + NeoForge invalidation + FE conservation preserved")
