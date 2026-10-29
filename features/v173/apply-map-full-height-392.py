#!/usr/bin/env python3
"""B392: full world build height MAP from the configured bottom Y."""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
p=J/"client/V173WorldGhostRenderer.java"
s=p.read_text(encoding="utf-8")
old='''  final int fromY=Math.max(mc.level.getMinY(),
       Math.min(mc.level.getMaxY()-1,be.holoMapStartY()));
  final int depth=Math.max(1,Math.min(128,be.holoDepth()));
  final int bottomY=Math.max(mc.level.getMinY(),fromY-depth+1);
  final int worldHeight=fromY-bottomY+1;'''
new='''  // B392_MAP_CEILING: full height, Start-Y is BOTTOM, never top.
  final int bottomY=Math.max(mc.level.getMinY(),
       Math.min(mc.level.getMaxY()-1,be.holoMapStartY()));
  final int topY=mc.level.getMaxY()-1;
  final int worldHeight=topY-bottomY+1;'''
assert s.count(old)==1,("B392_MAP_HEIGHT_DRIFT",s.count(old))
s=s.replace(old,new,1)
for old,new in (("new BlockPos(sx,fromY,sz)","new BlockPos(sx,bottomY,sz)"),
                ("int high=Math.min(fromY,low+stride-1);","int high=Math.min(topY,low+stride-1);")):
 assert s.count(old)==1,("B392_Y_AXIS_DRIFT",old,s.count(old))
 s=s.replace(old,new,1)
assert "B388_EXACT_MAP_FOOTPRINT" in s and "cube,cube,cube" in s
p.write_text(s,encoding="utf-8")
p=J/"client/HologramConfigScreen.java"
s=p.read_text(encoding="utf-8")
old='  depthInput.visible=map;depthInput.active=map;'
assert s.count(old)==1
s=s.replace(old,'  // B392_MAP_GUI_START_ONLY: no depth cap; world top automatic.\n  depthInput.visible=false;depthInput.active=false;',1)
old='g.text(font,"START Y               DEPTH                 MAP SIZE",bx+12,by+112,0xffd3e4f1);'
assert s.count(old)==1
s=s.replace(old,'g.text(font,"START Y (BOTTOM)                       MAP SIZE",bx+12,by+112,0xffd3e4f1);',1)
p.write_text(s,encoding="utf-8")
print("B392_MAP_FULL_HEIGHT_PASS")
