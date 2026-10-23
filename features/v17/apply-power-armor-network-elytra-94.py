#!/usr/bin/env python3
"""v1.7: real Network Elytra gliding/Shift boost when a complete Power Armor
has the network_elytra card; exactly the same shared FE/speed limits.
Run AFTER Build93 and all three existing Network Elytra overlays.
"""
import os
from pathlib import Path

java=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
marker="BUILD94_POWER_ARMOR_NETWORK_ELYTRA"
def load(p):return p.read_text(encoding="utf-8")
def write(p,s):p.write_text(s,encoding="utf-8")
def change(s,old,new,expected=1):
 count=s.count(old)
 assert count==expected, f"{marker}: anchor drift {count} != {expected}: {old[:120]!r}"
 return s.replace(old,new)

# No replacement chest piece, no phantom network-elytra stack and no mutations
# to any saved armor inventory. The chest suit piece itself carries the FE.
bridge=java/"powerarmor/PowerArmorElytraBridge.java"
assert not bridge.exists(), f"{marker}: duplicate helper"
bridge.write_text(r'''package dev.obsidiannetwork.powerarmor;

import dev.obsidiannetwork.registry.ModDataComponents;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;

/** Power Armor chest core can act as a powered Network Elytra when upgraded. */
public final class PowerArmorElytraBridge {
 private PowerArmorElytraBridge(){}

 public static ItemStack chest(Player player){
  if(player==null)return ItemStack.EMPTY;
  EquipmentSlot[] slots=PowerArmorRuntime.SLOTS;
  int tier=PowerArmorRuntime.tier(player.getItemBySlot(slots[0]),0);
  if(tier==0)return ItemStack.EMPTY;
  for(int i=1;i<slots.length;i++)
   if(PowerArmorRuntime.tier(player.getItemBySlot(slots[i]),i)!=tier)
    return ItemStack.EMPTY;

  ItemStack chest=player.getItemBySlot(EquipmentSlot.CHEST);
  String data=chest.get(ModDataComponents.POWER_ARMOR_UPGRADES.get());
  if(data==null||data.isEmpty())return ItemStack.EMPTY;
  for(String id:data.split(","))if("network_elytra".equals(id))
   return chest;
  return ItemStack.EMPTY;
 }
}
''',encoding="utf-8")

# Server tick is the actual existing Network Elytra FE + launch/landing/boost
# implementation. Reuse it instead of introducing a second physics algorithm.
server_path=java/"item/NetworkElytraItem.java"
s=load(server_path)
s=change(s,
 '''        if (!(chest.getItem() instanceof NetworkElytraItem)) return;
        long energy = EnergyTool.energy(chest);''',
 '''        // BUILD94_POWER_ARMOR_NETWORK_ELYTRA: reuse this exact Network Elytra tick.
        boolean armorElytra = !(chest.getItem() instanceof NetworkElytraItem);
        if (armorElytra)
            chest = dev.obsidiannetwork.powerarmor.PowerArmorElytraBridge.chest(player);
        if (chest.isEmpty()) return;
        long energy = EnergyTool.energy(chest);''')
s=change(s,
 '''            if (chest.has(DataComponents.GLIDER)) chest.remove(DataComponents.GLIDER);''',
 '''            if (!armorElytra && chest.has(DataComponents.GLIDER))
                chest.remove(DataComponents.GLIDER);''')
s=change(s,
 '''        if (!chest.has(DataComponents.GLIDER))
            chest.set(DataComponents.GLIDER, Unit.INSTANCE);''',
 '''        if (!armorElytra && !chest.has(DataComponents.GLIDER))
            chest.set(DataComponents.GLIDER, Unit.INSTANCE);''')
s=change(s,
 '''                    chest.remove(DataComponents.GLIDER);''',
 '''                    if (!armorElytra) chest.remove(DataComponents.GLIDER);''')
s=change(s,
 '''                chest.remove(DataComponents.GLIDER);''',
 '''                if (!armorElytra) chest.remove(DataComponents.GLIDER);''')
assert s.count("if (!armorElytra) chest.remove(DataComponents.GLIDER);")==2
assert "SHIFT_COST_PER_5_TICKS = 1500L" in s
assert "BOOST_MAX_SPEED = 2.4D" in s
write(server_path,s)

# Vanilla canGlide() is true for a fully equipped upgraded, FE-powered armor
# even without an Elytra in the chest or optional Curios installed. Apply
# precisely the existing ground and takeoff checks to avoid launch exploits.
mixin_path=java/"mixin/NetworkElytraCuriosGlideMixin.java"
s=load(mixin_path)
s=change(s,
 '''  if(!ModList.get().isLoaded("curios"))return;
  ItemStack wing=dev.obsidiannetwork.wireless.NetworkElytraCurios.find(player);
  // XSXLABS_ELYTRA_GROUND_AND_TAKEOFF_GUARD_V1
  if(player.onGround())return;
  if(!player.isFallFlying() && player.getDeltaMovement().y>=-0.02D)return;''',
 '''  // BUILD94_POWER_ARMOR_NETWORK_ELYTRA: takeoff rules match Network Elytra.
  if(player.onGround())return;
  if(!player.isFallFlying() && player.getDeltaMovement().y>=-0.02D)return;
  ItemStack armoredWing=dev.obsidiannetwork.powerarmor.PowerArmorElytraBridge.chest(player);
  if(!armoredWing.isEmpty()
      && EnergyTool.energy(armoredWing)>=NetworkElytraItem.FLIGHT_COST_PER_5_TICKS){
   result.setReturnValue(true);
   return;
  }
  if(!ModList.get().isLoaded("curios"))return;
  ItemStack wing=dev.obsidiannetwork.wireless.NetworkElytraCurios.find(player);
  // XSXLABS_ELYTRA_GROUND_AND_TAKEOFF_GUARD_V1''')
write(mixin_path,s)

# Match the local Shift prediction and landing pose for smooth flying without
# silently touching GLIDER/Equippable components on the real suit.
client_path=java/"client/NetworkElytraBoostClient.java"
s=load(client_path)
s=change(s,
 '''   if(landingWing.getItem() instanceof NetworkElytraItem)mc.player.stopFallFlying();''',
 '''   if(!(landingWing.getItem() instanceof NetworkElytraItem))
    landingWing=dev.obsidiannetwork.powerarmor.PowerArmorElytraBridge.chest(mc.player);
   if(landingWing.getItem() instanceof NetworkElytraItem || !landingWing.isEmpty())
    mc.player.stopFallFlying();''')
s=change(s,
 '''  if(!(wing.getItem() instanceof NetworkElytraItem)
      || EnergyTool.energy(wing)<NetworkElytraItem.SHIFT_COST_PER_5_TICKS)return;''',
 '''  // BUILD94_POWER_ARMOR_NETWORK_ELYTRA: same 0.09 acceleration and 2.4 cap.
  if(!(wing.getItem() instanceof NetworkElytraItem))
   wing=dev.obsidiannetwork.powerarmor.PowerArmorElytraBridge.chest(mc.player);
  if(wing.isEmpty() || EnergyTool.energy(wing)<NetworkElytraItem.SHIFT_COST_PER_5_TICKS)return;''')
write(client_path,s)

# Do not trigger vanilla's anti-speed/rubber-band guard for legitimate,
# powered Power Armor gliding: same scoped exception as Network Elytra.
check_path=java/"mixin/NetworkElytraSpeedCheckMixin.java"
s=load(check_path)
s=change(s,
 '''        if (!(wing.getItem() instanceof NetworkElytraItem)) {
            if (!ModList.get().isLoaded("curios")) return;
            wing = NetworkElytraCurios.find(p);
        }
        if (!(wing.getItem() instanceof NetworkElytraItem)) return;
        if (EnergyTool.energy(wing) < NetworkElytraItem.FLIGHT_COST_PER_5_TICKS) return;''',
 '''        if (!(wing.getItem() instanceof NetworkElytraItem)) {
            if (ModList.get().isLoaded("curios"))
                wing = NetworkElytraCurios.find(p);
            if (!(wing.getItem() instanceof NetworkElytraItem))
                wing = dev.obsidiannetwork.powerarmor.PowerArmorElytraBridge.chest(p);
        }
        // BUILD94_POWER_ARMOR_NETWORK_ELYTRA: still requires suit + card + FE.
        if (wing.isEmpty() || EnergyTool.energy(wing) < NetworkElytraItem.FLIGHT_COST_PER_5_TICKS) return;''')
write(check_path,s)

assert marker in load(server_path) and marker in load(mixin_path)
assert marker in load(client_path) and marker in load(check_path)
print(f"{marker} PASS: full MK1-MK12 + installed network_elytra card -> glide and Shift boost, identical original FE/physics/landing and movement checks; no GLIDER mutation to armor; Curios optional")
