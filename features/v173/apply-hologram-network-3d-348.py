#!/usr/bin/env python3
"""Build348: true local 3D network topology for Hologram NETWORK mode.

Read-only loaded-client chunks; traverse only connected NETWORK cable lanes,
show attached importer/exporter models, keep text telemetry and height controls.
Runs after 328, 337/340, 338 and 345. No world, save or FE mutation.
"""
from pathlib import Path
import os

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
p=J/"client/V173WorldGhostRenderer.java"
s=p.read_text(encoding="utf-8")

old='''  if(!"map".equals(be.holoMode())){
   // B340_HOLO_SINGLE_OWNER: keep text visible until the server entity syncs.'''
new='''  if(!"map".equals(be.holoMode())){
   // V173_B348_NETWORK_3D: real connected models, not a text-only diagram.
   if("network".equals(be.holoMode()))networkProjection(mc,ev,cam,mapTerminal,be);
   // B340_HOLO_SINGLE_OWNER: keep text visible until the server entity syncs.'''
assert s.count(old)==1,("V173_B348_MODE_DRIFT",s.count(old))
s=s.replace(old,new,1)

anchor=" private static java.util.List<MapVoxel> sampleMap(Minecraft mc,BlockPos t,"
assert s.count(anchor)==1,("V173_B348_SAMPLER_DRIFT",s.count(anchor))
method=r''' // V173_B348_NETWORK_3D: real source block models, no HUD rectangles or
 // fake cable geometry, physical world edits, or forced chunk loads.
 private record NetworkNode(BlockPos pos,BlockState state){}
 private static net.minecraft.client.multiplayer.ClientLevel networkCacheWorld;
 private static BlockPos networkCacheTerminal;
 private static long networkCacheTick=Long.MIN_VALUE;
 private static java.util.List<NetworkNode> networkCache=java.util.List.of();
 private static boolean networkWire(Minecraft mc,BlockPos at){
  if(!mc.level.hasChunkAt(at))return false;
  BlockState state=mc.level.getBlockState(at);
  if(state.is(ObsidianNetwork.NETWORK_CABLE.get()))return true;
  if(!state.is(ObsidianNetwork.CONDUIT_BUNDLE.get()))return false;
  return mc.level.getBlockEntity(at) instanceof
       dev.obsidiannetwork.blockentity.ConduitBundleBlockEntity bundle
       &&bundle.has(dev.obsidiannetwork.blockentity.ConduitBundleBlockEntity.Layer.NETWORK);
 }
 private static boolean networkAttachment(Minecraft mc,BlockPos pos){
  if(!mc.level.hasChunkAt(pos))return false;
  BlockState state=mc.level.getBlockState(pos);
  String path=BuiltInRegistries.BLOCK.getKey(state.getBlock()).getPath();
  // Only actual network endpoint blocks. FE and other machinery are excluded.
  return path.equals("importer")||path.equals("exporter")||
    path.endsWith("_importer")||path.endsWith("_exporter")||
    path.equals("storage_drive")||path.equals("network_controller")||
    path.equals("storage_terminal")||path.equals("crafting_terminal");
 }
 private static boolean nearTerminal(BlockPos origin,BlockPos node){
  // Local loaded part of the network; never request arbitrary chunks.
  return Math.abs((long)node.getX()-origin.getX())<=16L
    &&Math.abs((long)node.getZ()-origin.getZ())<=16L
    &&Math.abs((long)node.getY()-origin.getY())<=12L;
 }
 private static java.util.List<NetworkNode> sampleNetwork(Minecraft mc,BlockPos terminal){
  java.util.ArrayList<NetworkNode> result=new java.util.ArrayList<>();
  java.util.ArrayDeque<BlockPos> frontier=new java.util.ArrayDeque<>();
  java.util.HashSet<BlockPos> seen=new java.util.HashSet<>();
  java.util.HashSet<BlockPos> drawn=new java.util.HashSet<>();
  // No radius scan of unrelated cables. Start at actual attached NETWORK wires.
  for(net.minecraft.core.Direction d:net.minecraft.core.Direction.values()){
   BlockPos first=terminal.relative(d);
   if(nearTerminal(terminal,first)&&networkWire(mc,first)&&seen.add(first))
    frontier.addLast(first);
  }
  while(!frontier.isEmpty()&&result.size()<256){
   BlockPos at=frontier.removeFirst();
   if(drawn.add(at))result.add(new NetworkNode(at,mc.level.getBlockState(at)));
   for(net.minecraft.core.Direction d:net.minecraft.core.Direction.values()){
    BlockPos next=at.relative(d);
    if(!nearTerminal(terminal,next)||!mc.level.hasChunkAt(next))continue;
    if(networkWire(mc,next)){
     if(seen.size()<512&&seen.add(next))frontier.addLast(next);
    }else if(networkAttachment(mc,next)&&drawn.add(next)&&result.size()<256){
     result.add(new NetworkNode(next,mc.level.getBlockState(next)));
    }
   }
  }
  return result;
 }
 private static void networkProjection(Minecraft mc,SubmitCustomGeometryEvent ev,
       Vec3 camera,BlockPos origin,NetworkDeviceBlockEntity be){
  long tick=mc.level.getGameTime();
  if(networkCacheWorld!=mc.level||!origin.equals(networkCacheTerminal)||
     networkCacheTick==Long.MIN_VALUE||tick<networkCacheTick||
     tick-networkCacheTick>=10L){
   networkCacheWorld=mc.level;networkCacheTerminal=origin;
   networkCacheTick=tick;networkCache=sampleNetwork(mc,origin);
  }
  if(networkCache.isEmpty())return; // authoritative status text says OFFLINE.
  int minX=Integer.MAX_VALUE,minY=Integer.MAX_VALUE,minZ=Integer.MAX_VALUE;
  int maxX=Integer.MIN_VALUE,maxY=Integer.MIN_VALUE,maxZ=Integer.MIN_VALUE;
  for(NetworkNode node:networkCache){
   var at=node.pos();
   minX=Math.min(minX,at.getX());minY=Math.min(minY,at.getY());
   minZ=Math.min(minZ,at.getZ());
   maxX=Math.max(maxX,at.getX());maxY=Math.max(maxY,at.getY());
   maxZ=Math.max(maxZ,at.getZ());
  }
  double dx=maxX-minX+1D,dy=maxY-minY+1D,dz=maxZ-minZ+1D;
  double scale=Math.max(.045D,Math.min(1D,be.holoWidth()/Math.max(dx,Math.max(dy,dz))));
  double centerX=(minX+maxX+1D)/2D,centerZ=(minZ+maxZ+1D)/2D;
  // HEIGHT is a downward translation: 1 means directly BELOW the table.
  double topY=origin.getY()-be.holoHeight()+1D;
  double baseX=origin.getX()+.5D,baseZ=origin.getZ()+.5D;
  for(NetworkNode node:networkCache){
   BlockState real=node.state();
   // Facade is visual only. Sample and submit the bare cable blockstate.
   var property=real.getBlock().getStateDefinition().getProperty("facaded");
   if(property instanceof net.minecraft.world.level.block.state.properties.BooleanProperty flag)
    real=real.setValue(flag,false);
   BlockPos at=node.pos();
   double x=baseX+(at.getX()-centerX)*scale;
   double y=topY-(maxY+1D-at.getY())*scale;
   double z=baseZ+(at.getZ()-centerZ)*scale;
   drawSized(mc,ev,camera,real,x,y,z,scale,scale,scale);
  }
 }
'''
s=s.replace(anchor,method+anchor,1)
p.write_text(s,encoding="utf-8")
assert "V173_B348_NETWORK_3D" in p.read_text(encoding="utf-8")
print("V173_B348_NETWORK_CONNECTED_3D_HOLOGRAM_PASS")
