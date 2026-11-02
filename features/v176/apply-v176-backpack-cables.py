#!/usr/bin/env python3
"""Transactional extract-only xSxLabs Item Cable bridge for placed backpacks.

Exposes REAL native StorageCell contents through NeoForge
Capabilities.Item.BLOCK. Upgrade, cells, filters, and backpack stack itself are
never visible to Item Cables. SnapshotJournal rolls back source state when a
destination simulates/fails and never commits the transaction.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
p=J/"backpack/NetworkBackpackBlockEntity.java"
s=p.read_text(encoding="utf-8")
needle=" private ItemStack backpack=ItemStack.EMPTY;"
assert s.count(needle)==1,("V176_BPK_CABLE_BE_DRIFT",s.count(needle))
s=s.replace(needle,''' private ItemStack backpack=ItemStack.EMPTY;
 private final net.neoforged.neoforge.transfer.transaction.SnapshotJournal<ItemStack> cableJournal=
   new net.neoforged.neoforge.transfer.transaction.SnapshotJournal<>() {
    @Override protected ItemStack createSnapshot(){return backpack.copy();}
    @Override protected void revertToSnapshot(ItemStack before){backpack=before.copy();}
    @Override protected void onRootCommit(ItemStack before){setChanged();}
   };
 private final net.neoforged.neoforge.transfer.ResourceHandler<
     net.neoforged.neoforge.transfer.item.ItemResource> cableHandler=
   new net.neoforged.neoforge.transfer.ResourceHandler<>() {
    private java.util.List<V176BackpackCells.Entry> list(){
     if(backpack.isEmpty()||level==null)return java.util.List.of();
     return V176BackpackCells.entries(backpack);
    }
    @Override public int size(){return list().size();}
    @Override public net.neoforged.neoforge.transfer.item.ItemResource getResource(int i){
     var entries=list();
     if(i<0||i>=entries.size())return net.neoforged.neoforge.transfer.item.ItemResource.EMPTY;
     var codec=new dev.obsidiannetwork.platform.MinecraftItemStackCodec(level.registryAccess());
     return net.neoforged.neoforge.transfer.item.ItemResource.of(
       codec.recreate(entries.get(i).descriptor(),1));
    }
    @Override public long getAmountAsLong(int i){
     var entries=list();return i>=0&&i<entries.size()?entries.get(i).count():0L;
    }
    @Override public long getCapacityAsLong(int i,
      net.neoforged.neoforge.transfer.item.ItemResource resource){return 0L;}
    @Override public boolean isValid(int i,net.neoforged.neoforge.transfer.item.ItemResource resource){
     return false; // extract-only, never fill hidden upgrade/cell/filter slots.
    }
    @Override public int insert(int i,net.neoforged.neoforge.transfer.item.ItemResource item,
      int amount,net.neoforged.neoforge.transfer.transaction.TransactionContext tx){return 0;}
    @Override public int extract(int i,net.neoforged.neoforge.transfer.item.ItemResource wanted,
      int amount,net.neoforged.neoforge.transfer.transaction.TransactionContext tx){
     if(amount<=0||level==null||backpack.isEmpty())return 0;
     var entries=list();
     if(i<0||i>=entries.size())return 0;
     var d=entries.get(i).descriptor();
     var codec=new dev.obsidiannetwork.platform.MinecraftItemStackCodec(level.registryAccess());
     if(!net.neoforged.neoforge.transfer.item.ItemResource.of(
          codec.recreate(d,1)).equals(wanted))return 0;
     int max=(int)Math.min((long)amount,entries.get(i).count());
     if(max<=0)return 0;
     cableJournal.updateSnapshots(tx);
     var result=V176BackpackCells.extract(level,backpack,d,max);
     return (int)result.accepted();
    }
   };
 public net.neoforged.neoforge.transfer.ResourceHandler<
     net.neoforged.neoforge.transfer.item.ItemResource> cableItemHandler(){
  return cableHandler;
 }
''',1)
p.write_text(s,encoding="utf-8")

cap=J/"backpack/V176BackpackCableCapability.java"
assert not cap.exists()
cap.write_text('''package dev.obsidiannetwork.backpack;

import dev.obsidiannetwork.registry.ModBlockEntities;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.capabilities.RegisterCapabilitiesEvent;

/** Native capability: other mods' Item Cables can extract safely as well. */
@EventBusSubscriber(modid="obsidiannetwork")
public final class V176BackpackCableCapability {
 private V176BackpackCableCapability(){}
 @SubscribeEvent public static void register(RegisterCapabilitiesEvent event){
  event.registerBlockEntity(Capabilities.Item.BLOCK,
      ModBlockEntities.NETWORK_BACKPACK.get(),
      (bag,side)->bag.cableItemHandler());
 }
}
''',encoding="utf-8")
print("V176_BACKPACK_PLACED_ITEM_CABLE_NATIVE_TRANSACTIONAL_EXTRACTION_PASS")
