#!/usr/bin/env python3
"""B1883: continuous chunk-registered blue claims on the GPU minimap.

Independent implementation: authoritative server snapshots populate a
dimension-specific client cache. Both maps project from chunk coordinates.
The minimap composes translucent tint into the *same moving terrain raster*,
eliminating the mismatch between interpolated terrain and static GUI quads.
No world/block scans, forced chunks or network reads during GUI rendering.
"""
from pathlib import Path
import os
import re

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def replace(rel,old,new):
    p=J/rel
    s=p.read_text(encoding="utf-8")
    if s.count(old)==1:
        p.write_text(s.replace(old,new,1),encoding="utf-8")
        return
    # Generators use mixed Java indentation. Match complete statements,
    # never partial tokens or a second unrelated block.
    lines=old.splitlines()
    pattern=r"(?m)^[ \t]*"+r"\n".join(
        r"[ \t]*"+re.escape(line.lstrip()) for line in lines)
    matches=list(re.finditer(pattern,s))
    assert len(matches)==1,("B1883_SOURCE_DRIFT",rel,old[:130],len(matches))
    a=matches[0]
    p.write_text(s[:a.start()]+new+s[a.end():],encoding="utf-8")

client="client/V178ClaimsClient.java"
replace(client,
    '  private static volatile V178ClaimsSnapshot last;',
    '''  private static volatile V178ClaimsSnapshot last;
  // B1883: retain chunk ownership when a 25x25 server snapshot recenters.
  // Only claimed positions occupy memory; zero/removed positions are evicted.
  private static final java.util.concurrent.ConcurrentHashMap<Long,Byte>
      B1883_STATUS=new java.util.concurrent.ConcurrentHashMap<>();
  private static volatile String B1883_DIMENSION="";
  private static volatile int B1883_REVISION;
  private static long b1883Key(int x,int z){
   return ((long)x<<32)|(z&0xffffffffL);
  }
  public static int claimRevision(){return B1883_REVISION;}
  public static byte claimStatus(net.minecraft.client.multiplayer.ClientLevel world,
                                  int cx,int cz){
   if(world==null||!world.dimension().identifier().toString().equals(B1883_DIMENSION))
    return 0;
   return B1883_STATUS.getOrDefault(b1883Key(cx,cz),(byte)0);
  }
  private static void b1883Receive(V178ClaimsSnapshot snapshot){
   Minecraft mc=Minecraft.getInstance();
   if(mc.level==null || !snapshot.dimension().equals(
        mc.level.dimension().identifier().toString()))return;
   if(!snapshot.dimension().equals(B1883_DIMENSION)){
    B1883_STATUS.clear();
    B1883_DIMENSION=snapshot.dimension();
    B1883_REVISION++;
   }
   int r=snapshot.radius();
   byte[] data=snapshot.statuses();
   if(r<0||r>12||data.length!=(2*r+1)*(2*r+1))return;
   boolean changed=false;
   int side=2*r+1;
   for(int dz=-r;dz<=r;dz++)for(int dx=-r;dx<=r;dx++){
    int st=Byte.toUnsignedInt(data[(dz+r)*side+dx+r]);
    long key=b1883Key(snapshot.cx()+dx,snapshot.cz()+dz);
    Byte previous=st==0?B1883_STATUS.remove(key):
          B1883_STATUS.put(key,(byte)st);
    if((previous==null?0:Byte.toUnsignedInt(previous))!=st)changed=true;
   }
   last=snapshot;
   if(changed)B1883_REVISION++;
  }''')
replace(client,
    'event.register(V178ClaimsSnapshot.TYPE,(message,context)->last=message);',
    'event.register(V178ClaimsSnapshot.TYPE,(message,context)->b1883Receive(message));')
replace(client,
    '   last=null;lastRequestX=Integer.MIN_VALUE;lastRequestZ=Integer.MIN_VALUE;',
    '''   last=null;lastRequestX=Integer.MIN_VALUE;lastRequestZ=Integer.MIN_VALUE;
    if(!B1883_STATUS.isEmpty()||!B1883_DIMENSION.isEmpty()){
     B1883_STATUS.clear();B1883_DIMENSION="";B1883_REVISION++;
    }''')
# The old minimap quads were not interpolated with the scrolling terrain GPU.
# When terrain is enabled, only the raster draws claims; for terrain-off mode
# the previous rectangle painter still works as a low-cost fallback.
replace(client,
    'if(drawClaims)V178TerrainMap.drawClaim(g,x,y,markerStep,',
    'if(drawClaims&&!drawTerrain)V178TerrainMap.drawClaim(g,x,y,markerStep,')

# Fullscreen map used to blank every old claim when the network snapshot was
# still in flight or a map pan changed the center. Draw from cached chunk
# coordinates instead and let the refreshed snapshot update the cache.
screen="client/V178ClaimsMapScreen.java"
replace(screen,
    'int state=good?Byte.toUnsignedInt(V178ClaimsClient.state(map,cxWorld,czWorld)):0;',
    'int state=Byte.toUnsignedInt(V178ClaimsClient.claimStatus(world,cxWorld,czWorld));')
# Older versions coupled grid display to ownership. Later worldmap renderers
# may have already separated these toggles; handle both safely.
screen_path=J/screen
screen_src=screen_path.read_text("utf-8")
for grid_gate in ("if(!grid||!showClaims)continue;",
                  "if(!grid || !showClaims)continue;"):
    if grid_gate in screen_src:
        screen_src=screen_src.replace(grid_gate,
             "if(!showClaims)continue; // grid toggle never hides ownership tint",1)
screen_path.write_text(screen_src,"utf-8")

raster="client/V178MiniRaster.java"
replace(raster,
    ' private static int lastX=Integer.MIN_VALUE,lastZ,lastCrop,lastRevision=-1;',
    ''' private static int lastX=Integer.MIN_VALUE,lastZ,lastCrop,lastRevision=-1;
 private static int b1883LastClaimRevision=-1;
 private static boolean b1883LastClaimsOption;''')
replace(raster,
    'dimension="";valid=false;lastX=Integer.MIN_VALUE;lastRevision=-1;',
    'dimension="";valid=false;lastX=Integer.MIN_VALUE;lastRevision=-1;b1883LastClaimRevision=-1;')
replace(raster,
    'int crop=V178MiniPreferences.cropPixels(),rev=V178TerrainMap.terrainRevision();',
    '''int crop=V178MiniPreferences.cropPixels(),rev=V178TerrainMap.terrainRevision();
   int claimRev=V178ClaimsClient.claimRevision();
   boolean claimOption=V178ClaimsClient.option("claims");''')
replace(raster,
    'if(valid&&x==lastX&&z==lastZ&&crop==lastCrop&&rev==lastRevision',
    '''if(valid&&x==lastX&&z==lastZ&&crop==lastCrop&&rev==lastRevision
      &&claimRev==b1883LastClaimRevision
      &&claimOption==b1883LastClaimsOption''')
replace(raster,
    '''  int[][] tiles=new int[chunksX*chunksZ][];
   for(int zz=0;zz<chunksZ;zz++)for(int xx=0;xx<chunksX;xx++)
    tiles[zz*chunksX+xx]=V178TerrainMap.pixels(world,firstCX+xx,firstCZ+zz);''',
    '''  int[][] tiles=new int[chunksX*chunksZ][];
   byte[] b1883Claims=new byte[chunksX*chunksZ];
   boolean b1883ShowClaims=claimOption;
   for(int zz=0;zz<chunksZ;zz++)for(int xx=0;xx<chunksX;xx++){
    int index=zz*chunksX+xx;
    tiles[index]=V178TerrainMap.pixels(world,firstCX+xx,firstCZ+zz);
    if(b1883ShowClaims)b1883Claims[index]=V178ClaimsClient.claimStatus(
        world,firstCX+xx,firstCZ+zz);
   }''')
replace(raster,
    '  for(int py=0;py<SIDE;py++){\n   int wz=startZ+(int)((long)py*crop/SIDE);',
    '''  // Precompute chunk rims just once per X-column; no additional world IO.
  boolean[] b1883XBorder=new boolean[SIDE];
  for(int px=0;px<SIDE;px++)
   b1883XBorder[px]=px==0||px==SIDE-1||
       B1799_COLUMN_CHUNK[px] != B1799_COLUMN_CHUNK[px-1]||
       B1799_COLUMN_CHUNK[px] != B1799_COLUMN_CHUNK[px+1];
  for(int py=0;py<SIDE;py++){
   int wz=startZ+(int)((long)py*crop/SIDE);
   int prevWz=py==0?wz-16:startZ+(int)((long)(py-1)*crop/SIDE);
   int nextWz=py==SIDE-1?wz+16:startZ+(int)((long)(py+1)*crop/SIDE);
   boolean b1883ZBorder=(wz>>4)!=(prevWz>>4)||(wz>>4)!=(nextWz>>4);''')
replace(raster,
    '''    img.setPixel(px,py,color);''',
    '''    // The claim tint and terrain share the identical pixel projection.
    // This prevents flicker or sliding rectangles when the player moves
    // between ticks (the whole texture is interpolated as one layer).
    if(b1883ShowClaims&&(!round||B1799_CIRCLE_MASK[maskRow+px]==0)){
     int claim=b1883Claims[tileRow+B1799_COLUMN_CHUNK[px]]&3;
     if(claim!=0)
      color=b1883Tint(color,claim,b1883ZBorder||b1883XBorder[px]);
    }
    img.setPixel(px,py,color);''')
replace(raster,
    ' public static void draw(GuiGraphicsExtractor g,int x,int y,int width){',
    ''' private static int b1883Tint(int color,int owner,boolean edge){
  int tint=switch(owner){
   case 1->0x79b4ff;case 2->0x6acaf2;default->0x7e94d5;
  };
  // Subtle transparent fill; clear readable 1px equivalent chunk rims.
  int alpha=edge?175:78;
  int rr=(((color>>16)&255)*(255-alpha)+((tint>>16)&255)*alpha)/255;
  int gg=(((color>>8)&255)*(255-alpha)+((tint>>8)&255)*alpha)/255;
  int bb=((color&255)*(255-alpha)+(tint&255)*alpha)/255;
  return 0xff000000|(rr<<16)|(gg<<8)|bb;
 }
 public static void draw(GuiGraphicsExtractor g,int x,int y,int width){''')
replace(raster,
    'valid=true;lastX=x;lastZ=z;lastCrop=crop;lastRevision=rev;',
    'valid=true;lastX=x;lastZ=z;lastCrop=crop;lastRevision=rev;b1883LastClaimRevision=claimRev;b1883LastClaimsOption=claimOption;')

# Verify the texture path, client status cache, shared worldmap status and old
# authority/permission boundaries. This never reimplements the claim server.
c=(J/client).read_text("utf-8")
w=(J/screen).read_text("utf-8")
m=(J/raster).read_text("utf-8")
for tok in ("B1883_STATUS", "B1883_REVISION", "b1883Receive(message)",
            'if(drawClaims&&!drawTerrain)V178TerrainMap.drawClaim'):
 assert tok in c,("B1883_CLIENT_GATE",tok)
for tok in ("V178ClaimsClient.claimStatus(world,cxWorld,czWorld)",
            "if(!showClaims)continue"):
 assert tok in w,("B1883_WORLDMAP_GATE",tok)
for tok in ("b1883Claims", "claimRev==b1883LastClaimRevision",
            "b1883Tint(color,claim,b1883ZBorder||b1883XBorder[px])",
            "img.setPixel(px,py,color)"):
 assert tok in m,("B1883_RASTER_GATE",tok)
print("B1883_V20_STABLE_CHUNK_COORD_CLAIMS_GPU_RASTER_WORLDMAP_SNAPSHOTS_PASS")
