#!/usr/bin/env python3
"""Build209: wireless-network powered visuals for devices behind real NETWORK conductors."""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
p=J/"blockentity/NetworkSignalRelayBlockEntity.java"
s=p.read_text(encoding="utf-8")
old='''  if(l instanceof ServerLevel sl && be.transmitter() && be.paired())
   LIVE.computeIfAbsent(sl.getServer(),ignored->java.util.Collections.newSetFromMap(
      new java.util.IdentityHashMap<>())).add(be);'''
new='''  if(l instanceof ServerLevel sl && be.transmitter() && be.paired())
   LIVE.computeIfAbsent(sl.getServer(),ignored->java.util.Collections.newSetFromMap(
      new java.util.IdentityHashMap<>())).add(be);
  // V173_WIRELESS_CONNECTED_VISUAL: same machine CONNECTED property as cables.
  if(l instanceof ServerLevel sl && !be.transmitter() && sl.getGameTime()%20L==0L)
   refreshWirelessVisuals(sl,p);'''
assert s.count(old)==1,(s.count(old),old[:90])
s=s.replace(old,new,1)
mark=''' @Override public void setRemoved(){'''
insert=r''' private static void refreshWirelessVisuals(ServerLevel world,BlockPos source){
  // Only loaded, physically connected NETWORK conductors participate.
  // Never bridge FE, never add tickets; finite 256-position traversal.
  java.util.ArrayDeque<BlockPos> pending=new java.util.ArrayDeque<>();
  java.util.Set<BlockPos> seen=new java.util.HashSet<>();
  for(Direction d:Direction.values()){
   BlockPos at=source.relative(d);
   if(dev.obsidiannetwork.network.NetworkSignalRelayBridge.networkWire(world,at))
    pending.addLast(at);
  }
  while(!pending.isEmpty()&&seen.size()<256){
   BlockPos cable=pending.removeFirst();
   if(!seen.add(cable)||!world.hasChunkAt(cable)||
      !dev.obsidiannetwork.network.NetworkSignalRelayBridge.networkWire(world,cable))continue;
   for(Direction d:Direction.values()){
    BlockPos at=cable.relative(d);
    if(!world.hasChunkAt(at))continue;
    if(dev.obsidiannetwork.network.NetworkSignalRelayBridge.networkWire(world,at)){
     if(!seen.contains(at))pending.addLast(at);
     continue;
    }
    BlockState block=world.getBlockState(at);
    if(!block.hasProperty(dev.obsidiannetwork.block.HorizontalMachineBlock.CONNECTED))continue;
    var rt=dev.obsidiannetwork.network.WorldTopologyBridge.runtimeForAccessory(world,at);
    boolean active=rt!=null&&rt.powered();
    if(block.getValue(dev.obsidiannetwork.block.HorizontalMachineBlock.CONNECTED)!=active)
     world.setBlock(at,block.setValue(dev.obsidiannetwork.block.HorizontalMachineBlock.CONNECTED,active),2);
   }
  }
 }
'''
assert s.count(mark)==1
s=s.replace(mark,insert+mark,1)
p.write_text(s,encoding="utf-8")
print("V173_WIRELESS_MACHINE_CONNECTED_LIGHT_BUILD209_PASS")
