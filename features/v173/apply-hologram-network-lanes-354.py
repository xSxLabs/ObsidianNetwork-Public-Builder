#!/usr/bin/env python3
"""Build354: render the actual NETWORK lane of mixed conduit bundles.

The bundle's BlockState is not its visible conductor; its native BER draws
the layers. In NETWORK holograms the physical NETWORK lane is represented by
the actual registered NETWORK_CABLE model, never by a fabricated cube.
Also show attached storage terminals/drives across their published name variants.
Only loaded client blocks are sampled. No storage, topology or save mutations.
"""
from pathlib import Path
import os

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
target=J/"client/V173WorldGhostRenderer.java"
s=target.read_text(encoding="utf-8")

old='''   BlockState real=node.state();
   // Facade is visual only. Sample and submit the bare cable blockstate.'''
new='''   BlockState real=node.state();
   // V173_B354_BUNDLE_NETWORK_LANE: bundled conductors use a dedicated BER.
   // Reuse the REAL network cable model for their NETWORK lane only.
   // Other lanes (FE, redstone, fluids) are intentionally not drawn.
   if(real.is(ObsidianNetwork.CONDUIT_BUNDLE.get()))
    real=ObsidianNetwork.NETWORK_CABLE.get().defaultBlockState();
   // Facade is visual only. Sample and submit the bare cable blockstate.'''
assert s.count(old)==1,("V173_B354_RENDER_DRIFT",s.count(old))
s=s.replace(old,new,1)

old='''    path.equals("storage_drive")||path.equals("network_controller")||
    path.equals("storage_terminal")||path.equals("crafting_terminal");'''
new='''    path.equals("storage_drive")||path.equals("network_drive")||
    path.equals("network_storage_drive")||path.equals("network_controller")||
    path.equals("storage_terminal")||path.equals("network_terminal")||
    path.equals("crafting_terminal")||path.equals("network_crafting_terminal")||
    path.equals("network_interface");'''
assert s.count(old)==1,("V173_B354_ENDPOINT_DRIFT",s.count(old))
s=s.replace(old,new,1)

# Prefer a connected 3D graph to a tiny local crop, but NEVER let the
# hologram explore unloaded chunks or turn into an unbounded BFS.
old='''  return Math.abs((long)node.getX()-origin.getX())<=16L
    &&Math.abs((long)node.getZ()-origin.getZ())<=16L
    &&Math.abs((long)node.getY()-origin.getY())<=12L;'''
new='''  // V173_B354_CONNECTED_REACH: two chunks across X/Z, 24 blocks above/below.
  return Math.abs((long)node.getX()-origin.getX())<=32L
    &&Math.abs((long)node.getZ()-origin.getZ())<=32L
    &&Math.abs((long)node.getY()-origin.getY())<=24L;'''
assert s.count(old)==1,("V173_B354_RADIUS_DRIFT",s.count(old))
s=s.replace(old,new,1)

old="while(!frontier.isEmpty()&&result.size()<256)"
new="while(!frontier.isEmpty()&&result.size()<384)"
assert s.count(old)==1,("V173_B354_LIMIT_DRIFT",s.count(old))
s=s.replace(old,new,1)
old="networkAttachment(mc,next)&&drawn.add(next)&&result.size()<256"
new="networkAttachment(mc,next)&&drawn.add(next)&&result.size()<384"
assert s.count(old)==1,("V173_B354_ENDPOINT_LIMIT_DRIFT",s.count(old))
s=s.replace(old,new,1)
old="if(seen.size()<512&&seen.add(next))frontier.addLast(next);"
new="if(seen.size()<768&&seen.add(next))frontier.addLast(next);"
assert s.count(old)==1,("V173_B354_VISITED_LIMIT_DRIFT",s.count(old))
s=s.replace(old,new,1)

target.write_text(s,encoding="utf-8")
assert "V173_B354_BUNDLE_NETWORK_LANE" in target.read_text(encoding="utf-8")
assert "V173_B354_CONNECTED_REACH" in target.read_text(encoding="utf-8")
print("V173_B354_REAL_NETWORK_LANES_EXTENDED_ENDPOINTS_PASS")
