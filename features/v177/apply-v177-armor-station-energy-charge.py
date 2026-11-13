#!/usr/bin/env python3
"""v1.7.7: station simultaneously repairs integrity, refills paste and recharges FE.

Runs after apply-v177-armor-station-nutripaste.py. Reuses the real 400k-FE
station buffer and the real EnergyTool component/capacity of each worn piece.
No additional FE storage, no wireless energy creation and no per-player ticker.
"""
import os
from pathlib import Path

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
station=root/"powerarmor/ArmorStationBlockEntity.java"
text=station.read_text(encoding="utf-8")
old="""    // Paste refill does not consume FE and still works while the FE tank is empty.
    V177ArmorStationPaste.fillHelmet(server,pos,be);"""
new="""    // Paste refills independently of FE; integrity repair keeps first priority.
    V177ArmorStationPaste.fillHelmet(server,pos,be);
    // Recharge all FOUR worn armor pieces from real station FE, never create FE.
    V177ArmorStationCharge.chargeWornArmor(server,pos,be);"""
assert text.count(old)==1,("V177_ARMOR_STATION_RECHARGE_DRIFT",text.count(old))
station.write_text(text.replace(old,new,1),encoding="utf-8")

file=root/"powerarmor/V177ArmorStationCharge.java"
assert not file.exists(),("V177_ARMOR_STATION_RECHARGE_ALREADY_PRESENT",str(file))
file.write_text(r'''package dev.obsidiannetwork.powerarmor;

import dev.obsidiannetwork.core.EnergyTool;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;

/** Native FE charging for all four worn pieces while standing on the station.
 *
 *  Existing integrity repairs take precedence. The station has 400,000 FE
 *  of *real* input-only storage; every charged FE is debited from that same
 *  tank. Maximum 400,000 FE per 5-tick cycle. With steady FE input, a 4x16M-FE suit charges within 60 seconds at 20 TPS; no extra ticker.
 */
public final class V177ArmorStationCharge {
 private V177ArmorStationCharge(){}
 public static final int MAX_FE_PER_SERVICE=400_000; // 60-second 4x16M-FE target with sufficient real input

 public static void chargeWornArmor(ServerLevel level,BlockPos pos,
                                   ArmorStationBlockEntity station){
  int available=Math.min(MAX_FE_PER_SERVICE,station.v177StoredFe());
  if(available<=0)return;
  for(ServerPlayer player:level.players()){
   if(!player.isAlive()||!PowerArmorRuntime.full(player))continue;
   // Same bounding volume as the established integrity repair/paste service.
   if(Math.abs(player.getX()-(pos.getX()+.5D))>1D
       ||Math.abs(player.getZ()-(pos.getZ()+.5D))>1D
       ||player.getY()<pos.getY()
       ||player.getY()>pos.getY()+2.5D)continue;

   // First pass distributes FE fairly across all four worn suit pieces.
   // Second pass reuses unused shares when some pieces are already full.
   int perPiece=Math.max(1,available/PowerArmorRuntime.SLOTS.length);
   for(int pass=0;pass<2&&available>0;pass++){
    for(int slot=0;slot<PowerArmorRuntime.SLOTS.length&&available>0;slot++){
     ItemStack armor=player.getItemBySlot(PowerArmorRuntime.SLOTS[slot]);
     if(!V177ArmorIntegrity.piece(armor,slot))continue;
     long capacity=EnergyTool.capacity(armor);
     long stored=EnergyTool.energy(armor);
     long missing=Math.max(0L,capacity-stored);
     if(missing<=0L)continue;
     int offered=(int)Math.min(missing,Math.min(
          (long)available,pass==0?(long)perPiece:(long)available));
     if(offered<=0)continue;
     // Debit BEFORE modifying the armor ItemStack: FE can never be duplicated.
     int drawn=station.v177ConsumeFe(offered);
     if(drawn<=0)return;
     EnergyTool.setEnergy(armor,stored+drawn);
     available-=drawn;
    }
   }
   // Exactly one player is serviced by one station every five ticks.
   break;
  }
 }
}
''',encoding="utf-8")
print("V177_ARMOR_STATION_THREE_WAY_SERVICE_PASS: integrity + 400k-FE per-cycle suit recharge + helmet paste")
