#!/usr/bin/env python3
"""v22: show only complete minimap terrain; cap zoom dynamically, never fabricate pixels."""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/client"

def replace(path,old,new):
    s=path.read_text("utf-8")
    assert s.count(old)==1,("V22_COMPLETE_MAP_SOURCE_DRIFT",path.name,old[:100],s.count(old))
    path.write_text(s.replace(old,new,1),"utf-8")

prefs=J/"V178MiniPreferences.java"
replace(prefs,"public static int cropPixels(){ensure();return Math.max(16,",
"""public static int cropPixels(){
  int requested=requestedCropPixels();
  return V178ClaimsClient.option("terrain")?V178MiniRaster.effectiveCrop(requested):requested;
 }
 public static int requestedCropPixels(){ensure();return Math.max(16,""")

# Keep prefetch driven by the user's REQUESTED zoom, not the temporary safe crop.
terrain=J/"V178TerrainMap.java"
replace(terrain,
"int visible=Math.max(2,Math.min(20,(V178MiniPreferences.cropPixels()+31)/32+1));",
"int visible=Math.max(2,Math.min(20,(V178MiniPreferences.requestedCropPixels()+31)/32+1));")

r=J/"V178MiniRaster.java"
replace(r,"private static boolean valid;",
"""private static boolean valid;
 private static int v22LastRequested=-1;
 private static java.lang.ref.WeakReference<ClientLevel> v22RasterWorld=
     new java.lang.ref.WeakReference<>(null);
 public static boolean hasCompleteTerrain(){
  return valid&&v22RasterWorld.get()!=null&&v22RasterWorld.get()==Minecraft.getInstance().level;
 }
 public static int effectiveCrop(int requested){
  return hasCompleteTerrain()?Math.min(requested,lastCrop):requested;
 }
 // Search nested block rectangles; even and odd crops both remain centered.
 // Conservative square coverage also guarantees the entire circular interior.
 private static boolean v22Covered(int x,int z,int crop,int baseX,int baseZ,
       int stride,int[][] tiles){
  int left=x-crop/2,top=z-crop/2;
  int minX=(left>>4)-baseX,maxX=((left+crop-1)>>4)-baseX;
  int minZ=(top>>4)-baseZ,maxZ=((top+crop-1)>>4)-baseZ;
  for(int zz=minZ;zz<=maxZ;zz++)for(int xx=minX;xx<=maxX;xx++){
   int[] tile=tiles[zz*stride+xx];
   if(tile==null||tile.length!=256)return false;
  }
  return true;
 }
 private static int v22SafeCrop(int x,int z,int requested,int baseX,int baseZ,
       int stride,int[][] tiles){
  int lo=0,hi=requested;
  while(lo<hi){
   int mid=lo+(hi-lo+1)/2;
   if(v22Covered(x,z,mid,baseX,baseZ,stride,tiles))lo=mid;
   else hi=mid-1;
  }
  return lo;
 }""")
replace(r,"if(!dim.equals(dimension)){reset();dimension=dim;}",
"""if(!dim.equals(dimension)||v22RasterWorld.get()!=world){
   reset();dimension=dim;v22LastRequested=-1;
   v22RasterWorld=new java.lang.ref.WeakReference<>(world);
  }""")
replace(r,"int crop=V178MiniPreferences.cropPixels(),rev=V178TerrainMap.terrainRevision();",
"int requested=V178MiniPreferences.requestedCropPixels(),crop=requested,rev=V178TerrainMap.terrainRevision();")
replace(r,"&&crop==lastCrop&&rev==lastRevision",
"&&requested==v22LastRequested&&rev==lastRevision")
# Fetch the originally requested tile rectangle once, then choose a fully
# covered crop. Build the final tint array using the final (not requested) grid.
a=r.read_text("utf-8")
needle="int[][] tiles=new int[chunksX*chunksZ][];"
assert a.count(needle)==1
replace(r,needle,r'''// V22: never upload missing terrain. First inspect the requested area.
   int baseX=firstCX,baseZ=firstCZ,baseStride=chunksX;
   int[][] available=new int[chunksX*chunksZ][];
   for(int zz=0;zz<chunksZ;zz++)for(int xx=0;xx<chunksX;xx++)
    available[zz*chunksX+xx]=V178TerrainMap.pixels(world,firstCX+xx,firstCZ+zz);
   crop=v22SafeCrop(x,z,requested,baseX,baseZ,baseStride,available);
   // Even at maximum zoom no complete useful 16-block crop exists yet:
   // hide the terrain layer and show a loading label, never a fake/black map.
   if(crop<16){valid=false;v22LastRequested=-1;return;}
   startX=x-crop/2;startZ=z-crop/2;
   firstCX=startX>>4;firstCZ=startZ>>4;
   chunksX=((startX+crop-1)>>4)-firstCX+1;
   chunksZ=((startZ+crop-1)>>4)-firstCZ+1;
   int[][] tiles=new int[chunksX*chunksZ][];''')
replace(r,"tiles[index]=V178TerrainMap.pixels(world,firstCX+xx,firstCZ+zz);",
"""tiles[index]=available[(firstCZ+zz-baseZ)*baseStride+firstCX+xx-baseX];""")
# The validated final grid has no missing tiles: no UNKNOWN fallback can reach GPU.
replace(r,"int color=tile==null?UNKNOWN:tile[pixelRow+B1799_COLUMN_PIXEL[px]];",
"int color=tile[pixelRow+B1799_COLUMN_PIXEL[px]];")
replace(r,"valid=true;lastX=x;lastZ=z;lastCrop=crop;lastRevision=rev;",
"valid=true;v22LastRequested=requested;lastX=x;lastZ=z;lastCrop=crop;lastRevision=rev;")
replace(r,"if(!valid||texture==null)return;",
"if(!hasCompleteTerrain()||texture==null)return;")
# HUD must not leave a dark placeholder with compass/markers when no complete
# useful map is available. Keep the regular terrain-off claim mode unchanged.
c=J/"V178ClaimsClient.java"
replace(c,"if(drawTerrain)V178TerrainMap.drawViewport(mc.level,g,cx,cz,",
"""if(drawTerrain&&!V178MiniRaster.hasCompleteTerrain()){
    g.text(mc.font,"Karte lädt...",ox+4,oy+15,0xffcce8f6);
    return;
   }
   if(drawTerrain)V178TerrainMap.drawViewport(mc.level,g,cx,cz,""")
assert "V178MiniRaster.effectiveCrop(requested)" in prefs.read_text("utf-8")
assert "V178MiniPreferences.requestedCropPixels()" in terrain.read_text("utf-8")
s=r.read_text("utf-8")
assert "tile==null?UNKNOWN" not in s
assert "b1883Tint(color,claim" in s
print("V22_COMPLETE_TERRAIN_ONLY_ADAPTIVE_ZOOM_PASS")
