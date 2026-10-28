#!/usr/bin/env python3
"""v1.7.3: bounded volumetric MAP mode, sampled from real loaded world blocks.

Runs after Build314. Height moves the entire miniature below the holo table;
radius (in chunks) exclusively determines X/Z footprint and scale.
"""
import os
from pathlib import Path

p = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork/client/V173WorldGhostRenderer.java"
s = p.read_text(encoding="utf-8")
a = " private static java.util.List<MapVoxel> sampleMap(Minecraft mc,BlockPos t,"
b = " private static net.minecraft.client.multiplayer.ClientLevel portalWorld;"
assert s.count(a) == 1 and s.count(b) == 1, ("V173_VOLUMETRIC_MAP_SOURCE_DRIFT",s.count(a),s.count(b))
start = s.index(a)
stop = s.index(b,start)
assert "Heightmap.Types.WORLD_SURFACE" in s[start:stop], "Build314 terrain sampler missing"
assert "originY=t.getY()-be.holoHeight()" in s[start:stop], "projection offset contract changed"

new = r''' // V173_VOLUME_MAP_327: genuine exposed blocks in the miniature, not just a surface skin.
 private static java.util.List<MapVoxel> sampleMap(Minecraft mc,BlockPos t,
                                                     NetworkDeviceBlockEntity be){
  java.util.ArrayList<MapVoxel> out=new java.util.ArrayList<>();
  if(t==null || mc.level==null)return out;
  // Radius = chunks, not blocks. Size is derived automatically in MAP mode.
  int radiusChunks=Math.max(1,Math.min(12,be.holoRadius()));
  int radius=radiusChunks*16,side=radius*2+1;
  // Bounded LOD: a maximum of 40x40 columns across the entire selected area.
  int step=Math.max(1,(side+39)/40);
  int count=(side+step-1)/step;
  int[][] surfaceHeight=new int[count][count];
  BlockState[][] surface=new BlockState[count][count];
  int cx=t.getX(),cz=t.getZ();
  int minY=mc.level.getMinY(),maxY=mc.level.getMaxY();
  int midHeight=mc.level.getHeight(
     net.minecraft.world.level.levelgen.Heightmap.Types.WORLD_SURFACE,cx,cz)-1;
  if(midHeight<minY||midHeight>=maxY)midHeight=t.getY();

  for(int ix=0;ix<count;ix++)for(int iz=0;iz<count;iz++){
   int wx=cx-radius+ix*step,wz=cz-radius+iz*step;
   BlockPos column=new BlockPos(wx,t.getY(),wz);
   // Never request or force-load missing terrain chunks from the client.
   if(!mc.level.hasChunkAt(column))continue;
   int y=mc.level.getHeight(
      net.minecraft.world.level.levelgen.Heightmap.Types.WORLD_SURFACE,wx,wz)-1;
   if(y<minY||y>=maxY)continue;
   BlockState real=mc.level.getBlockState(new BlockPos(wx,y,wz));
   if(real.isAir())continue;
   surfaceHeight[ix][iz]=y;
   surface[ix][iz]=real;
  }

  double footprint=2.5D+radiusChunks*1.25D;
  double perBlock=footprint/side;
  double tile=step*perBlock;
  double originX=t.getX()+.5-footprint/2D;
  double originZ=t.getZ()+.5-footprint/2D;
  // Height=1 means the projection reference is one block UNDER the table.
  // World relief uses original 1:1 XYZ proportions on the miniature.
  double originY=t.getY()-be.holoHeight()+.5D;

  // Surface first: every sampled column gets representation before any caves.
  for(int ix=0;ix<count;ix++)for(int iz=0;iz<count;iz++){
   BlockState real=surface[ix][iz];if(real==null)continue;
   int y=surfaceHeight[ix][iz];
   double x=originX+ix*tile,z=originZ+iz*tile;
   BlockState render=real.getFluidState().isEmpty()?real:Blocks.BLUE_STAINED_GLASS.defaultBlockState();
   out.add(new MapVoxel(render,x,originY+(y-midHeight)*perBlock,z,tile,perBlock,tile));
  }

  // Traverse actual underground/overhang/tree/building faces in depth rounds.
  // Each depth is traversed ACROSS ALL COLUMNS before going deeper, so large
  // radius maps never get cut off after rendering one edge of the world.
  // Two-block vertical samples preserve continuous sidewalls with bounded work.
  final int maxVoxels=4600,maxDepth=48;
  for(int depth=2;depth<=maxDepth && out.size()<maxVoxels;depth+=2){
   for(int ix=0;ix<count&&out.size()<maxVoxels;ix++)
    for(int iz=0;iz<count&&out.size()<maxVoxels;iz++){
     if(surface[ix][iz]==null)continue;
     int y=surfaceHeight[ix][iz]-depth;
     if(y<minY||y>=maxY)continue;
     int wx=cx-radius+ix*step,wz=cz-radius+iz*step;
     BlockPos at=new BlockPos(wx,y,wz);
     // Column was checked loaded above, including missing-neighbor guards.
     BlockState real=mc.level.getBlockState(at);
     if(real.isAir())continue;
     boolean exposed=false;
     for(net.minecraft.core.Direction direction:net.minecraft.core.Direction.values()){
      BlockPos neighbor=at.relative(direction);
      if(mc.level.hasChunkAt(neighbor)&&mc.level.getBlockState(neighbor).isAir()){
       exposed=true;break;
      }
     }
     if(!exposed)continue; // hidden rock should not consume render budget
     BlockState render=real.getFluidState().isEmpty()?real:Blocks.BLUE_STAINED_GLASS.defaultBlockState();
     out.add(new MapVoxel(render,
      originX+ix*tile,originY+(y-midHeight)*perBlock,originZ+iz*tile,
      tile,2D*perBlock,tile));
    }
  }
  return out;
 }

'''
s=s[:start]+new+s[stop:]
assert "V173_VOLUME_MAP_327" in s and "radiusChunks*16" in s
assert "originY=t.getY()-be.holoHeight()" in s
assert "mc.level.hasChunkAt(neighbor)" in s
p.write_text(s,encoding="utf-8")
print("V173_VOLUMETRIC_TERRAIN_327_PASS: loaded-world blocks, bounded 4600, depth 48, scaled radius")
