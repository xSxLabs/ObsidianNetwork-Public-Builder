#!/usr/bin/env python3
"""v22: bounded, center-out minimap prefetch well beyond the current crop."""
import os
from pathlib import Path

p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/client/V178TerrainMap.java"
s=p.read_text("utf-8")

def once(old,new):
    global s
    assert s.count(old)==1,("V22_PREFETCH_SOURCE_DRIFT",old[:120],s.count(old))
    s=s.replace(old,new,1)

# Larger live surface cache: a full 65x65 loaded neighborhood fits.
once("MAX_CACHED=1536","MAX_CACHED=8192")
# Keep the old local refresh and worldmap logic. Only replace the missing-tile scheduler.
a=s.index("  private static int b1843ExploreCursor;")
b=s.index("private static void b1802RefreshTravel(ClientLevel world,int cx,int cz){",a)
old=s[a:b]
assert "known.containsKey(pos(x,z))||!world.hasChunk(x,z)" in old
assert "n<64&&done<8" in old
new=r'''  // V22: live prefetch uses independent center-out cursors for the visible
  // crop and the much wider travel buffer. Client-thread world reads only.
  private static final int V22_MAX_RADIUS=80,V22_MIN_RADIUS=32;
  private static final int V22_MAX_SAMPLES=12,V22_VISIBLE_PROBES=256,V22_WIDE_PROBES=1024;
  private static final long V22_BUDGET_NS=2_000_000L;
  private static int v22VisibleCursor,v22WideCursor,v22LastX,v22LastZ;
  private static int v22LastVisible=-1,v22LastWide=-1;
  private static ClientLevel v22LastWorld;
  private static boolean v22Budget(long start,int done){
   return done<V22_MAX_SAMPLES&&System.nanoTime()-start<V22_BUDGET_NS;
  }
  // Index 0 is the center; each subsequent square ring contains 8*r cells.
  private static long v22Offset(int index){
   if(index==0)return 0L;
   int r=(int)((Math.sqrt(index)+1.0D)/2.0D);
   int side=2*r,inner=side-1;
   int k=index-inner*inner;
   int dx,dz;
   if(k<side){dx=-r+k;dz=-r;}
   else if(k<2*side){dx=r;dz=-r+k-side;}
   else if(k<3*side){dx=r-(k-2*side);dz=r;}
   else{dx=-r;dz=r-(k-3*side);}
   return ((long)dx<<32)|(dz&0xffffffffL);
  }
  private static int b1843TryLoaded(ClientLevel world,
      LinkedHashMap<Long,int[]> known,int x,int z,long start,int done){
   if(!v22Budget(start,done))return done;
   if(known.containsKey(pos(x,z))||!world.hasChunk(x,z))return done;
   refreshSurface(world,x,z);
   return done+1;
  }
  private static int b1843Near(ClientLevel world,
      LinkedHashMap<Long,int[]> known,int cx,int cz,long start,int done){
   for(int i=0;i<25&&v22Budget(start,done);i++){
    long offset=v22Offset(i);
    done=b1843TryLoaded(world,known,cx+(int)(offset>>32),cz+(int)offset,start,done);
   }
   return done;
  }
  private static void b1843FillVisible(ClientLevel world,int viewCx,int viewCz,long start){
   var mc=Minecraft.getInstance();
   if(mc.player==null)return;
   var p=mc.player;
   int playerCx=p.blockPosition().getX()>>4;
   int playerCz=p.blockPosition().getZ()>>4;
   int visible=Math.max(2,Math.min(20,(V178MiniPreferences.cropPixels()+31)/32+1));
   int wide=Math.min(V22_MAX_RADIUS,Math.max(V22_MIN_RADIUS,visible*4));
   int visibleCount=(2*visible+1)*(2*visible+1);
   int wideCount=(2*wide+1)*(2*wide+1);
   // Reset after entering a world, changing zoom, or teleporting. Ordinary
   // movement must NOT reset the wide scan or it never reaches distant rings.
   boolean reset=v22LastWorld!=world||Math.abs((long)playerCx-v22LastX)>wide
       ||Math.abs((long)playerCz-v22LastZ)>wide;
   if(reset||visible!=v22LastVisible)v22VisibleCursor=0;
   if(reset||wide!=v22LastWide)v22WideCursor=0;
   v22LastWorld=world;v22LastX=playerCx;v22LastZ=playerCz;
   v22LastVisible=visible;v22LastWide=wide;
   LinkedHashMap<Long,int[]> known=cache(world.dimension().identifier().toString());
   int done=b1843Near(world,known,playerCx,playerCz,start,0);
   double vx=p.getX()-p.xo,vz=p.getZ()-p.zo;
   double speed=Math.hypot(vx,vz);
   if(speed>0.75D&&v22Budget(start,done)){
    int lead=Math.max(3,Math.min(16,(int)Math.ceil(speed*2.5D)));
    int aheadX=playerCx+(int)Math.round(vx/speed*lead);
    int aheadZ=playerCz+(int)Math.round(vz/speed*lead);
    done=b1843Near(world,known,aheadX,aheadZ,start,done);
   }
   if((viewCx!=playerCx||viewCz!=playerCz)&&v22Budget(start,done))
    done=b1843Near(world,known,viewCx,viewCz,start,done);
   // Visible holes first, then preload the surrounding rings, all loaded-only.
   for(int n=0;n<V22_VISIBLE_PROBES&&v22Budget(start,done);n++){
    int i=v22VisibleCursor;
    v22VisibleCursor=(i+1)%visibleCount;
    long offset=v22Offset(i);
    done=b1843TryLoaded(world,known,playerCx+(int)(offset>>32),
         playerCz+(int)offset,start,done);
   }
   for(int n=0;n<V22_WIDE_PROBES&&v22Budget(start,done);n++){
    int i=v22WideCursor;
    v22WideCursor=(i+1)%wideCount;
    long offset=v22Offset(i);
    done=b1843TryLoaded(world,known,playerCx+(int)(offset>>32),
         playerCz+(int)offset,start,done);
   }
  }
 '''
s=s[:a]+new+s[b:]
assert "b1843FillVisible(world,cx,cz,start);" in s
assert "V178MiniRaster.tick(world);" in s
assert "world.hasChunk(cx,cz)?null:archiveLookup(cx,cz)" in s
assert "b1810WideCursor++%169" in s
assert "world.getChunk(" not in new and "forceChunk(" not in new
p.write_text(s,"utf-8")
print("V22_WIDE_CENTER_OUT_LOADED_ONLY_PREFETCH_PASS")
