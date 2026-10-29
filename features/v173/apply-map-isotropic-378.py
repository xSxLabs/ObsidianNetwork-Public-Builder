#!/usr/bin/env python3
"""B378: true isotropic MAP voxels and independent projection size.

The reference Maps3D uses volumetric LOD and exposed faces. Our native
renderer retains its own block-model rendering, but uses ONE XYZ resolution
and ONE Minecraft block scale. No rectangular/tall slab approximations.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def replace(rel,old,new):
 p=J/rel
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("B378_SOURCE_DRIFT",rel,old[:120],s.count(old))
 p.write_text(s.replace(old,new,1),encoding="utf-8")
be="blockentity/NetworkDeviceBlockEntity.java"
replace(be,
 " private int holoMapStartY=Integer.MIN_VALUE;",
 """ // B378_MAP_SIZE: independent of radius and other hologram modes.
 private int holoMapSize=4;
 public int holoMapSize(){return holoMapSize;}
 private int holoMapStartY=Integer.MIN_VALUE;""")
replace(be,
 "holoWidth=Math.max(1,Math.min(32,width));holoHeight=Math.max(1,Math.min(32,height));",
 """if("map".equals(mode))holoMapSize=Math.max(1,Math.min(32,width));
  else holoWidth=Math.max(1,Math.min(32,width));
  holoHeight=Math.max(1,Math.min(32,height));""")
replace(be,
 'out.putInt("holo_radius",holoRadius);out.putInt("holo_start_y",holoMapStartY);',
 'out.putInt("holo_radius",holoRadius);out.putInt("holo_start_y",holoMapStartY);out.putInt("holo_map_size",holoMapSize);')
replace(be,
 'holoMapStartY=in.getIntOr("holo_start_y",Integer.MIN_VALUE);',
 'holoMapStartY=in.getIntOr("holo_start_y",Integer.MIN_VALUE);holoMapSize=Math.max(1,Math.min(32,in.getIntOr("holo_map_size",4)));')
gui="client/HologramConfigScreen.java"
replace(gui,
 'private EditBox content,color,size,heightInput,radius,startY,depthInput;',
 'private EditBox content,color,size,heightInput,radius,startY,depthInput,mapSize;')
replace(gui,
 '''  depthInput=make(bx+108,by+127,85,"Depth blocks",be==null?"48":(!"map".equals(be.holoMode())&&be.holoDepth()<16?"48":""+be.holoDepth()),3);''',
 '''  depthInput=make(bx+108,by+127,85,"Depth blocks",be==null?"48":(!"map".equals(be.holoMode())&&be.holoDepth()<16?"48":""+be.holoDepth()),3);
  // B378_MAP_SIZE_GUI: independent world radius versus visual width.
  mapSize=make(bx+204,by+127,75,"Map size (blocks)",be==null?"4":""+be.holoMapSize(),2);''')
replace(gui,
 '  depthInput.visible=map;depthInput.active=map;',
 '''  depthInput.visible=map;depthInput.active=map;
  mapSize.visible=map;mapSize.active=map;''')
replace(gui,
 '  int s=val(size,5,1,32),r=val(radius,1,1,12);',
 '  int s=mode.equals("map")?val(mapSize,4,1,32):val(size,5,1,32),r=val(radius,1,1,12);')
replace(gui,
 'g.text(font,"START WORLD Y     DEPTH (BLOCKS)",bx+12,by+112,0xffd3e4f1);',
 'g.text(font,"START Y               DEPTH                 MAP SIZE",bx+12,by+112,0xffd3e4f1);')
renderer="client/V173WorldGhostRenderer.java"
p=J/renderer
s=p.read_text(encoding="utf-8")
a=s.index(" private static java.util.List<MapVoxel> sampleMap(Minecraft mc,BlockPos t,")
b=s.index(" private static net.minecraft.client.multiplayer.ClientLevel portalWorld;",a)
assert a<b and "private static void networkProjection(" in s[:a], "B378_NETWORK_RENDERER_MUST_SURVIVE"
new=r''' // V173_VOLUME_MAP_327 / B368_MAP_FIXED_VOLUME: loaded-world 3D data.
 // B378_ISOTROPIC_MAP: one grid stride, one physical scale, cube voxels.
 // B368_MAP_TABLETOP_CALIBRATION: translate whole model, never stretch Y.
 // V173_B357_MAP_BOTTOM_ALIGNED: preserve the chosen hologram height.
 private static java.util.List<MapVoxel> sampleMap(Minecraft mc,BlockPos t,
                                                    NetworkDeviceBlockEntity be){
  java.util.ArrayList<MapVoxel> out=new java.util.ArrayList<>();
  if(t==null||mc.level==null)return out;
  final int radiusChunks=Math.max(1,Math.min(12,be.holoRadius()));
  final int radius=16*radiusChunks; // B378 preserved radius-in-chunks contract.
  final int side=2*radius+1;
  final int fromY=Math.max(mc.level.getMinY(),
       Math.min(mc.level.getMaxY()-1,be.holoMapStartY()));
  final int depth=Math.max(1,Math.min(128,be.holoDepth()));
  final int bottomY=Math.max(mc.level.getMinY(),fromY-depth+1);
  final int worldHeight=fromY-bottomY+1;
  // Every axis shares ONE integer LOD. Budget the entire XYZ volume,
  // not an unrelated XZ grid with stretched vertically sampled layers.
  int stride=1;
  while((long)((side+stride-1)/stride)*((side+stride-1)/stride)*
        ((worldHeight+stride-1)/stride)>4096L)stride++;
  final double scale=(double)be.holoMapSize()/side;
  final double cube=stride*scale; // sx == sy == sz, always a true cube.
  final int columns=(side+stride-1)/stride;
  final int layers=(worldHeight+stride-1)/stride;
  final double originX=t.getX()+.5D-side*scale/2D;
  final double originZ=t.getZ()+.5D-side*scale/2D;
  for(int ix=0;ix<columns;ix++)for(int iz=0;iz<columns;iz++){
   int wx=t.getX()-radius+ix*stride;
   int wz=t.getZ()-radius+iz*stride;
   // Sample the middle of each LOD cube (including its topmost Y slab).
   int sx=Math.min(t.getX()+radius,wx+stride/2);
   int sz=Math.min(t.getZ()+radius,wz+stride/2);
   if(!mc.level.hasChunkAt(new BlockPos(sx,fromY,sz)))continue;
   for(int layer=0;layer<layers;layer++){
    int low=bottomY+layer*stride;
    int high=Math.min(fromY,low+stride-1);
    int sy=low+(high-low)/2;
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
       Blocks.BLUE_STAINED_GLASS.defaultBlockState();
    out.add(new MapVoxel(state,originX+ix*cube,
          layer*cube,originZ+iz*cube,cube,cube,cube));
   }
  }
  if(out.isEmpty())return out;
  double lowest=Double.POSITIVE_INFINITY;
  for(MapVoxel voxel:out)lowest=Math.min(lowest,voxel.y());
  final double tabletop=t.getY()+be.holoHeight();
  double shift=tabletop-lowest;
  java.util.ArrayList<MapVoxel> aligned=new java.util.ArrayList<>(out.size());
  for(MapVoxel v:out)
   aligned.add(new MapVoxel(v.state(),v.x(),v.y()+shift,v.z(),
                            v.sx(),v.sy(),v.sz()));
  return aligned;
 }

'''
s=s[:a]+new+s[b:]
for token in ("private static void networkProjection(","V173_B351_EXACT_NETWORK_SIZE",
              "V173_B362_BUNDLE_CONNECTIONS","B378_ISOTROPIC_MAP",
              "B368_MAP_TABLETOP_CALIBRATION"):
 assert token in s,("B378_RENDERER_CONTRACT",token)
p.write_text(s,encoding="utf-8")
print("B378_MAP_ISOTROPIC_AND_SIZE_PASS")
