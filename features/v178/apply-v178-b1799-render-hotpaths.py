#!/usr/bin/env python3
"""B1799 / v1.7.8 v11: exact-pixel minimap CPU reduction and leak-safe facade light identity.

Runs after B1792. Fail closed on generated-source drift. No changes to the
map samples, sample cadence, visual pixels, game ticks, block mechanics, or version.
"""
import os
import re
from pathlib import Path

JAVA = Path(os.environ['V1_SOURCE_ROOT']) / 'dev/obsidiannetwork'

def replace_once(path, old, new):
    src = path.read_text(encoding='utf-8')
    assert src.count(old) == 1, ('B1799_SOURCE_DRIFT', str(path), src.count(old), old[:85])
    path.write_text(src.replace(old, new, 1), encoding='utf-8')

mini = JAVA / 'client/V178MiniRaster.java'
replace_once(mini,
''' private static final int SIDE=19*16,UNKNOWN=0xff1c2530;''',
''' private static final int SIDE=19*16,UNKNOWN=0xff1c2530;
 // Entirely camera-relative and independent of the current world or zoom.
 // Cache the EXACT original circular pixel mask once instead of computing
 // ninety thousand squared distances for each movement/terrain refresh.
 private static final byte[] B1799_CIRCLE_MASK=b1799CircleMask();
 private static final int[] B1799_COLUMN_CHUNK=new int[SIDE];
 private static final int[] B1799_COLUMN_PIXEL=new int[SIDE];
 private static byte[] b1799CircleMask(){
  byte[] mask=new byte[SIDE*SIDE];
  double radius=(SIDE-1)*0.5,inner=radius-1.25;
  double outer2=radius*radius,inner2=inner*inner;
  for(int py=0;py<SIDE;py++)for(int px=0;px<SIDE;px++){
   double dx=px+0.5-SIDE*0.5,dz=py+0.5-SIDE*0.5;
   double distance=dx*dx+dz*dz;
   mask[py*SIDE+px]=(byte)(distance>outer2?2:distance>=inner2?1:0);
  }
  return mask;
 }''')

replace_once(mini,
'''  double radius=(SIDE-1)*0.5,inner=radius-1.25;
  double outer2=radius*radius,inner2=inner*inner;
  for(int py=0;py<SIDE;py++)for(int px=0;px<SIDE;px++){
   int wx=startX+(int)((long)px*crop/SIDE);
   int wz=startZ+(int)((long)py*crop/SIDE);
   int[] tile=tiles[((wz>>4)-firstCZ)*chunksX+((wx>>4)-firstCX)];
   int color=tile==null?UNKNOWN:tile[(wz&15)*16+(wx&15)];
   if(round){
    double dx=px+0.5-SIDE*0.5,dz=py+0.5-SIDE*0.5;
    double distance=dx*dx+dz*dz;
    if(distance>outer2)color=0;
    else if(distance>=inner2)color=0xff95adbc;
   }
   img.setPixel(px,py,color);
  }''',
'''  // The zoom resampling is separable: X never depends on Y. Reuse the 304
  // exact X samples for every raster row; no in-loop division or distance math.
  for(int px=0;px<SIDE;px++){
   int wx=startX+(int)((long)px*crop/SIDE);
   B1799_COLUMN_CHUNK[px]=(wx>>4)-firstCX;
   B1799_COLUMN_PIXEL[px]=wx&15;
  }
  for(int py=0;py<SIDE;py++){
   int wz=startZ+(int)((long)py*crop/SIDE);
   int tileRow=((wz>>4)-firstCZ)*chunksX,pixelRow=(wz&15)*16;
   int maskRow=py*SIDE;
   for(int px=0;px<SIDE;px++){
    int[] tile=tiles[tileRow+B1799_COLUMN_CHUNK[px]];
    int color=tile==null?UNKNOWN:tile[pixelRow+B1799_COLUMN_PIXEL[px]];
    if(round){
     byte mask=B1799_CIRCLE_MASK[maskRow+px];
     if(mask==2)color=0;
     else if(mask==1)color=0xff95adbc;
    }
    img.setPixel(px,py,color);
   }
  }''')

# A weak-key map must NOT have a strong Level reference in its value. Check
# world identity through WeakReference so a BlockEntity reused across a world
# switch cannot temporarily reuse a previous world's light result.
facade = JAVA / 'client/render/CableFacadeRenderer.java'
replace_once(facade,
'''  final long tick;final int packed;
  B1792Light(long t,int p){tick=t;packed=p;}''',
'''  final long tick;final int packed;
  final java.lang.ref.WeakReference<net.minecraft.world.level.Level> level;
  B1792Light(long t,int p,net.minecraft.world.level.Level world){
   tick=t;packed=p;level=new java.lang.ref.WeakReference<>(world);
  }''')
src = facade.read_text(encoding='utf-8')
be = re.findall(r'B1792_LIGHTS\.get\(([A-Za-z_$][\w$]*)\)', src)
assert len(be) == 1, ('B1799_FACADE_ENTITY_ANCHOR', len(be))
replace_once(facade,
 'if(cached!=null&&xsxNow>=cached.tick&&xsxNow-cached.tick<5L)',
 f'if(cached!=null&&cached.level.get()=={be[0]}.getLevel()'
 '&&xsxNow>=cached.tick&&xsxNow-cached.tick<5L)')
src = facade.read_text(encoding='utf-8')
pattern = r'new B1792Light\(xsxNow,([A-Za-z_$][\w$]*\.lightCoords)\)'
source, matches = re.subn(pattern,
 lambda m: f'new B1792Light(xsxNow,{m.group(1)},{be[0]}.getLevel())',src)
assert matches == 1, ('B1799_FACADE_CTOR_ANCHOR', matches)
facade.write_text(source,encoding='utf-8')
print('B1799_V11_MINIMAP_EXACT_RASTER_SEPARABLE_X_CIRCLE_MASK_AND_WEAK_WORLD_PASS')
