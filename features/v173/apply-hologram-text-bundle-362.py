#!/usr/bin/env python3
"""Build362: stable multiline holograms and connected bundled NETWORK models.

For CUSTOM/NETWORK, align client fallback text line order with server TextDisplay.
For bundles, preserve the native NETWORK conductor's real directional connections
where the network cable model exposes boolean directional blockstate properties.
Pure client rendering; no world, storage or FE mutation. Runs after Build357.
"""
import os
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
p=J/"client/V173WorldGhostRenderer.java"
s=p.read_text(encoding="utf-8")

# Server display: the first line is topmost, last line sits on the configured
# tabletop/above-table baseline. The client fallback must preserve that order.
old='''  for(int i=0;i<Math.min(lines.length,12);i++)
    textLine(mc,ev,cam,t,be,lines[i],i,1F);'''
new='''  // V173_B362_TEXT_ORDER: client fallback must match server TextDisplay.
  // First line at top, final line at HEIGHT 1 tabletop baseline.
  int visibleLines=Math.min(lines.length,12);
  for(int i=0;i<visibleLines;i++)
    textLine(mc,ev,cam,t,be,lines[i],visibleLines-1-i,1F);'''
assert s.count(old)==1,("V173_B362_TEXT_DRIFT",s.count(old))
s=s.replace(old,new,1)

# B354 draws a genuine NETWORK_CABLE model for mixed bundles. The default
# blockstate may have all directional ports closed, depicting a disconnected
# stub even when the real bundle is connected. Read actual nearby network wires
# and attached I/O and set directional booleans only when available on model.
old='''   if(real.is(ObsidianNetwork.CONDUIT_BUNDLE.get()))
    real=ObsidianNetwork.NETWORK_CABLE.get().defaultBlockState();
   // Facade is visual only. Sample and submit the bare cable blockstate.'''
new='''   if(real.is(ObsidianNetwork.CONDUIT_BUNDLE.get())){
    // V173_B362_BUNDLE_CONNECTIONS: derive real NETWORK-side connections.
    BlockState cable=ObsidianNetwork.NETWORK_CABLE.get().defaultBlockState();
    for(net.minecraft.core.Direction dir:net.minecraft.core.Direction.values()){
     var side=cable.getBlock().getStateDefinition().getProperty(dir.getName());
     if(side instanceof net.minecraft.world.level.block.state.properties.BooleanProperty link){
      BlockPos neighbor=node.pos().relative(dir);
      boolean linked=networkWire(mc,neighbor)||networkAttachment(mc,neighbor);
      cable=cable.setValue(link,linked);
     }
    }
    real=cable;
   }
   // Facade is visual only. Sample and submit the bare cable blockstate.'''
assert s.count(old)==1,("V173_B362_BUNDLE_DRIFT",s.count(old))
s=s.replace(old,new,1)
p.write_text(s,encoding="utf-8")

assert "V173_B362_TEXT_ORDER" in p.read_text(encoding="utf-8")
assert "V173_B362_BUNDLE_CONNECTIONS" in p.read_text(encoding="utf-8")
print("V173_B362_TEXT_ORDER_AND_REAL_BUNDLE_CONNECTIONS_PASS")
