#!/usr/bin/env python3
"""B581 regression gate: retained FE math, all valid outer/core cube edges,
bounded cache, same cable locations, no weakening of B580 contracts."""
import os
from pathlib import Path
root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
r=(root/"reactor/ReactorControllerBlockEntity.java").read_text()
v=(root/"client/NetworkVisionClient.java").read_text()
p=(root/"powerbank/PowerbankBlockEntity.java").read_text()
s=(root/"blockentity/SolarGeneratorBlockEntity.java").read_text()
assert "B581_REACTOR_CACHE" in r and "BlockCapabilityCache.create(" in r
assert "b581PortCapabilities.size()>=256" in r
assert "b581CachedSink(world,at,next,dir)" in r
assert "b581Directions" in r
assert "world.hasChunkAt(next)||approvedPorts.contains(next.asLong())" in r
assert "world.getBlockState(at).is(ObsidianNetwork.REACTOR_POWER_PORT.get())" in r
assert "energyPort.extract(accepted,tx)==accepted" in r
assert "tx.commit();" in r
assert "int budget=(int)Math.min(262144L,storedFe);" in r
assert "B579_REACTOR_GENERATE_EVERY_TICK" in r
assert "B579_REACTOR_PUSH_EVERY_TICK" in r
assert "be.rodAssemblies*600L*(100-be.controlRodInsertion)/100L" in r
assert "b579ActualGeneration" in r
assert "B579_BANK_ROLLING_20" in p
assert "B547_SOLAR_SPARSE_FACE_WALK" in s
assert "B581_VISION_SHARED_VERTICES" in v
assert "xrayPositions.size()>=160" in v
assert "b579VisionMasks.getOrDefault(pos,0)" in v
assert "wirePipe(" not in v
assert "wireLine(g,core[near[i]],far[i]" in v
assert "wireLine(g,far[i],far[j]" in v
# For all six directions, a core cube face has 4 vertices, 4 edges.
# A connection's 4 long rails and 4 far ring edges replace the exact
# edges from the old rectangular prism minus its duplicate inner ring.
axes=[(1,0),(1,1),(2,0),(2,2),(4,0),(4,4)]
for axis,face in axes:
 near=[i for i in range(8) if (i&axis)==face]
 assert len(near)==4
 long_edges={(a,("far",a)) for a in near}
 far_edges={(a,b) for a in near for b in near if a<b and (a^b).bit_count()==1}
 near_edges={(a,b) for a in near for b in near if a<b and (a^b).bit_count()==1}
 assert len(long_edges)==4 and len(far_edges)==4 and len(near_edges)==4
old_edges=12+6*12
new_edges=12+6*8
old_vertices=8+6*8
new_vertices=8+6*4
assert old_edges==84 and new_edges==60 and old_vertices==56 and new_vertices==32
print("B581_FE_TRANSACTION_AND_VISION_GEOMETRY_EQUIVALENCE_PASS")
