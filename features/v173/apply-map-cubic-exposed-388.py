#!/usr/bin/env python3
"""Build 388: exact map footprint, uniform voxel proportions and visible terrain.

This post-B378 patch preserves the complete Network/Custom projection and
changes only the native MAP sampler. Minecraft block dimensions are never
stretched, and hidden terrain cannot obscure the miniature from above.
"""
import os
from pathlib import Path

p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/client/V173WorldGhostRenderer.java"
s=p.read_text(encoding="utf-8")
def change(old,new):
 global s
 assert s.count(old)==1,("B388_MAP_SOURCE_DRIFT",old[:130],s.count(old))
 s=s.replace(old,new,1)

assert "B378_ISOTROPIC_MAP" in s and "private static void networkProjection(" in s
assert "V173_B362_BUNDLE_CONNECTIONS" in s
# Budget sampled *volume*, before exposed-face culling. More detail at 1 chunk;
# large/chunky selections remain bounded. The stride is shared by X/Y/Z.
change("((worldHeight+stride-1)/stride)>4096L)stride++;",
       "((worldHeight+stride-1)/stride)>8192L)stride++;")

# B378 rendered ceil(side/stride)*stride/sourceSide visual units, spilling
# beyond the requested footprint. The final partial X/Z cells must fit too.
change("""  final double scale=(double)be.holoMapSize()/side;
  final double cube=stride*scale; // sx == sy == sz, always a true cube.
  final int columns=(side+stride-1)/stride;
  final int layers=(worldHeight+stride-1)/stride;
  final double originX=t.getX()+.5D-side*scale/2D;
  final double originZ=t.getZ()+.5D-side*scale/2D;""",
"""  // B388_EXACT_MAP_FOOTPRINT: columns*cube == configured map size.
  final int columns=(side+stride-1)/stride;
  final int layers=(worldHeight+stride-1)/stride;
  final double scale=(double)be.holoMapSize()/(columns*stride);
  final double cube=stride*scale; // Identical XYZ size, no elongated tiles.
  final double originX=t.getX()+.5D-columns*cube/2D;
  final double originZ=t.getZ()+.5D-columns*cube/2D;""")

# Sample from the upper face of each *uniform-sized* LOD cube. The previous
# midpoint sample often selected interior stone, erasing visible roofs.
# Mutable cursors avoid creating one BlockPos per Y sample.
change("""  for(int ix=0;ix<columns;ix++)for(int iz=0;iz<columns;iz++){""",
"""  BlockPos.MutableBlockPos b388Cursor=new BlockPos.MutableBlockPos();
  for(int ix=0;ix<columns;ix++)for(int iz=0;iz<columns;iz++){""")
change("""    int sy=low+(high-low)/2;
    BlockPos sample=new BlockPos(sx,sy,sz);
    if(!mc.level.hasChunkAt(sample))continue;
    BlockState real=mc.level.getBlockState(sample);
    if(real.isAir()){
     // Do not miss the real upper surface when it falls inside a
     // coarse cube whose midpoint happens to be in the air.
     for(int y=high;y>=low;y--){
      BlockState candidate=mc.level.getBlockState(new BlockPos(sx,y,sz));
      if(!candidate.isAir()){real=candidate;break;}
     }
    }
    if(real.isAir())continue;
    BlockState state=real.getFluidState().isEmpty()?real:
       Blocks.BLUE_STAINED_GLASS.defaultBlockState();""",
"""    // B388_EXPOSED_MAP: always choose the actual uppermost occupied Y
    // inside the cube (including thin roofs, trees and uneven terrain).
    BlockState real=Blocks.AIR.defaultBlockState();
    int pickedY=low;
    for(int y=high;y>=low;y--){
     b388Cursor.set(sx,y,sz);
     BlockState candidate=mc.level.getBlockState(b388Cursor);
     if(!candidate.isAir()){real=candidate;pickedY=y;break;}
    }
    if(real.isAir())continue;
    // A cropped edge or the cut bottom is intentionally a visible face.
    // Inside the volume render only blocks exposed to air: hidden solid
    // stone must not eat render budget or obscure the actual terrain.
    boolean exposed=layer==0||layer==layers-1||
       ix==0||iz==0||ix==columns-1||iz==columns-1;
    if(!exposed){
     BlockPos at=new BlockPos(sx,pickedY,sz);
     for(net.minecraft.core.Direction direction:net.minecraft.core.Direction.values()){
      BlockPos adjacent=at.relative(direction);
      if(mc.level.hasChunkAt(adjacent)&&mc.level.getBlockState(adjacent).isAir()){
       exposed=true;break;
      }
     }
    }
    if(!exposed)continue;
    BlockState state=real.getFluidState().isEmpty()?real:
       Blocks.BLUE_STAINED_GLASS.defaultBlockState();""")
for token in ("B388_EXACT_MAP_FOOTPRINT","B388_EXPOSED_MAP",
              "cube,cube,cube","private static void networkProjection(",
              "V173_B351_EXACT_NETWORK_SIZE","V173_B362_BUNDLE_CONNECTIONS",
              "B368_MAP_TABLETOP_CALIBRATION"):
 assert token in s,("B388_MAP_CONTRACT",token)
p.write_text(s,encoding="utf-8")
print("B388_EXACT_CUBE_FOOTPRINT_EXPOSED_TERRAIN_PASS")
