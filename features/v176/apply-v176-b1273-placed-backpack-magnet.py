#!/usr/bin/env python3
"""B1273: placed Network Backpack magnet, server-tick, exact 8-block radius.

The old magnet only uses PlayerTickEvent + equipped/held backpack lookup.
Give the real placed BlockEntity a server-only ticker. It collects already
dropped items directly into the SAME original backpack's real Storage Cells
using a single CAS persist per batch. No inventories, items or blocks are
mutated until exact accepted counts have been prepared. No global registry or
chunk-leaking static list; unloaded blocks stop ticking automatically.

Avoid expensive scans for unupgraded/full bags by caching the immutable
CONTAINER identity and the native cable capacity/used view. Never assume the
old cached state survives item changes, cell swap or cable rollback.
The no-pickup-delay behavior matches the existing B1270 handheld magnet.
"""
import os
from pathlib import Path

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
block=root/"backpack/NetworkBackpackBlock.java"
be=root/"backpack/NetworkBackpackBlockEntity.java"
helper=root/"backpack/V176BackpackPlacedMagnet.java"
block_src=block.read_text("utf-8")
be_src=be.read_text("utf-8")
assert not helper.exists(),("B1273_ALREADY_GENERATED",str(helper))

def once(source,old,new,label):
    assert source.count(old)==1,("B1273_PLACED_MAGNET_DRIFT",label,source.count(old))
    return source.replace(old,new,1)

block_src=once(block_src,
''' @Nullable @Override public BlockEntity newBlockEntity(BlockPos p,BlockState s){
  return new NetworkBackpackBlockEntity(p,s);
 }''',
''' @Nullable @Override public BlockEntity newBlockEntity(BlockPos p,BlockState s){
  return new NetworkBackpackBlockEntity(p,s);
 }
 // A placed backpack has no player inventory slot and was never considered
 // by PlayerTickEvent. Server-only BE ticking avoids global entity scans.
 @Nullable @Override public <T extends BlockEntity>
     net.minecraft.world.level.block.entity.BlockEntityTicker<T> getTicker(
         Level world,BlockState state,
         net.minecraft.world.level.block.entity.BlockEntityType<T> type){
  return world.isClientSide()?null:createTickerHelper(
      type,dev.obsidiannetwork.registry.ModBlockEntities.NETWORK_BACKPACK.get(),
      V176BackpackPlacedMagnet::tick);
 }''',"block ticker registration")
be_src=once(be_src,
''' public ItemStack getBackpack(){return backpack;}''',
''' // A live magnet with a valid real Cell is the ONLY placed BE which may
 // search world drops; stable immutable contents cost O(1) per server tick.
 private ItemStack xsxPlacedMagnetOwner=null;
 private net.minecraft.world.item.component.ItemContainerContents xsxPlacedMagnetContainer=null;
 private boolean xsxPlacedMagnetEnabled=false;
 public boolean xsxPlacedMagnetActive(){
  if(level==null||level.isClientSide()||backpack.isEmpty())return false;
  var content=backpack.get(net.minecraft.core.component.DataComponents.CONTAINER);
  if(xsxPlacedMagnetOwner!=backpack||xsxPlacedMagnetContainer!=content){
   xsxPlacedMagnetEnabled=V176BackpackCells.magnetEnabled(backpack)
       &&V176BackpackCells.capacity(backpack)>0L;
   xsxPlacedMagnetOwner=backpack;
   xsxPlacedMagnetContainer=content;
  }
  if(!xsxPlacedMagnetEnabled)return false;
  // This cached cable view updates with exact committed insertion/extraction
  // and detects a changed immutable cell container or rolled-back ItemStack.
  xsxRefreshCableView();
  return xsxCableUsed<xsxCableCapacity;
 }
 public ItemStack getBackpack(){return backpack;}''',"O(1) no-magnet/full-bag gate")

java='''package dev.obsidiannetwork.backpack;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.neoforged.neoforge.transfer.item.ItemResource;
import java.util.ArrayList;
import java.util.LinkedHashMap;

/** A placed backpack collects as soon as drops exist, without a player.
 * One real BE remains the only owner. Do not register static per-world sets.
 */
public final class V176BackpackPlacedMagnet {
 private V176BackpackPlacedMagnet(){}
 private static final double RANGE=8.0D;
 private static final double RANGE_SQUARED=RANGE*RANGE;
 private static final class Group {
  final ItemStack sample;
  final ArrayList<ItemEntity> entities=new ArrayList<>();
  long requested=0L;
  long accepted=0L;
  Group(ItemStack stack){sample=stack.copy();}
 }
 private record Pickup(ItemEntity entity,int amount){}
 /** Called only from the original NetworkBackpackBlock server ticker. */
 public static void tick(Level world,BlockPos pos,BlockState state,
                         NetworkBackpackBlockEntity bag){
  if(!(world instanceof ServerLevel server)||!bag.xsxPlacedMagnetActive())
   return;
  final double cx=pos.getX()+0.5D,cy=pos.getY()+0.5D,cz=pos.getZ()+0.5D;
  var drops=server.getEntitiesOfClass(ItemEntity.class,
      new AABB(pos).inflate(RANGE),entity->entity.isAlive()
          &&!entity.getItem().isEmpty()
          &&entity.distanceToSqr(cx,cy,cz)<=RANGE_SQUARED);
  if(drops.isEmpty())return;
  ItemStack original=bag.getBackpack();
  if(original.isEmpty()||!V176BackpackCells.magnetEnabled(original))return;
  var groups=new LinkedHashMap<ItemResource,Group>();
  for(ItemEntity drop:drops){
   var item=drop.getItem();
   if(item.isEmpty())continue;
   var resource=ItemResource.of(item);
   if(resource.isEmpty())continue;
   Group group=groups.get(resource);
   if(group==null){
    group=new Group(item);
    groups.put(resource,group);
   }
   group.entities.add(drop);
   group.requested=Math.addExact(group.requested,(long)item.getCount());
  }
  if(groups.isEmpty())return;

  ItemStack next=original.copy();
  for(Group group:groups.values()){
   if(!V176BackpackCells.magnetAccepts(server,next,group.sample))continue;
   try{
    ItemStack candidate=next.copy();
    // The original native Cell routing and Equipment Cell restrictions apply.
    var transferred=V176BackpackCells.insert(
        server,candidate,group.sample,group.requested);
    if(transferred.accepted()<=0)continue;
    group.accepted=transferred.accepted();
    next=candidate;
   }catch(RuntimeException rejected){
    group.accepted=0L;
   }
  }

  var picked=new ArrayList<Pickup>();
  for(Group group:groups.values()){
   long left=group.accepted;
   for(ItemEntity drop:group.entities){
    if(left<=0L)break;
    int count=(int)Math.min(left,(long)drop.getItem().getCount());
    if(count<=0)continue;
    picked.add(new Pickup(drop,count));
    left-=count;
   }
   if(left!=0L)return; // No split that could lose unaccounted items.
  }
  if(picked.isEmpty())return;
  // Persist the complete populated original backpack once. A concurrent
  // player GUI/cable change rejects the expected snapshot, leaving ALL drops.
  if(!bag.replaceBackpack(original,next))return;
  // Only AFTER a successful BE write, shrink each accepted world stack.
  for(Pickup pickup:picked){
   ItemEntity drop=pickup.entity();
   ItemStack remainder=drop.getItem().copy();
   remainder.shrink(pickup.amount());
   if(remainder.isEmpty())drop.discard();
   else drop.setItem(remainder);
  }
 }
}
'''
assert "xsxCableCommitRevision" in be_src
assert "xsxRefreshCableView();" in be_src
assert "V176BackpackCells.magnetEnabled" in be_src
assert "V176BackpackPlacedMagnet::tick" in block_src
assert "bag.replaceBackpack(original,next)" in java
assert java.index("bag.replaceBackpack(original,next)")<java.index("remainder.shrink(pickup.amount());")
assert "RANGE=8.0D;" in java
assert "Thread.sleep" not in java and "tickCount%" not in java
# Atomic source write after all anchors/guards passed.
block.write_text(block_src,"utf-8")
be.write_text(be_src,"utf-8")
helper.write_text(java,"utf-8")
print("B1273_PLACED_BACKPACK_MAGNET_8_BLOCK_SERVER_TICK_BATCHED_ATOMIC_PASS")
