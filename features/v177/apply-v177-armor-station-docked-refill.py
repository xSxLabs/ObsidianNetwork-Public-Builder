#!/usr/bin/env python3
"""v1.7.7: service an authentic deployed Power Armor suit on a station's front red pad.

The existing five-tick station tick already services worn armor. Reuse it,
never create FE or NutriPaste, never copy an item into player inventory,
and never service a generic or foreign armor stand.
"""
import os
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def patch(rel,old,new):
 p=J/rel
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("V177_DOCKED_STATION_SOURCE_DRIFT",rel,s.count(old),old[:120])
 p.write_text(s.replace(old,new,1),encoding="utf-8")

# The original finder requires an online owner for upgrade interactions.
# A charging station must also work when that owner has disconnected.
# Use the SAME strict front-facing red pad, full four-piece tier validation,
# and our own protected suit marker; never charge arbitrary armor stands.
patch("powerarmor/PowerArmorSuitWorld.java",
 ' public static ArmorStand findNearby(Level level,BlockPos station,ServerPlayer player){',
 ''' /** Find one deployed full Power Armor suit on the EXACT red pad, owner online or not.
  *  A normal stand, a rear/diagonal stand, and multiple overlapping suits are ignored.
  */
 public static ArmorStand findDockedOnPad(Level level,BlockPos station){
  var state=level.getBlockState(station);
  if(!(state.getBlock() instanceof ArmorStationBlock))return null;
  BlockPos pad=station.relative(state.getValue(ArmorStationBlock.FACING));
  List<ArmorStand> suits=level.getEntitiesOfClass(ArmorStand.class,
      new AABB(pad),e->e.entityTags().contains(MARKER)&&full(e)
          &&e.blockPosition().equals(pad));
  return suits.size()==1?suits.get(0):null;
 }
 public static ArmorStand findNearby(Level level,BlockPos station,ServerPlayer player){''')

# Reuse the existing 25-real-FE/HP, at most 10 HP per piece repair algorithm.
# Called on copies of the stand's actual ItemStacks; install copies only after
# the station energy debit succeeds.
patch("powerarmor/V177ArmorIntegrity.java",
 ' private static int repairOne(ItemStack stack,int availableFe){',
 ' public static int repairOne(ItemStack stack,int availableFe){')

# The same server-only five-tick station tick already runs worn integrity,
# worn helmet paste and worn FE. Docked servicing consumes what REMAINS.
# Keep all existing player behavior, cap and scheduling unchanged.
patch("powerarmor/ArmorStationBlockEntity.java",
 '    V177ArmorStationCharge.chargeWornArmor(server,pos,be);',
 '''    V177ArmorStationCharge.chargeWornArmor(server,pos,be);
    V177ArmorStationDockService.service(server,pos,be);''')

target=J/"powerarmor/V177ArmorStationDockService.java"
assert not target.exists(),("V177_DOCKED_STATION_DUPLICATE",str(target))
target.write_text(r'''package dev.obsidiannetwork.powerarmor;

import dev.obsidiannetwork.core.EnergyTool;
import dev.obsidiannetwork.nutrition.NutriPaste;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.item.ItemStack;

/** Refills a real, server-owned deployed ArmorStand suit on the exact red pad.
 *  Runs after the old worn-player services, from the SAME existing five-tick
 *  Armor Station tick. No additional ticker, no cross-chunk scan or free FE.
 */
public final class V177ArmorStationDockService {
 private V177ArmorStationDockService(){}

 public static void service(ServerLevel level,BlockPos pos,
                            ArmorStationBlockEntity station){
  // No work / stand lookup if station has neither actual resource.
  if(station.v177StoredFe()<=0&&station.v177StoredPaste()<=0L)return;
  ArmorStand stand=PowerArmorSuitWorld.findDockedOnPad(level,pos);
  if(stand==null)return;

  // 1. Structural integrity comes first: exactly the original 10 HP
  // per piece / service, 25 FE per HP, 1000 real FE max per five ticks.
  int budget=Math.min(1000,station.v177StoredFe());
  for(int i=0;i<PowerArmorRuntime.SLOTS.length&&budget>0;i++){
   ItemStack original=stand.getItemBySlot(PowerArmorRuntime.SLOTS[i]);
   if(!V177ArmorIntegrity.piece(original,i))continue;
   ItemStack changed=original.copy();
   int cost=V177ArmorIntegrity.repairOne(changed,budget);
   if(cost<=0)continue;
   // Stage the modified copy and commit ONLY after actual FE debit.
   if(station.v177ConsumeFe(cost)!=cost)return;
   stand.setItemSlot(PowerArmorRuntime.SLOTS[i],changed);
   budget-=cost;
  }

  // 2. The actual helmet gets real, registered NutriPaste from the
  // same station's physical tank, even if its owner is offline.
  if(station.v177StoredPaste()>0L){
   ItemStack helmet=stand.getItemBySlot(PowerArmorRuntime.SLOTS[0]);
   if(V177ArmorIntegrity.piece(helmet,0)){
    ItemStack changed=helmet.copy();
    long inserted=NutriPaste.add(changed,station.v177StoredPaste());
    if(inserted>0L){
     if(station.v177TakePaste(inserted)!=inserted)return;
     stand.setItemSlot(PowerArmorRuntime.SLOTS[0],changed);
    }
   }
  }

  // 3. Recharge the same four original ItemStacks in-place from the
  // shared station 400k FE buffer. Two passes preserve worn-armor fairness.
  int available=Math.min(V177ArmorStationCharge.MAX_FE_PER_SERVICE,
                         station.v177StoredFe());
  if(available<=0)return;
  int perPiece=Math.max(1,available/PowerArmorRuntime.SLOTS.length);
  for(int pass=0;pass<2&&available>0;pass++){
   for(int i=0;i<PowerArmorRuntime.SLOTS.length&&available>0;i++){
    ItemStack armor=stand.getItemBySlot(PowerArmorRuntime.SLOTS[i]);
    if(!V177ArmorIntegrity.piece(armor,i))continue;
    long stored=EnergyTool.energy(armor);
    long missing=Math.max(0L,EnergyTool.capacity(armor)-stored);
    if(missing<=0L)continue;
    int offered=(int)Math.min(missing,Math.min((long)available,
                      pass==0?(long)perPiece:(long)available));
    if(offered<=0)continue;
    int drawn=station.v177ConsumeFe(offered);
    if(drawn<=0)return;
    ItemStack changed=armor.copy();
    EnergyTool.setEnergy(changed,stored+drawn);
    stand.setItemSlot(PowerArmorRuntime.SLOTS[i],changed);
    available-=drawn;
   }
  }
 }
}
''',encoding="utf-8")
print("V177_DOCKED_POWER_ARMOR_400K_FE_1000_HP_1M_PASTE_FRONT_PAD_PASS")
