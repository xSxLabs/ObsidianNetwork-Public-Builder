#!/usr/bin/env python3
"""B1843 / 1.7.8 v18: prioritize missing, *already loaded* terrain while travelling.

The previous 13x13 row-major background pass took many ticks to discover
recently arrived chunk tiles. This client-tick fast path fills missing tiles
center-first, then in travel direction, then across the displayed crop.
No chunk loads, network packets, disk format changes, or render-time world reads.
A shared ~2.4ms deadline retains the old conservative world update cadence.
"""
from pathlib import Path
import os

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
terrain=J/"client/V178TerrainMap.java"
s=terrain.read_text("utf-8")
method="private static void b1802RefreshTravel(ClientLevel world,int cx,int cz){"
assert s.count(method)==1,("B1843_MISSING_TRAVEL_METHOD",s.count(method))
assert "V178MiniRaster.tick(world);" in s
assert "b1810WideCursor++%169" in s
assert "world.hasChunk(cx,cz)?null:archiveLookup(cx,cz)" in s
assert "private static final int ATLAS_UPDATE_TICKS=1;" in s

fastpath=r'''  // B1843: pending live tiles, not stale snapshots, determine travel priority.
  // The map cache is only touched on the client tick. Never load chunks.
  private static int b1843ExploreCursor;
  private static int b1843TryLoaded(ClientLevel world,
      LinkedHashMap<Long,int[]> known,int x,int z,long start,int done){
   if(done>=8||System.nanoTime()-start>=2_000_000L)return done;
   if(known.containsKey(pos(x,z))||!world.hasChunk(x,z))return done;
   refreshSurface(world,x,z);
   return done+1;
  }
  private static int b1843Near(ClientLevel world,
      LinkedHashMap<Long,int[]> known,int cx,int cz,long start,int done){
   // Center-out, not row-major; newly arrived local terrain appears first.
   for(int ring=0;ring<=2;ring++)
    for(int dz=-ring;dz<=ring;dz++)
     for(int dx=-ring;dx<=ring;dx++){
      if(Math.max(Math.abs(dx),Math.abs(dz))!=ring)continue;
      done=b1843TryLoaded(world,known,cx+dx,cz+dz,start,done);
      if(done>=8||System.nanoTime()-start>=2_000_000L)return done;
     }
   return done;
  }
  private static void b1843FillVisible(ClientLevel world,int viewCx,int viewCz,long start){
   var mc=Minecraft.getInstance();
   if(mc.player==null)return;
   var p=mc.player;
   int playerCx=p.blockPosition().getX()>>4;
   int playerCz=p.blockPosition().getZ()>>4;
   LinkedHashMap<Long,int[]> known=cache(world.dimension().identifier().toString());
   int done=b1843Near(world,known,playerCx,playerCz,start,0);
   // At high speed, favor already-loaded terrain *ahead* of the player.
   // Using actual motion rather than the face direction also handles strafing.
   double vx=p.getX()-p.xo,vz=p.getZ()-p.zo;
   double speed=Math.hypot(vx,vz);
   if(speed>0.75D&&done<8){
    int lead=Math.max(2,Math.min(7,(int)Math.ceil(speed*1.5D)));
    int aheadX=playerCx+(int)Math.round(vx/speed*lead);
    int aheadZ=playerCz+(int)Math.round(vz/speed*lead);
    done=b1843Near(world,known,aheadX,aheadZ,start,done);
   }
   // If a fullscreen map has been panned away, prioritize its center too.
   if((viewCx!=playerCx||viewCz!=playerCz)&&done<8)
    done=b1843Near(world,known,viewCx,viewCz,start,done);
   // Rotate over the FULL minimap crop, rather than only 5x5 / 13x13.
   // Large zoom-out modes can show up to ~39 chunk columns.
   int radius=Math.max(6,Math.min(20,
       (V178MiniPreferences.cropPixels()+31)/32+1));
   int side=radius*2+1,count=side*side;
   for(int n=0;n<64&&done<8;n++){
    if(System.nanoTime()-start>=2_000_000L)break;
    int index=Math.floorMod(b1843ExploreCursor++,count);
    int tx=playerCx+index%side-radius;
    int tz=playerCz+index/side-radius;
    done=b1843TryLoaded(world,known,tx,tz,start,done);
   }
  }
'''
s=s.replace(method,fastpath+method,1)
start=s.index(method)
stop=s.index("private static void refreshSurface(ClientLevel world,int cx,int cz){",start)
travel=s[start:stop]
needle="long start=System.nanoTime();"
assert travel.count(needle)==1,("B1843_TIME_BUDGET_ANCHOR",travel.count(needle))
travel=travel.replace(needle,needle+"\n   b1843FillVisible(world,cx,cz,start);",1)
s=s[:start]+travel+s[stop:]
assert "b1843FillVisible(world,cx,cz,start);" in s
assert "if(known.containsKey(pos(x,z))||!world.hasChunk(x,z))return done;" in s
assert "b1843Near(world,known,playerCx,playerCz,start,0)" in s
assert "Math.hypot(vx,vz)" in s
assert "V178MiniPreferences.cropPixels()" in s
assert "b1810WideCursor++%169" in s
assert "V178MiniRaster.tick(world);" in s
assert "updateAtlas(world,cx,cz);" in s
assert not any(word in fastpath for word in ("getChunk(", "getHeight(", "loadChunk(","requestChunk(", "forceChunk(","PacketDistributor"))
terrain.write_text(s,"utf-8")
print("B1843_V18_FAST_LOADED_CHUNK_TRAVEL_CENTER_FORWARD_CROP_BOUNDED_TICK_PASS")
