#!/usr/bin/env python3
"""v1.7.7: native Fluid Cable NutriPaste input, 500 mB station tank, worn helmet refill.

Non-destructive addition after apply-v177-armor-integrity-repair.py. The station
keeps its 200,000 FE buffer and energy-based integrity repair independent of
the paste buffer. Fluid transfer uses NeoForge transactional rollback.
"""
import os
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def patch(rel,old,new):
 p=J/rel
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("V177_STATION_PASTE_SOURCE_DRIFT",rel,s.count(old),old[:130])
 p.write_text(s.replace(old,new,1),encoding="utf-8")

patch("powerarmor/ArmorStationBlockEntity.java",
''' public int v177StoredFe(){return (int)v177Energy.getAmountAsLong();}''',
''' public int v177StoredFe(){return (int)v177Energy.getAmountAsLong();}
 // V177_STATION_NUTRIPASTE_500MB: accepts ONLY real registered NutriPaste.
 // Never substitute water or energy; never extract paste through a pipe.
 public static final long V177_PASTE_CAPACITY=500L;
 private long v177Paste=0L;
 private final net.neoforged.neoforge.transfer.transaction.SnapshotJournal<Long>
     v177PasteJournal=new net.neoforged.neoforge.transfer.transaction.SnapshotJournal<>() {
  @Override protected Long createSnapshot(){return v177Paste;}
  @Override protected void revertToSnapshot(Long before){v177Paste=before;}
  @Override protected void onRootCommit(Long before){
   if(before!=v177Paste)ArmorStationBlockEntity.this.setChanged();
  }
 };
 private final net.neoforged.neoforge.transfer.ResourceHandler<
      net.neoforged.neoforge.transfer.fluid.FluidResource>
      v177PastePort=new net.neoforged.neoforge.transfer.ResourceHandler<>() {
  private net.neoforged.neoforge.transfer.fluid.FluidResource paste(){
   return net.neoforged.neoforge.transfer.fluid.FluidResource.of(
      dev.obsidiannetwork.nutrition.NutriPasteFluids.SOURCE.get());
  }
  @Override public int size(){return 1;}
  @Override public net.neoforged.neoforge.transfer.fluid.FluidResource getResource(int slot){
   java.util.Objects.checkIndex(slot,1);
   return v177Paste>0L?paste():
      net.neoforged.neoforge.transfer.fluid.FluidResource.EMPTY;
  }
  @Override public long getAmountAsLong(int slot){
   java.util.Objects.checkIndex(slot,1);return v177Paste;
  }
  @Override public boolean isValid(int slot,
      net.neoforged.neoforge.transfer.fluid.FluidResource resource){
   java.util.Objects.checkIndex(slot,1);
   return paste().equals(resource);
  }
  @Override public long getCapacityAsLong(int slot,
      net.neoforged.neoforge.transfer.fluid.FluidResource resource){
   java.util.Objects.checkIndex(slot,1);
   return resource.isEmpty()||isValid(slot,resource)?V177_PASTE_CAPACITY:0L;
  }
  @Override public int insert(int slot,
       net.neoforged.neoforge.transfer.fluid.FluidResource resource,int offered,
       net.neoforged.neoforge.transfer.transaction.TransactionContext tx){
   java.util.Objects.checkIndex(slot,1);
   if(offered<=0||!isValid(slot,resource))return 0;
   int accepted=(int)Math.min((long)offered,V177_PASTE_CAPACITY-v177Paste);
   if(accepted>0){v177PasteJournal.updateSnapshots(tx);v177Paste+=accepted;}
   return accepted;
  }
  @Override public int extract(int slot,
       net.neoforged.neoforge.transfer.fluid.FluidResource resource,int requested,
       net.neoforged.neoforge.transfer.transaction.TransactionContext tx){
   java.util.Objects.checkIndex(slot,1);
   return 0; // input only: helmet refill is server-authorized instead
  }
 };
 public net.neoforged.neoforge.transfer.ResourceHandler<
    net.neoforged.neoforge.transfer.fluid.FluidResource> v177PastePort(){
  return v177PastePort;
 }
 public long v177StoredPaste(){return v177Paste;}
 public long v177TakePaste(long used){
  long actual=Math.max(0L,Math.min(v177Paste,used));
  if(actual>0L){v177Paste-=actual;setChanged();}
  return actual;
 }''')

patch("powerarmor/ArmorStationBlockEntity.java",
'  out.putInt("v177_armor_station_fe",v177StoredFe());',
'''  out.putInt("v177_armor_station_fe",v177StoredFe());
  out.putLong("v177_armor_station_paste_mb",v177StoredPaste());''')

patch("powerarmor/ArmorStationBlockEntity.java",
'  v177Energy.set(Math.max(0,Math.min(200000,in.getIntOr("v177_armor_station_fe",0))));',
'''  v177Energy.set(Math.max(0,Math.min(200000,in.getIntOr("v177_armor_station_fe",0))));
  v177Paste=Math.max(0L,Math.min(V177_PASTE_CAPACITY,
       in.getLongOr("v177_armor_station_paste_mb",0L)));''')

patch("powerarmor/ArmorStationBlockEntity.java",
'''    V177ArmorIntegrity.repairNearby(server,pos,be);''',
'''   {
    V177ArmorIntegrity.repairNearby(server,pos,be);
    // Paste refill does not consume FE and still works while the FE tank is empty.
    V177ArmorStationPaste.fillHelmet(server,pos,be);
   }''')

patch("backpack/V176BackpackCableCapability.java",
'''  // V177_STATION_NATIVE_ENERGY_INPUT: no output/extract path.
  event.registerBlockEntity(Capabilities.Energy.BLOCK,
      ModBlockEntities.ARMOR_STATION.get(),
      (station,side)->station.v177Energy());''',
'''  // V177_STATION_NATIVE_ENERGY_INPUT: no output/extract path.
  event.registerBlockEntity(Capabilities.Energy.BLOCK,
      ModBlockEntities.ARMOR_STATION.get(),
      (station,side)->station.v177Energy());
  // V177_STATION_FLUID_INPUT: the EXISTING fluid cable can connect directly.
  event.registerBlockEntity(Capabilities.Fluid.BLOCK,
      ModBlockEntities.ARMOR_STATION.get(),
      (station,side)->station.v177PastePort());''')

file=J/"powerarmor/V177ArmorStationPaste.java"
assert not file.exists(),("V177_STATION_PASTE_DUPLICATE",file)
file.write_text(r'''package dev.obsidiannetwork.powerarmor;

import dev.obsidiannetwork.nutrition.NutriPaste;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;

/** Refills the HELMET only while a complete power suit is worn on the station. */
public final class V177ArmorStationPaste {
 private V177ArmorStationPaste(){}

 public static void fillHelmet(ServerLevel world,BlockPos pos,
                               ArmorStationBlockEntity station){
  if(station.v177StoredPaste()<=0L)return;
  for(ServerPlayer player:world.players()){
   if(!player.isAlive()||!PowerArmorRuntime.full(player))continue;
   // Same standing-on-platform proximity as integrity repair.
   if(Math.abs(player.getX()-(pos.getX()+.5D))>1D
       ||Math.abs(player.getZ()-(pos.getZ()+.5D))>1D
       ||player.getY()<pos.getY()
       ||player.getY()>pos.getY()+2.5D)continue;
   ItemStack helmet=player.getItemBySlot(PowerArmorRuntime.SLOTS[0]);
   if(!V177ArmorIntegrity.piece(helmet,0))continue;
   long available=station.v177StoredPaste();
   long inserted=NutriPaste.add(helmet,available);
   // Debit ONLY what actually landed in the real armor helmet.
   if(inserted>0L)station.v177TakePaste(inserted);
   break; // one nearby player per station tick, never duplicate fluid
  }
 }
}
''',encoding="utf-8")
print("V177_ARMOR_STATION_500MB_NUTRIPASTE_FLUID_CABLE_HELMET_FILL_INSTALLED")
