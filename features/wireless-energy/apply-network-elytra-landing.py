#!/usr/bin/env python3
"""Build 377: ground/launch guards for the powered Network Elytra, without editing the meter."""
import os
from pathlib import Path
root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
elytra=root/"item/NetworkElytraItem.java"
mixin=root/"mixin/NetworkElytraCuriosGlideMixin.java"
client=root/"client/NetworkElytraBoostClient.java"
sources={p:p.read_text(encoding="utf-8") for p in (elytra,mixin,client)}
marker="XSXLABS_ELYTRA_GROUND_AND_TAKEOFF_GUARD_V1"
assert all(marker not in s for s in sources.values()), "Already patched"
def once(text,old,new,what):
 assert text.count(old)==1, "Fail-closed Elytra "+what+" source changed: "+str(text.count(old))
 return text.replace(old,new,1)

# Server: a charged glider never receives Shift acceleration while grounded
# and cannot remain in the fall-flying pose after physical contact.
server=sources[elytra]
server=once(server,
 '''        if (!player.isFallFlying()) return;
        boolean boosting = player.isShiftKeyDown() && energy >= SHIFT_COST_PER_5_TICKS;''',
 '''        // XSXLABS_ELYTRA_GROUND_AND_TAKEOFF_GUARD_V1: landing always wins.
        if (player.onGround()) {
            if (player.isFallFlying()) player.stopFallFlying();
            return;
        }
        if (!player.isFallFlying()) return;
        boolean boosting = player.isShiftKeyDown() && energy >= SHIFT_COST_PER_5_TICKS;''',
 "server landing gate")

# Curios grant must never override grounded vanilla logic. In addition, on
# first jump's upward impulse the Curios fallback must NOT force a glide.
# Once already flying, rising under FE-powered boost remains valid.
mix=sources[mixin]
mix=once(mix,
 '''  if(wing.getItem() instanceof NetworkElytraItem
     && EnergyTool.energy(wing)>=NetworkElytraItem.FLIGHT_COST_PER_5_TICKS)
   result.setReturnValue(true);''',
 '''  // XSXLABS_ELYTRA_GROUND_AND_TAKEOFF_GUARD_V1
  if(player.onGround())return;
  if(!player.isFallFlying() && player.getDeltaMovement().y>=-0.02D)return;
  if(wing.getItem() instanceof NetworkElytraItem
     && EnergyTool.energy(wing)>=NetworkElytraItem.FLIGHT_COST_PER_5_TICKS)
   result.setReturnValue(true);''',
 "Curios first-jump and landing gate")

# Client: do not simulate any Shift acceleration at ground contact. Clear a
# lingering pose once grounded so the local camera returns immediately.
cl=sources[client]
cl=once(cl,
 '''  if(mc.player==null || !mc.player.isFallFlying() || !mc.options.keyShift.isDown())return;
  ItemStack wing=mc.player.getItemBySlot(EquipmentSlot.CHEST);''',
 '''  if(mc.player==null)return;
  // XSXLABS_ELYTRA_GROUND_AND_TAKEOFF_GUARD_V1
  if(mc.player.onGround() && mc.player.isFallFlying()){
   ItemStack landingWing=mc.player.getItemBySlot(EquipmentSlot.CHEST);
   if(!(landingWing.getItem() instanceof NetworkElytraItem)
      && net.neoforged.fml.ModList.get().isLoaded("curios"))
    landingWing=dev.obsidiannetwork.wireless.NetworkElytraCurios.find(mc.player);
   if(landingWing.getItem() instanceof NetworkElytraItem)mc.player.stopFallFlying();
   return;
  }
  if(!mc.player.isFallFlying() || !mc.options.keyShift.isDown())return;
  ItemStack wing=mc.player.getItemBySlot(EquipmentSlot.CHEST);''',
 "client landing gate")

# All source-shape validation above completes BEFORE publishing any mutation.
for path,text in ((elytra,server),(mixin,mix),(client,cl)):
 assert text.count(marker)==1, "Guard not installed in "+str(path)
 path.write_text(text,encoding="utf-8")
print("ELYTRA_GROUND_TAKEOFF_V1 PASS: early Curios gate, server/client landing stop; FE and boost rates unchanged")
