#!/usr/bin/env python3
"""B581: bounded NeoForge capability caching on 20Hz reactor output, and
deduplicated/allocated-once cable wireframes in the client Vision overlay.

No change to FE budget, extraction/insertion, transactions, rod insertion,
port routing eligibility, Vision radius/colors/through-walls visibility.
"""
import os
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def update(rel,old,new,n=1):
 p=J/rel;s=p.read_text(encoding="utf-8")
 assert s.count(old)==n,("B581_SOURCE_DRIFT",rel,old[:140],s.count(old))
 s=s.replace(old,new,n);p.write_text(s,encoding="utf-8")

# NeoForge's BlockCapabilityCache invalidates when target caps change;
# controller still validates approved live ports, chunk state, and transactions
# every single tick. Cache is lazy, bounded to 256 ports, and world scoped.
react="reactor/ReactorControllerBlockEntity.java"
anchor=" // B497_REACTOR_PORT_PUSH: PORT drives FE every 5 ticks, not just a passive"
# The original comment remains (from B497) though the caller is now 20Hz.
# Inject immediately before pushToPowerPort rather than changing any FE math.
p=J/react;s=p.read_text(encoding="utf-8")
push=" private void pushToPowerPort(ServerLevel world){"
assert s.count(push)==1,("B581_REACTOR_PUSH_SIGNATURE",s.count(push))
cache=''' // B581_REACTOR_CACHE: avoid repeated expensive capability resolution
 // on each of the existing 20 per-second reactor export operations.
 private static final net.minecraft.core.Direction[] b581Directions=
   net.minecraft.core.Direction.values();
 @SuppressWarnings("unchecked")
 private final java.util.Map<Long,
   net.neoforged.neoforge.capabilities.BlockCapabilityCache<
    net.neoforged.neoforge.transfer.energy.EnergyHandler,net.minecraft.core.Direction>[]>
      b581PortCapabilities=new java.util.HashMap<>();
 private ServerLevel b581PortCacheWorld;
 @SuppressWarnings("unchecked")
 private net.neoforged.neoforge.transfer.energy.EnergyHandler b581CachedSink(
   ServerLevel world,BlockPos port,BlockPos next,net.minecraft.core.Direction direction){
  if(b581PortCacheWorld!=world){
   b581PortCapabilities.clear();b581PortCacheWorld=world;
  }
  long key=port.asLong();
  var ports=b581PortCapabilities.get(key);
  if(ports==null){
   // Unbounded multiblocks may have many ports; retain at most 256 owners.
   // When full use the original live resolution, never decline a transfer.
   if(b581PortCapabilities.size()>=256)
    return world.getCapability(
     net.neoforged.neoforge.capabilities.Capabilities.Energy.BLOCK,
     next,direction.getOpposite());
   ports=(net.neoforged.neoforge.capabilities.BlockCapabilityCache<
     net.neoforged.neoforge.transfer.energy.EnergyHandler,net.minecraft.core.Direction>[])
     new net.neoforged.neoforge.capabilities.BlockCapabilityCache[6];
   b581PortCapabilities.put(key,ports);
  }
  int index=direction.get3DDataValue();
  var cached=ports[index];
  if(cached==null){
   cached=net.neoforged.neoforge.capabilities.BlockCapabilityCache.create(
    net.neoforged.neoforge.capabilities.Capabilities.Energy.BLOCK,
    world,next,direction.getOpposite(),
    ()->!isRemoved()&&level==world,()->{});
   ports[index]=cached;
  }
  return cached.getCapability();
 }
'''
s=s.replace(push,cache+push,1)
start=s.index(push)
opening=s.index("{",start)
depth=0
end=None
for i in range(opening,len(s)):
 if s[i]=="{":depth+=1
 elif s[i]=="}":
  depth-=1
  if depth==0:
   end=i+1
   break
assert end is not None, "B581_REACTOR_METHOD_BOUNDARY"
region=s[start:end]
old='for(net.minecraft.core.Direction dir:net.minecraft.core.Direction.values()){'
assert region.count(old)==1,("B581_DIRECTION_LOOP",region.count(old))
region=region.replace(old,"for(net.minecraft.core.Direction dir:b581Directions){",1)
old='''var sink=world.getCapability(
      net.neoforged.neoforge.capabilities.Capabilities.Energy.BLOCK,
      next,dir.getOpposite());'''
assert region.count(old)==1,("B581_REACTOR_SINK_LOOKUP",region.count(old))
region=region.replace(old,"var sink=b581CachedSink(world,at,next,dir);",1)
assert "energyPort.extract(accepted,tx)==accepted" in region
assert "tx.commit();" in region
assert "int budget=(int)Math.min(262144L,storedFe);" in region
s=s[:start]+region+s[end:]
p.write_text(s,encoding="utf-8")

# Network Vision previously projected and rasterized the shared center face of
# each connected arm twice. Project the 8 core vertices ONCE and 4 external
# vertices per real arm, draw 12 core edges plus 8 per arm (same unique edges).
# Client only: no level access, no extra network data, no server ticking.
vis="client/NetworkVisionClient.java"
p=J/vis;s=p.read_text(encoding="utf-8")
start=s.index(" // B514_VISION_CABLE_GEOMETRY: pipe core + six connected 3D arms.")
end=s.index(" // V174_XRAY_WORLD_WIREFRAME_B469: show",start)
replacement=r''' // B514_VISION_CABLE_GEOMETRY: same pipe shape through solid blocks.
 // B581_VISION_SHARED_VERTICES: remove duplicate arm faces, 84 -> 60
 // edge submissions and 56 -> 32 projections for a six-connected cable.
 private static final net.minecraft.core.Direction[] b581VisionDirections=
   net.minecraft.core.Direction.values();
 private static void pipeAt(net.minecraft.client.gui.GuiGraphicsExtractor g,
   BlockPos pos,net.minecraft.world.level.block.state.BlockState state,int color,
   net.minecraft.world.phys.Vec3 eye,Quaternionf inverse,double focal,int width,int height){
  float x=pos.getX(),y=pos.getY(),z=pos.getZ();
  float[][] core=new float[8][];
  for(int i=0;i<8;i++)
   core[i]=project(x+((i&1)==0?.375f:.625f),
      y+((i&2)==0?.375f:.625f),z+((i&4)==0?.375f:.625f),
      eye,inverse,focal,width,height);
  for(int i=0;i<8;i++)for(int bit=1;bit<=4;bit*=2){
   int other=i^bit;
   if(i<other)wireLine(g,core[i],core[other],color,width,height);
  }
  // Reuse four index slots and projected corners across arms in this frame.
  int[] near=new int[4];float[][] far=new float[4][];
  for(var dir:b581VisionDirections){
   if((b579VisionMasks.getOrDefault(pos,0)&(1<<dir.get3DDataValue()))==0)continue;
   int axis=switch(dir){
     case WEST,EAST->1;case DOWN,UP->2;case NORTH,SOUTH->4;
   };
   int bit=switch(dir){
     case EAST,UP,SOUTH->axis;default->0;
   };
   int count=0;
   for(int i=0;i<8;i++){
    if((i&axis)!=bit)continue;
    near[count]=i;
    float xx=x+((i&1)==0?.375f:.625f);
    float yy=y+((i&2)==0?.375f:.625f);
    float zz=z+((i&4)==0?.375f:.625f);
    if(axis==1)xx=x+(bit==0?0f:1f);
    else if(axis==2)yy=y+(bit==0?0f:1f);
    else zz=z+(bit==0?0f:1f);
    far[count]=project(xx,yy,zz,eye,inverse,focal,width,height);
    count++;
   }
   // Outer end ring and four longitudinal rails; central ring exists in core.
   for(int i=0;i<4;i++){
    wireLine(g,core[near[i]],far[i],color,width,height);
    for(int j=i+1;j<4;j++){
     if(Integer.bitCount(near[i]^near[j])==1)
      wireLine(g,far[i],far[j],color,width,height);
    }
   }
  }
 }
'''
s=s[:start]+replacement+s[end:]
assert "wirePipe(" not in s,("B581_DANGLING_OLD_RENDERER",s.count("wirePipe("))
assert "b579VisionMasks.getOrDefault(pos,0)" in s
assert "xrayPositions.size()>=160" in s
p.write_text(s,encoding="utf-8")
print("B581_20HZ_REACTOR_BOUNDED_CAP_CACHE_VISION_SAME_CABLE_EDGES_HALF_PROJECTIONS_PASS")
