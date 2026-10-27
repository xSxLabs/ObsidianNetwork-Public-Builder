#!/usr/bin/env python3
"""v1.7.3 legacy Planter key migration. No edits to frozen v1.7.2 scripts.

Old Planters inserted ItemKey.simple(item_id); terminals store the exact
MinecraftItemStackCodec descriptor. Migrate ONLY known plain planter drops.
Network APIs update per-cell quantities, indices and source maps together.
"""
import os
from pathlib import Path

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
planter=root/"blockentity/NetworkPlanterBlockEntity.java"
terminal=root/"menu/StorageTerminalMenu.java"
src=planter.read_text(encoding="utf-8")
menu=terminal.read_text(encoding="utf-8")
old_tick="""  if(world.getGameTime()%5L==0L)be.flush(world);"""
new_tick="""   if(world.getGameTime()%5L==0L)be.flush(world);
   // V173_PLANTER_LEGACY_MIGRATION: works even with empty harvest buffer.
   if(world.getGameTime()%20L==0L){
    for(Direction side:Direction.values()){
     BlockPos cable=pos.relative(side);
     if(!world.hasChunkAt(cable)||!world.getBlockState(cable).is(ObsidianNetwork.NETWORK_CABLE.get()))continue;
     var runtime=WorldTopologyBridge.runtimeForAccessory(world,cable);
     if(runtime!=null)
      dev.obsidiannetwork.network.LegacyPlanterKeyMigration.tick(world,runtime);
     break;
    }
   }"""
old_insert="""    var descriptor=codec.describe(stack.copyWithCount(1));
    long accepted=runtime.storage().insertExact("""
new_insert="""    var descriptor=codec.describe(stack.copyWithCount(1));
    // Exact StorageTerminalMenu behavior: register the canonical descriptor.
    runtime.descriptors().registerKnown(descriptor.key(),descriptor.canonicalPayload());
    long accepted=runtime.storage().insertExact("""
old_menu="ServerLevel openingLevel = this.terminalServerLevel();"
new_menu="""ServerLevel openingLevel = this.terminalServerLevel();
          // Repair pre-existing planter stacks even if no planter remains.
          // Migration is server-only and paced per logical storage runtime.
          if (openingLevel != null && inventory.player instanceof ServerPlayer) {
             NetworkRuntime migrationRt = this.wireless
                ? WorldTopologyBridge.runtimeForAccessory(openingLevel,this.terminalPos)
                : WorldTopologyBridge.runtimeForTerminal(openingLevel,this.terminalPos);
             if (migrationRt != null)
                dev.obsidiannetwork.network.LegacyPlanterKeyMigration.tick(openingLevel,migrationRt);
          }"""
for label,old,new in (("planter idle tick",old_tick,new_tick),
                       ("exact descriptor catalog",old_insert,new_insert)):
    if src.count(old)!=1: raise RuntimeError(f"{label}: expected one source anchor, got {src.count(old)}")
    src=src.replace(old,new,1)
if menu.count(old_menu)!=1: raise RuntimeError("terminal open migration anchor missing")
menu=menu.replace(old_menu,new_menu,1)
# Keep migration running while the terminal remains open, even after all
# planters have been removed. Avoid expensive topology lookups on other ticks.
menu_anchor="public BlockPos terminalPos()"
if menu.count(menu_anchor)!=1 or "void broadcastChanges()" in menu:
    raise RuntimeError("Terminal continuous-migration injection has conflicting source")
continuation="""// V173_PLANTER_TERMINAL_CONTINUOUS_MIGRATION: no remaining Planter required.
   private long xsxLastPlanterMigrationTick=Long.MIN_VALUE;
   @Override public void broadcastChanges(){
      super.broadcastChanges();
      if(!(this.player instanceof ServerPlayer))return;
      ServerLevel level=this.terminalServerLevel();
      if(level==null)return;
      long now=level.getGameTime();
      if(now%20L!=0L||now==xsxLastPlanterMigrationTick)return;
      xsxLastPlanterMigrationTick=now;
      NetworkRuntime rt=this.wireless
          ? WorldTopologyBridge.runtimeForAccessory(level,this.terminalPos)
          : WorldTopologyBridge.runtimeForTerminal(level,this.terminalPos);
      if(rt!=null)dev.obsidiannetwork.network.LegacyPlanterKeyMigration.tick(level,rt);
   }
   """
menu=menu.replace(menu_anchor,continuation+menu_anchor,1)
helper=root/"network/LegacyPlanterKeyMigration.java"
if helper.exists(): raise RuntimeError("Migration helper already exists")
java=r'''package dev.obsidiannetwork.network;

import dev.obsidiannetwork.block.NetworkPlanterBlock;
import dev.obsidiannetwork.core.ItemKey;
import dev.obsidiannetwork.core.NetworkRuntime;
import dev.obsidiannetwork.platform.MinecraftItemStackCodec;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.WeakHashMap;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

/** V173_LEGACY_PLANTER_NORMALIZE: convert old ID-only crop records to the
 * exact plain-ItemStack descriptor used by Storage Terminal. Never change
 * component-bearing keys. Runs on the server thread, bounded per network.
 */
public final class LegacyPlanterKeyMigration {
 private LegacyPlanterKeyMigration(){}
 private static final int PER_KEY=512;
 private static final int KEYS_PER_TICK=8;
 private static final Map<NetworkRuntime,Cursor> CURSORS=
     Collections.synchronizedMap(new WeakHashMap<>());
 private static final class Cursor {
  long lastTick=Long.MIN_VALUE;
  int next=0;
 }
 private static volatile List<Item> eligible;

 private static List<Item> items(){
  List<Item> cached=eligible;
  if(cached!=null)return cached;
  synchronized(LegacyPlanterKeyMigration.class){
   if(eligible!=null)return eligible;
   LinkedHashSet<Item> all=new LinkedHashSet<>();
   for(NetworkPlanterBlock.Plant plant:NetworkPlanterBlock.Plant.values()){
    all.add(plant.produce);
    if(plant.leaves!=Items.AIR)all.add(plant.leaves);
    all.add(plant.seed);
   }
   all.add(Items.STICK);
   all.add(Items.APPLE);
   all.add(Items.MELON_SLICE);
   all.add(Items.SWEET_BERRIES);
   all.remove(Items.AIR);
   eligible=List.copyOf(all);
   return eligible;
  }
 }

 /** One network gets at most eight candidate checks per second, with at most
  * 512 moved items each; never scan every connected cell on each planter tick.
  */
 public static void tick(ServerLevel level,NetworkRuntime runtime){
  if(level==null||runtime==null)return;
  long now=level.getGameTime();
  Cursor cursor;
  synchronized(CURSORS){
   cursor=CURSORS.computeIfAbsent(runtime,ignored->new Cursor());
   if(cursor.lastTick!=Long.MIN_VALUE && now>=cursor.lastTick && now-cursor.lastTick<20L)return;
   cursor.lastTick=now;
  }
  List<Item> drops=items();
  for(int attempt=0;attempt<Math.min(KEYS_PER_TICK,drops.size());attempt++){
   Item drop=drops.get(cursor.next);
   boolean changed=migratePlainItem(level,runtime,drop);
   ItemKey oldKey=ItemKey.simple(BuiltInRegistries.ITEM.getKey(drop).toString());
   // Drain large old stacks over subsequent seconds instead of stalling a tick.
   if(changed && runtime.storage().index().amount(oldKey)>0L)return;
   cursor.next=(cursor.next+1)%drops.size();
  }
 }

 /** Server-only one-key operation. Never rekey special components, other
  * item types or anything not produced by a Network Planter.
  */
 public static boolean migratePlainItem(ServerLevel level,NetworkRuntime runtime,Item item){
  if(level==null||runtime==null||item==null||!items().contains(item))return false;
  var storage=runtime.storage();
  ItemKey old=ItemKey.simple(BuiltInRegistries.ITEM.getKey(item).toString());
  long originalOld=storage.index().amount(old);
  if(originalOld<=0L)return false;
  var exact=new MinecraftItemStackCodec(level.registryAccess()).describe(new ItemStack(item));
  if(exact.key().equals(old))return false;
  long originalExact=storage.index().amount(exact.key());
  long requested=Math.min(PER_KEY,originalOld);
  long removed=storage.extract(old,requested);
  if(removed<=0L)return false;
  boolean committed=false;
  RuntimeException failure=null;
  try{
   if(removed==requested &&
      storage.previewInsertExact(exact.key(),exact.canonicalPayload(),removed)==removed){
    runtime.descriptors().registerKnown(exact.key(),exact.canonicalPayload());
    committed=storage.insertExact(exact.key(),exact.canonicalPayload(),removed)==removed;
   }
  }catch(RuntimeException ex){
   failure=ex;
  }
  if(!committed){
   // Undo any partial new-key insertion BEFORE restoring old-key quantity.
   // Storage is only mutated on this single authoritative server thread.
   long newDelta=storage.index().amount(exact.key())-originalExact;
   if(newDelta<0L||newDelta>removed)
    throw new IllegalStateException("Legacy planter migration unexpected exact-key delta",failure);
   if(newDelta>0L && storage.extract(exact.key(),newDelta)!=newDelta)
    throw new IllegalStateException("Legacy planter migration exact rollback failed",failure);
   long oldDeficit=originalOld-storage.index().amount(old);
   if(oldDeficit<0L||oldDeficit>removed ||
      (oldDeficit>0L && storage.insert(old,oldDeficit)!=oldDeficit))
    throw new IllegalStateException("Legacy planter migration old-key rollback failed",failure);
   if(storage.index().amount(old)!=originalOld||
      storage.index().amount(exact.key())!=originalExact)
    throw new IllegalStateException("Legacy planter migration conservation rollback failed",failure);
   return false;
  }
  if(storage.index().amount(old)!=originalOld-removed||
      storage.index().amount(exact.key())!=originalExact+removed)
   throw new IllegalStateException("Legacy planter migration conservation mismatch");
  return true;
 }
}
'''
# Guard the mutation only after every source condition is known.
for token in ("V173_PLANTER_EXACT_ITEM_KEY","runtime.descriptors().registerKnown","stack.shrink((int)Math.min(accepted,stack.getCount()))"):
 if token not in src:raise RuntimeError("existing exact planter behavior missing: "+token)
helper.parent.mkdir(parents=True,exist_ok=True)
planter.write_text(src,encoding="utf-8")
terminal.write_text(menu,encoding="utf-8")
helper.write_text(java,encoding="utf-8")
print("V173_LEGACY_PLANTER_MIGRATION_APPLIED: paced migration on planter tick and terminal open; rollback and conserved counts")
