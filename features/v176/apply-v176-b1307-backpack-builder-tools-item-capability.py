#!/usr/bin/env python3
"""B1307: real Network Backpack inventory/worn resource supply for builder tools.

Construction Sticks 26.1, Construction Wands Revived and Building Gadgets 2
use Capabilities.Item.ITEM on the player's inventory or Curios/armor stacks.
Register the native 26.1 item capability on every MK1..MK24 Backpack item.
Do NOT change placed Backpack block capability; placed backpacks are explicitly
NOT additional builder supply sources.

The ResourceHandler exposes ONLY actual contents of the three native cells:
never the backpack, cell items, magnet module, or ghost filter. All extraction
is staged on an ItemStack COPY; the actual backpack is modified ONLY through
ItemAccess.exchange(newResource,1,transaction), which is transactional even
for ItemAccess.forStack(stack) (its StackItemAccess onRootCommit restores the
patch into the original stack). Aborted simulations leave all cells unchanged.
Max one exact 26.1 root/subtransaction commit per accepted caller operation.
No modded-builder dependency or tick scan and no external inventory mirror.
"""
import os
from pathlib import Path

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/backpack"
cap=root/"V176BackpackCableCapability.java"
handler=root/"V176BackpackBuilderSupply.java"
old=cap.read_text(encoding="utf-8")
assert not handler.exists(),("B1307_DUPLICATE_BUILDER_CAPABILITY",handler)
anchor="""  event.registerBlockEntity(Capabilities.Item.BLOCK,
      ModBlockEntities.NETWORK_BACKPACK.get(),
      (bag,side)->bag.cableItemHandler());"""
assert old.count(anchor)==1,("B1307_PLACED_CAPABILITY_ANCHOR_DRIFT",old.count(anchor))
assert "event.registerItem(Capabilities.Item.ITEM" not in old
item_list=",\n      ".join(f"dev.obsidiannetwork.ObsidianNetwork.NETWORK_BACKPACK_MK{i}.get()" for i in range(1,25))
replacement=anchor+"""
  // B1307_INVENTORY_WORN_BUILDER_SUPPLY: item-only native capability.
  // Building tools use the ItemStack in a player's inventory / Curios / armor.
  // No additional BLOCK capability: placed backpacks are NOT builder sources.
  event.registerItem(Capabilities.Item.ITEM,
      (stack,access)->new V176BackpackBuilderSupply(access),
      """+item_list+""");"""
modified=old.replace(anchor,replacement,1)
assert modified.count("registerItem(Capabilities.Item.ITEM")==1
assert modified.count("registerBlockEntity(Capabilities.Item.BLOCK")==1
assert modified.index("registerBlockEntity(Capabilities.Item.BLOCK")<modified.index("registerItem(Capabilities.Item.ITEM")

java='''package dev.obsidiannetwork.backpack;

import dev.obsidiannetwork.platform.MinecraftItemStackCodec;
import java.util.List;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.server.ServerLifecycleHooks;
import net.neoforged.neoforge.transfer.ResourceHandler;
import net.neoforged.neoforge.transfer.access.ItemAccess;
import net.neoforged.neoforge.transfer.item.ItemResource;
import net.neoforged.neoforge.transfer.transaction.TransactionContext;

/**
 * B1307: builder tools may consume REAL Cell contents from carried/worn bags.
 *
 * This is an ITEM capability, NOT a BLOCK capability. No direct mutation of
 * player inventory or original stack; no hidden mirroring; no placement hooks.
 * All writes pass through NeoForge's enclosing item-access transaction.
 */
public final class V176BackpackBuilderSupply implements ResourceHandler<ItemResource> {
 private final ItemAccess access;
 public V176BackpackBuilderSupply(ItemAccess access) {
  this.access=java.util.Objects.requireNonNull(access);
 }
 private ItemStack bag() {
  var resource=access.getResource();
  if(resource.isEmpty()||access.getAmount()!=1)return ItemStack.EMPTY;
  ItemStack stack=resource.toStack(1);
  return stack.getItem() instanceof NetworkBackpackItem?stack:ItemStack.EMPTY;
 }
 private List<V176BackpackCells.Entry> entries(){
  ItemStack stack=bag();
  return stack.isEmpty()?List.of():V176BackpackCells.entries(stack);
 }
 private net.minecraft.server.level.ServerLevel world(){
  var server=ServerLifecycleHooks.getCurrentServer();
  return server==null?null:server.overworld();
 }
 private ItemResource resourceOf(V176BackpackCells.Entry entry){
  var world=world();
  if(world!=null){
   var codec=new MinecraftItemStackCodec(world.registryAccess());
   return ItemResource.of(codec.recreate(entry.descriptor(),1));
  }
  // Clients may query material previews without an integrated server;
  // the native identifier is sufficient to display ordinary building blocks.
  // Server extraction below ALWAYS performs exact component verification.
  var item=BuiltInRegistries.ITEM.getValue(entry.descriptor().key().itemId());
  return item==null?ItemResource.EMPTY:ItemResource.of(item);
 }
 @Override public int size(){return entries().size();}
 @Override public ItemResource getResource(int index){
  var entries=entries();
  return index>=0&&index<entries.size()?resourceOf(entries.get(index)):ItemResource.EMPTY;
 }
 @Override public long getAmountAsLong(int index){
  var entries=entries();
  return index>=0&&index<entries.size()?entries.get(index).count():0L;
 }
 @Override public long getCapacityAsLong(int index,ItemResource resource){
  var entries=entries();
  if(index<0||index>=entries.size()||resource.isEmpty())return 0L;
  return resource.equals(resourceOf(entries.get(index)))?entries.get(index).count():0L;
 }
 @Override public boolean isValid(int index,ItemResource resource){
  return false; // Builders can withdraw blocks, NEVER insert hidden upgrades.
 }
 @Override public int insert(int index,ItemResource resource,int amount,TransactionContext tx){
  return 0; // Supply-only. Real Cell/cable/magnet ingress remains unchanged.
 }
 @Override public int extract(int index,ItemResource requested,int amount,TransactionContext tx){
  if(amount<=0||requested.isEmpty()||tx==null)return 0;
  var world=world();
  if(world==null||world.isClientSide())return 0; // Only the server owns items.
  ItemStack before=bag();
  if(before.isEmpty())return 0;
  var list=V176BackpackCells.entries(before);
  if(index<0||index>=list.size())return 0;
  var entry=list.get(index);
  // Exact item AND component match before any transactional mutation.
  if(!requested.equals(resourceOf(entry)))return 0;
  int n=(int)Math.min((long)amount,entry.count());
  if(n<=0)return 0;
  ItemStack updated=before.copy();
  var result=V176BackpackCells.extract(world,updated,entry.descriptor(),n);
  int accepted=(int)result.accepted();
  if(accepted<=0)return 0;
  // The supplied ItemAccess is a real transactional item location. Its
  // exchange updates the original backpack's components only if BOTH
  // remove/replace succeed and the parent transaction is committed.
  if(access.exchange(ItemResource.of(updated),1,tx)!=1)return 0;
  return accepted;
 }
}
'''
assert "access.exchange(ItemResource.of(updated),1,tx)" in java
assert "V176BackpackCells.extract(world,updated,entry.descriptor(),n)" in java
assert "registerBlockEntity(Capabilities.Item.BLOCK" in modified
assert "NETWORK_BACKPACK_MK24" in modified and "NETWORK_BACKPACK_MK1" in modified
assert "onRootCommit" in java
handler.write_text(java,encoding="utf-8")
cap.write_text(modified,encoding="utf-8")
print("B1307_BACKPACK_INVENTORY_CURIO_WORN_BUILDER_CAPABILITY_REAL_CELLS_TRANSACTIONAL_PASS")
