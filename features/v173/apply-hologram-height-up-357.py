#!/usr/bin/env python3
"""Build357: all hologram modes rise from the tabletop, never below it.

HEIGHT=1 -> top face of the terminal block (block Y+1).
HEIGHT=n -> that face + (n-1) blocks.
For miniature MAP and NETWORK align the BOTTOM of their entire 3D bounding
box, rather than the midpoint or top of the projection, to this baseline.
For server/client text align its lowest line to the same baseline.

Rendering, GUI text and positioning only; no save-format/world/network/FE edits.
Runs after Build354 on v1.7.3.
"""
import os
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def change(rel,old,new):
 p=J/rel
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("V173_B357_ANCHOR_DRIFT",rel,s.count(old),old[:100])
 p.write_text(s.replace(old,new,1),encoding="utf-8")

render="client/V173WorldGhostRenderer.java"

# The fallback uses the same bottom line / placement as the server TextDisplay.
change(render,
 '''   double y=origin.getY()-be.holoHeight()+.55D+index*sizeFactor*.75D;''',
 '''   // V173_B357_TEXT_BASELINE: HEIGHT 1 is exactly tabletop height.
   double y=origin.getY()+be.holoHeight()+index*sizeFactor*.75D;''')

# Network uses the BOTTOM (minimum source Y) as anchor; preserve true XYZ
# scale, and never place the lowest rendered model beneath the tabletop.
change(render,
 '''  double topY=origin.getY()-be.holoHeight()+1D;''',
 '''  // V173_B357_NETWORK_BASELINE: 1=tabletop, 2=one block up, etc.
  double bottomY=origin.getY()+be.holoHeight();''')
change(render,
 '''   double y=topY-(maxY+1D-at.getY())*scale;''',
 '''   double y=bottomY+(at.getY()-minY)*scale;''')

# MAP samples terrain above/below its reference terrain Y, so merely changing
# originY leaves deep cave voxels underneath the table. Translate the ENTIRE
# finished miniature until its lowest model is anchored at the requested height.
change(render,
 '''  // Height=1 means the projection reference is one block UNDER the table.
  // World relief uses original 1:1 XYZ proportions on the miniature.
  double originY=t.getY()-be.holoHeight()+.5D;''',
 '''  // V173_B357_MAP_BASELINE: anchor is the table's top at HEIGHT=1.
  // Map samples still retain authentic terrain relief and proportions.
  double originY=t.getY()+be.holoHeight();''')
p=J/render
s=p.read_text(encoding="utf-8")
start=s.index(" // V173_VOLUME_MAP_327: genuine exposed blocks")
end=s.index(" private static net.minecraft.client.multiplayer.ClientLevel portalWorld;",start)
map_section=s[start:end]
assert map_section.count("  return out;")==1,("V173_B357_MAP_RETURN_DRIFT",map_section.count("  return out;"))
map_section=map_section.replace("  return out;",'''  // V173_B357_MAP_BOTTOM_ALIGNED: keep all terrain (including caves)
  // on/above the table. HEIGHT moves the whole map up exactly one block.
  if(out.isEmpty())return out;
  double lowest=Double.POSITIVE_INFINITY;
  for(MapVoxel tile:out)lowest=Math.min(lowest,tile.y());
  double shift=(t.getY()+be.holoHeight())-lowest;
  java.util.ArrayList<MapVoxel> elevated=new java.util.ArrayList<>(out.size());
  for(MapVoxel tile:out)
   elevated.add(new MapVoxel(tile.state(),tile.x(),tile.y()+shift,
                             tile.z(),tile.sx(),tile.sy(),tile.sz()));
  return elevated;''',1)
s=s[:start]+map_section+s[end:]
p.write_text(s,encoding="utf-8")

# Network and Custom TextDisplays survive client culling and are server-owned.
# Reposition the lowest line at tabletop on 1 and move UP with each step.
change("blockentity/NetworkDeviceBlockEntity.java",
 '''   double y=worldPosition.getY()-holoHeight+.5+(shown-1-2*i)*.12*scale;''',
 '''   // V173_B357_SERVER_TEXT_UP: bottom line on tabletop when HEIGHT=1.
   double y=worldPosition.getY()+holoHeight+(shown-1-i)*.24*scale;''')

# The GUI must explain the new behavior rather than the earlier below-table
# semantics. Do not change the size or radius mode-specific controls.
gui="client/HologramConfigScreen.java"
change(gui,
 '''"Height below table"''',
 '''"Height above table"''')
change(gui,
 '''"HEIGHT (BLOCKS BELOW)"''',
 '''"HEIGHT (BLOCKS UP)"''')
change(gui,
 '''"HEIGHT 1 = 1 block below holo table"''',
 '''"HEIGHT 1 = tabletop; each +1 moves up 1 block"''')

assert "V173_B357_MAP_BOTTOM_ALIGNED" in (J/render).read_text(encoding="utf-8")
assert "V173_B357_NETWORK_BASELINE" in (J/render).read_text(encoding="utf-8")
assert "V173_B357_SERVER_TEXT_UP" in (J/"blockentity/NetworkDeviceBlockEntity.java").read_text(encoding="utf-8")
assert "HEIGHT 1 = tabletop; each +1 moves up 1 block" in (J/gui).read_text(encoding="utf-8")
print("V173_B357_ALL_MODES_TABLETOP_UP_HEIGHT_PASS")
