#!/usr/bin/env python3
"""v1.7.3 Build414: fast wireless miss + single-pass wire scan on terminal I/O.

Never changes storage mutation, JEI, menus or portal state. The bounded BFS
is still used when a paired receiver and a live transmitter could be reached.
"""
import os
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
be=J/"blockentity/NetworkSignalRelayBlockEntity.java"
bridge=J/"network/NetworkSignalRelayBridge.java"
def one(s,old,new,file):
    count=s.count(old)
    assert count==1,(file,"source drift",count,old[:140])
    return s.replace(old,new,1)

s=be.read_text(encoding="utf-8")
assert "V173_WIRELESS_CONNECTED_VISUAL" in s
s=one(s,
 ''' private static final java.util.Map<net.minecraft.server.MinecraftServer,java.util.Set<NetworkSignalRelayBlockEntity>> LIVE=
   java.util.Collections.synchronizedMap(new java.util.WeakHashMap<>());''',
 ''' private static final java.util.Map<net.minecraft.server.MinecraftServer,java.util.Set<NetworkSignalRelayBlockEntity>> LIVE=
   java.util.Collections.synchronizedMap(new java.util.WeakHashMap<>());
 // B414_WIRELESS_RX_FAST_REJECT: live, paired receivers indexed per level.
 // A terminal cannot reach a receiver in an unloaded chunk or another level.
 private static final java.util.Map<ServerLevel,java.util.Set<NetworkSignalRelayBlockEntity>> LIVE_RX=
   java.util.Collections.synchronizedMap(new java.util.WeakHashMap<>());
 private static void trackReceiver(ServerLevel world,NetworkSignalRelayBlockEntity receiver){
  LIVE_RX.computeIfAbsent(world,ignored->java.util.Collections.newSetFromMap(
      new java.util.IdentityHashMap<>())).add(receiver);
 }
 /** Constant-time miss for worlds without live receivers. Conservative 514-block
  * Manhattan radius: a 512-node cable walk cannot encounter a farther receiver.
  * No FE lookup, no chunk loads, no storage snapshots. */
 public static boolean mayReachReceiver(ServerLevel world,BlockPos queried){
  var tx=LIVE.get(world.getServer());
  if(tx==null||tx.isEmpty())return false;
  var receivers=LIVE_RX.get(world);
  if(receivers==null||receivers.isEmpty())return false;
  for(var rx:receivers){
   if(rx.isRemoved()||!rx.paired()||rx.transmitter()||rx.getLevel()!=world)continue;
   BlockPos at=rx.getBlockPos();
   int dx=Math.abs(at.getX()-queried.getX());
   if(dx>514)continue;
   int dy=Math.abs(at.getY()-queried.getY());
   if(dx+dy>514)continue;
   int dz=Math.abs(at.getZ()-queried.getZ());
   if(dx+dy+dz<=514)return true;
  }
  return false;
 }''',"receiver registry")
s=one(s,
 '''  channel=key;owner=user;setChanged();
  player.sendSystemMessage(Component.literal("Signal Receiver paired | "+connectionStatus(world)+''',
 '''  channel=key;owner=user;setChanged();
  // Register immediately: pairing must work before the next world tick.
  trackReceiver(world,this);
  player.sendSystemMessage(Component.literal("Signal Receiver paired | "+connectionStatus(world)+''',"receiver interact")
s=one(s,
 '''  if(l instanceof ServerLevel sl && be.transmitter() && be.paired())
   LIVE.computeIfAbsent(sl.getServer(),ignored->java.util.Collections.newSetFromMap(
      new java.util.IdentityHashMap<>())).add(be);
  // V173_WIRELESS_CONNECTED_VISUAL''',
 '''  if(l instanceof ServerLevel sl && be.paired()){
   if(be.transmitter())
    LIVE.computeIfAbsent(sl.getServer(),ignored->java.util.Collections.newSetFromMap(
       new java.util.IdentityHashMap<>())).add(be);
   else trackReceiver(sl,be);
  }
  // V173_WIRELESS_CONNECTED_VISUAL''',"receiver ticker")
s=one(s,
 '''  if(level instanceof ServerLevel sl){
   var set=LIVE.get(sl.getServer());if(set!=null)set.remove(this);
  }
  super.setRemoved();''',
 '''  if(level instanceof ServerLevel sl){
   var set=LIVE.get(sl.getServer());if(set!=null)set.remove(this);
   var receivers=LIVE_RX.get(sl);if(receivers!=null)receivers.remove(this);
  }
  super.setRemoved();''',"receiver unload")
be.write_text(s,encoding="utf-8")

s=bridge.read_text(encoding="utf-8")
assert "B409_TERMINAL_BFS_TICK_CACHE" in s
assert "V173_WIRELESS_CABLE_ENTRY_GUARD" in s
s=one(s,
 ''' private static final ThreadLocal<Boolean> RESOLVING=ThreadLocal.withInitial(()->false);''',
 ''' private static final ThreadLocal<Boolean> RESOLVING=ThreadLocal.withInitial(()->false);
 private static final Direction[] FACES=Direction.values();''',"direction allocation")
s=one(s,
 ''' public static boolean networkWire(ServerLevel level,BlockPos at){
  if(!level.hasChunkAt(at))return false;
  var state=level.getBlockState(at);
  if(state.is(ObsidianNetwork.NETWORK_CABLE.get()))return true;
  if(state.is(ObsidianNetwork.CONDUIT_BUNDLE.get())
      &&level.getBlockEntity(at) instanceof dev.obsidiannetwork.blockentity.ConduitBundleBlockEntity bundle)
   return bundle.has(dev.obsidiannetwork.blockentity.ConduitBundleBlockEntity.Layer.NETWORK);
  return false;
 }''',
 ''' public static boolean networkWire(ServerLevel level,BlockPos at){
  if(!level.hasChunkAt(at))return false;
  return networkWireLoaded(level,at,level.getBlockState(at));
 }
 // B414_SINGLE_BLOCKSTATE_SCAN: caller already checked the chunk and loaded
 // the state. A second hasChunkAt/getBlockState in the BFS was redundant.
 private static boolean networkWireLoaded(ServerLevel level,BlockPos at,BlockState state){
  if(state.is(ObsidianNetwork.NETWORK_CABLE.get()))return true;
  if(state.is(ObsidianNetwork.CONDUIT_BUNDLE.get())
      &&level.getBlockEntity(at) instanceof dev.obsidiannetwork.blockentity.ConduitBundleBlockEntity bundle)
   return bundle.has(dev.obsidiannetwork.blockentity.ConduitBundleBlockEntity.Layer.NETWORK);
  return false;
 }''',"networkWire")
s=one(s,
 '''  if(RESOLVING.get()||queried==null)return null;
  TickLookups lookups=LOOKUPS.computeIfAbsent(level,unused->new TickLookups());''',
 '''  if(RESOLVING.get()||queried==null)return null;
  // B414_WIRELESS_RX_FAST_REJECT: no available TX/RX in this level or
  // within physical BFS range = return local topology immediately.
  if(!dev.obsidiannetwork.blockentity.NetworkSignalRelayBlockEntity
         .mayReachReceiver(level,queried))return null;
  TickLookups lookups=LOOKUPS.computeIfAbsent(level,unused->new TickLookups());''',"no receiver gate")
s=one(s,
 '''    if(!seen.add(at)||!level.hasChunkAt(at))continue;
    if(!networkWire(level,at)&&!at.equals(queried))continue;
    for(Direction face:Direction.values()){''',
 '''    // Every enqueued position was already verified as a loaded NETWORK
    // conductor. A single server-thread call cannot unload/replace it here.
    if(!seen.add(at))continue;
    for(Direction face:FACES){''',"BFS current wire double lookup")
s=one(s,
 '''     if(networkWire(level,neighbor)&&!seen.contains(neighbor))
      queue.addLast(neighbor);''',
 '''     if(!seen.contains(neighbor)&&networkWireLoaded(level,neighbor,state))
      queue.addLast(neighbor);''',"BFS neighbor double lookup")
# Initial seeding uses six unchanged physical wire checks.
s=one(s,
 '''   else for(Direction entry:Direction.values()){''',
 '''   else for(Direction entry:FACES){''',"BFS seeding")
assert s.count("B414_WIRELESS_RX_FAST_REJECT")==1
assert s.count("B414_SINGLE_BLOCKSTATE_SCAN")==1
assert "Layer.ENERGY" not in s
bridge.write_text(s,encoding="utf-8")

# No fast path may bypass powered-state checks or alter server transfers.
assert "if(rt!=null&&rt.powered())" in s
assert "known!=null&&known.powered()" in s
menu=(J/"menu/StorageTerminalMenu.java").read_text()
jei=(J/"compat/jei/NetworkStorageRecipeTransferHandler.java").read_text()
assert "B368_PARTIAL_INGREDIENTS" in menu
assert "B404_JEI_COSMETIC_MISSING" in jei and "Type.COSMETIC" in jei
portal=(J/"portal/PortalGateBlock.java").read_text()
assert "B409_PORTAL_FOUR_DIRECTIONS" in portal
print("B414_FAST_WIRELESS_MISS_SINGLE_SCAN_JEI_PORTAL_PRESERVED_PASS")
