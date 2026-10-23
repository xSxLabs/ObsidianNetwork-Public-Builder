#!/usr/bin/env python3
"""Build 65: restore stable persistent suit, fix cancelled right-click, visible animations.

Run after the existing GeckoLib/Build62/Build64 overlays.
Never touch the successful Apotheosis data, suit FE/upgrades or recovery saves.
"""
import os
from pathlib import Path
j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def edit(file,old,new):
 p=j/file
 src=p.read_text(encoding="utf-8")
 assert src.count(old)==1, "BUILD65 source drift: "+file+" count="+str(src.count(old))+" anchor="+old[:100]
 p.write_text(src.replace(old,new,1),encoding="utf-8")

# Preserve the successful anti-duplication transaction from Build62 but
# do not put all four physical stacks in the new custom GeoEntity: that
# regression made the standing suit disappear. Vanilla ArmorStand was the
# stable world owner. Retain existing decorative GeckoLib entities only for
# the short animation and NEVER make the real ArmorStand invisible.
edit("powerarmor/PowerArmorSuitWorld.java",
'''  // mk2 was already validated at the start of spawn(); reuse that value.
  var type=mk2?dev.obsidiannetwork.ObsidianNetwork.POWER_ARMOR_WORLD_MK2.get()
              :dev.obsidiannetwork.ObsidianNetwork.POWER_ARMOR_WORLD_MK1.get();
  PowerArmorStand stand=new PowerArmorStand(type,level);
  stand.setPos(pos.getX()+0.5D,pos.getY(),pos.getZ()+0.5D);''',
'''  // Reliable vanilla world owner for all four physical items; GeckoLib is
  // visual-only during the twenty-tick transition and cannot despawn the suit.
  ArmorStand stand=new ArmorStand(level,pos.getX()+0.5D,pos.getY(),pos.getZ()+0.5D);''')

# BUG: server/client shared event previously cancelled client clicks before
# Minecraft dispatched the standard entity-interact packet. Ownership markers
# also do not need to be present on the client. Only cancel on SERVER.
world=j/"powerarmor/PowerArmorSuitWorld.java"
s=world.read_text(encoding="utf-8")
old='''  event.setCanceled(true);
  event.setCancellationResult(InteractionResult.SUCCESS);
  if(event.getHand()==net.minecraft.world.InteractionHand.MAIN_HAND)
   enter(stand,event.getEntity());'''
new='''  // Do NOT cancel on the client: Minecraft must send its vanilla entity
  // interaction packet. If the packet is eaten by an ArmorStand part hitbox,
  // PowerArmorEnterPayload's fallback performs the same server-side checks.
  if(event.getEntity() instanceof ServerPlayer player){
   event.setCanceled(true);
   event.setCancellationResult(InteractionResult.SUCCESS);
   if(event.getHand()==net.minecraft.world.InteractionHand.MAIN_HAND)
    enter(stand,player);
  }'''
assert s.count(old)==2,"BUILD65 expected exactly two native interaction handlers"
s=s.replace(old,new)
world.write_text(s,encoding="utf-8")

# The old visual GeckoLib asset loader and controller remain registered.
# If it spawns, render the animation IN ADDITION to the always-visible suit;
# if a resource pack/renderer fails, player still sees their real equipment.
edit("powerarmor/PowerArmorSuitWorld.java",
'''  // The four actual ItemStacks never enter the cosmetic GeckoLib entity.
  stand.setInvisible(true);
  return new Animation(stand,20,entering,visual);''',
'''  // Keep the physical suit visible and pickable even if the cosmetic
  // GeckoLib overlay fails. Never hand real equipment to a visual entity.
  stand.setInvisible(false);
  return new Animation(stand,20,entering,visual);''')

# The former pose method was an all-zero no-op, hiding the mechanical
# transition whenever GeckoLib's temporary visual did not render.
edit("powerarmor/PowerArmorSuitWorld.java",
''' private static void pose(ArmorStand stand,int progress,boolean entering){
  // Keep vanilla suit neutral; GeckoLib performs all hinged bone movements.
  stand.setLeftArmPose(new net.minecraft.core.Rotations(0F,0F,0F));
  stand.setRightArmPose(new net.minecraft.core.Rotations(0F,0F,0F));
  stand.setHeadPose(new net.minecraft.core.Rotations(0F,0F,0F));
  stand.setLeftLegPose(new net.minecraft.core.Rotations(0F,0F,0F));
  stand.setRightLegPose(new net.minecraft.core.Rotations(0F,0F,0F));
  stand.setBodyPose(new net.minecraft.core.Rotations(0F,0F,0F));
 }''',
''' private static void pose(ArmorStand stand,int progress,boolean entering){
  if(stand.isRemoved())return;
  float t=Math.max(0F,Math.min(1F,progress/20F));
  float open=entering?1F-t:t;
  float spread=55F*open;
  // Visible server-synchronized fallback, independent of GeckoLib's mesh.
  stand.setLeftArmPose(new net.minecraft.core.Rotations(-15F*open,0F,-spread));
  stand.setRightArmPose(new net.minecraft.core.Rotations(-15F*open,0F,spread));
  stand.setHeadPose(new net.minecraft.core.Rotations(-28F*open,0F,0F));
  stand.setLeftLegPose(new net.minecraft.core.Rotations(0F,0F,-12F*open));
  stand.setRightLegPose(new net.minecraft.core.Rotations(0F,0F,12F*open));
  stand.setBodyPose(new net.minecraft.core.Rotations(0F,0F,0F));
 }''')

# Exit-created suit MUST be visible on the tick it spawns; do not wait 20
# ticks for a renderer or animation cleanup to decide what the player sees.
edit("powerarmor/PowerArmorSuitWorld.java",
'''  if(!level.addFreshEntity(stand))return null;
  pose(stand,20,false);''',
'''  if(!level.addFreshEntity(stand))return null;
  stand.setInvisible(false);
  pose(stand,0,false);''')

# Animation sequencing previously used a reversed open/close choice.
# 'entering' means opening, 'exiting' means closing, per GeckoLib assets.
v=j/"powerarmor/PowerArmorVisualEntity.java"
visual=v.read_text(encoding="utf-8")
anchor='''entityData.get(ENTERING)?"animation.power_armor.close":"animation.power_armor.open"'''
assert visual.count(anchor)==1
visual=visual.replace(anchor,'''entityData.get(ENTERING)?"animation.power_armor.open":"animation.power_armor.close"''',1)
v.write_text(visual,encoding="utf-8")

# Critical fallback when Minecraft returns BLOCK instead of ENTITY hit for
# an armor stand. Send an intent (id=-1); server validates owner, range, and
# where the player is actually LOOKING, so ordinary right-click stays safe.
client="powerarmor/PowerArmorEnterClient.java"
edit(client,
'''  if(!(mc.hitResult instanceof net.minecraft.world.phys.EntityHitResult hit))return;
  if(!(hit.getEntity() instanceof ArmorStand stand))return;
  // Only server may check ownership, valid slots and pending animations.
  net.neoforged.neoforge.client.network.ClientPacketDistributor.sendToServer(
    new PowerArmorEnterPayload(stand.getId()));''',
'''  if(mc.hitResult instanceof net.minecraft.world.phys.EntityHitResult hit
      && hit.getEntity() instanceof ArmorStand stand){
   net.neoforged.neoforge.client.network.ClientPacketDistributor.sendToServer(
     new PowerArmorEnterPayload(stand.getId()));
  }else{
   // Trigger a server-side look-target lookup, not client entity tags.
   net.neoforged.neoforge.client.network.ClientPacketDistributor.sendToServer(
     new PowerArmorEnterPayload(-1));
  }''')

edit("powerarmor/PowerArmorSuitWorld.java",
''' public static void tryEnter(ServerPlayer player,int entityId){
  Entity entity=player.level().getEntity(entityId);
  if(!(entity instanceof ArmorStand stand))return;
  if(stand.isRemoved()||!mine(stand,player))return;
  if(player.distanceToSqr(stand)>36.0D)return;
  enter(stand,player);
 }''',
''' public static void tryEnter(ServerPlayer player,int entityId){
  Entity entity=null;
  if(entityId<0){
   var eye=player.getEyePosition();
   var look=player.getLookAngle();
   List<ArmorStand> candidates=player.level().getEntitiesOfClass(
      ArmorStand.class,player.getBoundingBox().inflate(4D),
      stand->mine(stand,player)&&full(stand)&&!stand.isRemoved()
        &&eye.distanceToSqr(stand.getBoundingBox().getCenter())<=20D
        &&stand.getBoundingBox().getCenter().subtract(eye).normalize().dot(look)>0.90D);
   if(candidates.size()!=1)return;
   entity=candidates.get(0);
  }else{
   entity=player.level().getEntity(entityId);
  }
  if(!(entity instanceof ArmorStand stand))return;
  if(stand.isRemoved()||!mine(stand,player)||!full(stand))return;
  if(player.distanceToSqr(stand)>20D)return;
  enter(stand,player);
 }''')

# A status command for loaded owned suits and currently pending animation;
# unlike an execute/say command it ALWAYS emits a useful diagnostic message.
command=j/"powerarmor/PowerArmorCommands.java"
s=command.read_text(encoding="utf-8")
anchor='''   .then(Commands.literal("compat").executes(c->apotheosis(c.getSource().getPlayerOrException())))'''
assert s.count(anchor)==1
s=s.replace(anchor,anchor+'\n   .then(Commands.literal("status").executes(c->PowerArmorSuitWorld.status(c.getSource().getPlayerOrException())))',1)
command.write_text(s,encoding="utf-8")
world=j/"powerarmor/PowerArmorSuitWorld.java"
s=world.read_text(encoding="utf-8")
idx=s.rfind("\n}")
assert idx>0
s=s[:idx]+'''
 /** One-line health report with suit UUID/position and animation state. */
 public static int status(ServerPlayer player){
  var nearby=player.level().getEntitiesOfClass(ArmorStand.class,
      player.getBoundingBox().inflate(32D),stand->mine(stand,player));
  player.sendSystemMessage(Component.literal(
    "Power Armor | equipped="+PowerArmorRuntime.full(player)+
    " owned_stands="+nearby.size()+" transition="+ACTIVE.containsKey(player.getUUID())));
  for(ArmorStand stand:nearby){
   player.sendSystemMessage(Component.literal(
     "Suit "+stand.getUUID()+" xyz="+stand.blockPosition()+
     " complete="+full(stand)+" invisible="+stand.isInvisible()));
  }
  return 1;
 }
'''+s[idx:]
world.write_text(s,encoding="utf-8")

# Static assertions on final reconstructed source rather than just the
# overlay's source text, to detect generator collisions immediately.
w=world.read_text(encoding="utf-8")
assert "ArmorStand stand=new ArmorStand(level,pos.getX()" in w
assert "PowerArmorStand stand=new PowerArmorStand" not in w
assert "if(event.getEntity() instanceof ServerPlayer player)" in w
assert w.count("event.setCanceled(true)")>=2
assert "stand.setInvisible(true);" not in w
assert "new PowerArmorEnterPayload(-1)" in (j/client).read_text(encoding="utf-8")
assert "Commands.literal(\"status\")" in command.read_text(encoding="utf-8")
print("BUILD65_FALLBACK_WORLD PASS: real world stand visible, server-only cancel, geometry-safe entry, GeckoLib visual optional, rollback unchanged")
