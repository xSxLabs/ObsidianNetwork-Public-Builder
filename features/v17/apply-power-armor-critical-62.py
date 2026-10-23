#!/usr/bin/env python3
"""Build 62: fix in-game dupe, missing entering and absent GeckoLib transitions.

Generated-source overlay: must run AFTER Build 59 / Build 61, preserving
existing items, FE, upgrade components and previous-armor SavedData.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
W=J/"powerarmor/PowerArmorSuitWorld.java"
C=J/"powerarmor/PowerArmorEnterClient.java"
s=W.read_text(encoding="utf-8")

# Remove the suit from the wearer BEFORE creating a visible world copy. Keep
# the original docking, facing, stand-owner and GeckoLib spawn code unchanged.
beg=s.index(" private static boolean spawn(ServerPlayer player,List<ItemStack> suit){")
end=s.index(" /** Exit never creates or places an Armor Station. */",beg)
region=s[beg:end]
for old,new in [
 ("private static boolean spawn(","private static ArmorStand spawn("),
 ("if(suit.size()!=4)return false;","if(suit.size()!=4)return null;"),
 ("if(!PowerArmorRuntime.piece(suit.get(i),i,mk2))return false;","if(!PowerArmorRuntime.piece(suit.get(i),i,mk2))return null;"),
 ("if(pos==null){","if(pos==null){"),
 ("  return false;","  return null;"),
 ("if(!level.addFreshEntity(stand))return false;","if(!level.addFreshEntity(stand))return null;"),
 ("  return true;","  return stand;")
]:
 if old==new:continue
 assert old in region,"BUILD62 spawn drift: "+old
 region=region.replace(old,new)
assert region.count("return stand;")==1 and "return false;" not in region
s=s[:beg]+region+s[end:]

# Full tier validation. Never restore a stale 'previous armor' containing an
# entirely separate MK1/MK2 suit; that was a historical duplication path.
beg=s.index(" public static int exit(ServerPlayer player){")
end=s.index(" // Armor stands normally consume",beg)
old=s[beg:end]
assert "if(!spawn(player,suit))return 0;" in old
assert "backup==null?ItemStack.EMPTY:backup.previous().get(i).copy()" in old
new=''' public static int exit(ServerPlayer player){
  if(!PowerArmorRuntime.full(player)){
   player.sendSystemMessage(Component.literal(
     "Power Armor: equip a complete matching MK1/MK2 suit first."));
   return 0;
  }
  if(ACTIVE.containsKey(player.getUUID()))return 0;
  ArmorLoadoutData saved=ArmorLoadoutData.get(player.level().getServer());
  var backup=saved.get(player);
  if(backup!=null){
   if(backup.previous().size()!=4){
    player.sendSystemMessage(Component.literal("Power Armor: backup invalid; no suit moved."));
    return 0;
   }
   // Never promote an old power-suit backup into a second live suit.
   for(ItemStack prior:backup.previous())if(prior.getItem() instanceof PowerArmorItem){
    player.sendSystemMessage(Component.literal(
     "Power Armor: stale power-armor backup detected. Resolve backup before exiting."));
    return 0;
   }
  }
  List<ItemStack> worn=new ArrayList<>(4);
  for(EquipmentSlot slot:PowerArmorRuntime.SLOTS)worn.add(player.getItemBySlot(slot).copy());
  // Critical invariant: zero world copies exist while the player owns the
  // source items. Clear them and verify before creating any world stand.
  for(EquipmentSlot slot:PowerArmorRuntime.SLOTS)player.setItemSlot(slot,ItemStack.EMPTY);
  for(int i=0;i<4;i++)if(!player.getItemBySlot(PowerArmorRuntime.SLOTS[i]).isEmpty()){
   for(int k=0;k<4;k++)player.setItemSlot(PowerArmorRuntime.SLOTS[k],worn.get(k));
   player.sendSystemMessage(Component.literal("Power Armor: slot clear failed, exit aborted."));
   return 0;
  }
  ArmorStand stand=spawn(player,worn);
  if(stand==null){
   for(int i=0;i<4;i++)player.setItemSlot(PowerArmorRuntime.SLOTS[i],worn.get(i));
   return 0;
  }
  // Restore the normal former loadout only after successful creation.
  if(backup!=null){
   for(int i=0;i<4;i++)
    player.setItemSlot(PowerArmorRuntime.SLOTS[i],backup.previous().get(i).copy());
  }
  boolean valid=true;
  for(int i=0;i<4;i++){
   ItemStack required=backup==null?ItemStack.EMPTY:backup.previous().get(i);
   if(!ItemStack.matches(player.getItemBySlot(PowerArmorRuntime.SLOTS[i]),required))
    valid=false;
  }
  if(!valid){
   Animation active=ACTIVE.remove(player.getUUID());
   if(active!=null)cleanup(active);
   stand.discard();
   for(int i=0;i<4;i++)player.setItemSlot(PowerArmorRuntime.SLOTS[i],worn.get(i));
   player.sendSystemMessage(Component.literal(
    "Power Armor: post-transfer verification failed; exit reverted."));
   return 0;
  }
  if(backup!=null)saved.finish(player);
  player.sendSystemMessage(Component.literal(
   "Power Armor disengaged. Right-click the standing suit to enter."));
  return 1;
 }
'''
s=s[:beg]+new+s[end:]

# Entering currently has two separate event routes AND client network fallback.
# Guard the actual input before starting animation, and after 20 ticks MOVE
# the only four ItemStacks back, checking and reverting if anything failed.
beg=s.index(" private static void finishEntering(ArmorStand stand,ServerPlayer player){")
end=s.index(" @SubscribeEvent public static void animationLogout(",beg)
old=s[beg:end]
assert "saved.save(player,original)" in old
new=''' private static void finishEntering(ArmorStand stand,ServerPlayer player){
  if(stand.isRemoved()||!mine(stand,player)||!full(stand))return;
  if(PowerArmorRuntime.full(player))return;
  ArmorLoadoutData saved=ArmorLoadoutData.get(player.level().getServer());
  if(saved.has(player))return;
  List<ItemStack> original=new ArrayList<>(4);
  List<ItemStack> suit=new ArrayList<>(4);
  for(EquipmentSlot slot:PowerArmorRuntime.SLOTS){
   original.add(player.getItemBySlot(slot).copy());
   suit.add(stand.getItemBySlot(slot).copy());
  }
  // Keep a world-persistent backup of original normal armor.
  if(!saved.save(player,original))return;
  // The stand must relinquish ownership of all four stacks before the
  // player obtains them. No real ItemStack is ever on a GeckoLib visual.
  for(EquipmentSlot slot:PowerArmorRuntime.SLOTS)stand.setItemSlot(slot,ItemStack.EMPTY);
  for(int i=0;i<4;i++)player.setItemSlot(PowerArmorRuntime.SLOTS[i],suit.get(i));
  boolean valid=true;
  for(int i=0;i<4;i++){
   if(!ItemStack.matches(player.getItemBySlot(PowerArmorRuntime.SLOTS[i]),suit.get(i))
      ||!stand.getItemBySlot(PowerArmorRuntime.SLOTS[i]).isEmpty())valid=false;
  }
  if(!valid){
   for(int i=0;i<4;i++){
    player.setItemSlot(PowerArmorRuntime.SLOTS[i],original.get(i));
    stand.setItemSlot(PowerArmorRuntime.SLOTS[i],suit.get(i));
   }
   saved.finish(player);
   player.sendSystemMessage(Component.literal("Power Armor: entry verification failed; reverted."));
   return;
  }
  stand.discard();
  player.sendSystemMessage(Component.literal(
   "Power Armor engaged. Press the configurable Exit key to leave."));
 }
'''
s=s[:beg]+new+s[end:]

# Every transition must advance and run even when GeckoLib rendering is not
# available. Retain old visual entity but add a server-driven fallback pose,
# for a visible mechanical movement instead of an entirely static shell.
old='''  // Bone pose interpolations are now client-side GeckoLib animations.'''
assert s.count(old)==1
s=s.replace(old,'''  // GeckoLib drives real articulated bones. This synchronized ArmorStand
  // pose is an additional fallback for clients with failed mesh rendering.
  pose(stand,t,animation.entering());''',1)

# The client can send a packet before Minecraft's entity interaction pipeline
# discards it (e.g. invulnerable ArmorStand with custom renderer).
W.write_text(s,encoding="utf-8")
c=C.read_text(encoding="utf-8")
needle=''' @SubscribeEvent(priority=net.neoforged.bus.api.EventPriority.HIGHEST,receiveCanceled=true)
 public static void interact(PlayerInteractEvent.EntityInteractSpecific event){'''
assert c.count(needle)==1
before=''' @SubscribeEvent(priority=net.neoforged.bus.api.EventPriority.HIGHEST,receiveCanceled=true)
 public static void onUseKey(net.neoforged.neoforge.client.event.InputEvent.InteractionKeyMappingTriggered event){
  if(!event.isUseItem()||event.getHand()!=InteractionHand.MAIN_HAND)return;
  var mc=net.minecraft.client.Minecraft.getInstance();
  if(mc.player==null||mc.screen!=null)return;
  if(!(mc.hitResult instanceof net.minecraft.world.phys.EntityHitResult hit))return;
  if(!(hit.getEntity() instanceof ArmorStand stand))return;
  // Only server may check ownership, valid slots and pending animations.
  net.neoforged.neoforge.client.network.ClientPacketDistributor.sendToServer(
    new PowerArmorEnterPayload(stand.getId()));
 }
'''
c=c.replace(needle,before+needle)
C.write_text(c,encoding="utf-8")

# Transient GeckoLib silhouettes should never swallow an interaction; the
# permanent suit is a vanilla ArmorStand whose right-click packet is validated.
v=J/"powerarmor/PowerArmorVisualEntity.java"
visual=v.read_text(encoding="utf-8")
assert "public boolean isPickable(){return false;}" in visual
# Ensure no phantom equipment is given to the cosmetic renderer.
assert "setItemSlot(" not in visual

assert "ArmorStand stand=spawn(player,worn);" in s
assert "if(!ItemStack.matches" in s
assert "for(EquipmentSlot slot:PowerArmorRuntime.SLOTS)stand.setItemSlot(slot,ItemStack.EMPTY);" in s
assert "if(PowerArmorRuntime.full(player))return;" in s
assert "onUseKey(net.neoforged.neoforge.client.event.InputEvent.InteractionKeyMappingTriggered" in c
print("BUILD62_TRANSFERS_AND_GECKOLIB PASS: remove-before-world-spawn; verified rollback; validated stand-to-player transfer; early right-click; animated transition")
