#!/usr/bin/env python3
"""v1.7.2: transparent Create moving-platform carrier for real standing Power Armor.

No special blocks, anchors or player inputs. Never rides/serializes/transfers
ItemStacks. Pure motion integration when Create is installed and a moving
contraption actually supports a parked suit.
"""
import os
from pathlib import Path
j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/powerarmor"
target=j/"PowerArmorCreateCarrier.java"
assert not target.exists()
target.write_text(r'''package dev.obsidiannetwork.powerarmor;

import java.lang.invoke.MethodHandle;
import java.lang.invoke.MethodHandles;
import java.lang.invoke.MethodType;
import java.util.*;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.EntityLeaveLevelEvent;
import net.neoforged.neoforge.event.tick.EntityTickEvent;

/**
 * BUILD138_CREATE_MOVING_PLATFORM_COMPAT
 *
 * Optional runtime integration with the ordinary Create elevator, mechanical
 * piston and other translation contraptions. No extra block, no Create hard
 * dependency, no change to the real suit's inventory, ownership or backup.
 * The persistent ArmorStand stays the sole owner of the 4 ItemStacks.
 *
 * Attach only if there is a REAL Create contraption block directly beneath the
 * suit's feet. Preserve the original local-space coordinate while the platform
 * moves, including downwards when vanilla collisions cannot push an ArmorStand.
 */
@EventBusSubscriber(modid="obsidiannetwork")
public final class PowerArmorCreateCarrier {
 private static final String MARKER="xsxlabs_power_armor_suit_v17";
 private static final String OWNER="xsxlabs_power_armor_owner_";
 private static final String CREATE_CLASS_NAME=
   "com.simibubi.create.content.contraptions.AbstractContraptionEntity";
 private static final Map<UUID,Attachment> ATTACHED=new HashMap<>();
 private record Attachment(UUID contraption,Vec3 local){}
 // The base Create class has a CLIENT-ONLY abstract PoseStack method.
 // Never call Class#getMethod()/getMethods() on any Create entity.
 // Resolve exact SERVER API descriptors on the BASE class (not a subclass),
 // and cache the resulting handles for use during armor ticks.
 private record CreateApi(MethodHandle local,MethodHandle global,
                          MethodHandle contraption,MethodHandle blocks){}
 private static CreateApi API;
 private static boolean API_RESOLVED;
 private PowerArmorCreateCarrier(){}

 private static CreateApi api(Entity entity){
  if(API_RESOLVED)return API;
  API_RESOLVED=true;
  try{
   ClassLoader loader=entity.getClass().getClassLoader();
   Class<?> base=Class.forName(CREATE_CLASS_NAME,false,loader);
   Class<?> contraptionType=Class.forName(
       "com.simibubi.create.content.contraptions.Contraption",false,loader);
   if(!base.isInstance(entity))return null;
   MethodHandles.Lookup lookup=MethodHandles.publicLookup();
   MethodType transform=MethodType.methodType(Vec3.class,Vec3.class,float.class);
   API=new CreateApi(
       lookup.findVirtual(base,"toLocalVector",transform),
       lookup.findVirtual(base,"toGlobalVector",transform),
       lookup.findVirtual(base,"getContraption",MethodType.methodType(contraptionType)),
       lookup.findVirtual(contraptionType,"getBlocks",MethodType.methodType(Map.class)));
   return API;
  }catch(Throwable failure){
   if(failure instanceof VirtualMachineError fatal)throw fatal;
   if(failure instanceof ThreadDeath fatal)throw fatal;
   System.err.println("[ObsidianNetwork] Create armor platform API unavailable: "+
       failure.getClass().getSimpleName()+" "+failure.getMessage());
   return null;
  }
 }

 private static boolean isCreateContraption(Entity e){
  for(Class<?> t=e.getClass();t!=null;t=t.getSuperclass())
   if(CREATE_CLASS_NAME.equals(t.getName()))return true;
  return false;
 }
 private static Vec3 local(Entity contraption,Vec3 pos){
  try{
   CreateApi methods=api(contraption);
   if(methods==null)return null;
   return (Vec3)methods.local().invoke(contraption,pos,1.0F);
  }catch(Throwable failure){
   if(failure instanceof VirtualMachineError fatal)throw fatal;
   if(failure instanceof ThreadDeath fatal)throw fatal;
   return null;
  }
 }
 private static Vec3 global(Entity contraption,Vec3 pos){
  try{
   CreateApi methods=api(contraption);
   if(methods==null)return null;
   return (Vec3)methods.global().invoke(contraption,pos,1.0F);
  }catch(Throwable failure){
   if(failure instanceof VirtualMachineError fatal)throw fatal;
   if(failure instanceof ThreadDeath fatal)throw fatal;
   return null;
  }
 }
 private static boolean supports(Entity contraption,Vec3 localFeet){
  // Match actual moving contraption blocks, not just its (often huge) AABB.
  if(localFeet==null||!Double.isFinite(localFeet.x)
     ||!Double.isFinite(localFeet.y)||!Double.isFinite(localFeet.z))return false;
  BlockPos underneath=BlockPos.containing(localFeet.add(0D,-.125D,0D));
  if(Math.abs(localFeet.y-(underneath.getY()+1D))>.5D)return false;
  try{
   CreateApi methods=api(contraption);
   if(methods==null)return false;
   Object moving=methods.contraption().invoke(contraption);
   if(moving==null)return false;
   Object map=methods.blocks().invoke(moving);
   return map instanceof Map<?,?> blocks&&blocks.containsKey(underneath);
  }catch(Throwable failure){
   if(failure instanceof VirtualMachineError fatal)throw fatal;
   if(failure instanceof ThreadDeath fatal)throw fatal;
   return false;
  }
 }
 private static Entity find(ServerLevel level,UUID uuid,AABB nearby){
  for(Entity e:level.getEntitiesOfClass(Entity.class,nearby,
      candidate->candidate.getUUID().equals(uuid)&&isCreateContraption(candidate)))
   if(!e.isRemoved())return e;
  return null;
 }
 private static Attachment attach(ServerLevel level,ArmorStand stand){
  AABB nearby=stand.getBoundingBox().inflate(2.0D,3.0D,2.0D);
  for(Entity contraption:level.getEntitiesOfClass(Entity.class,nearby,
          PowerArmorCreateCarrier::isCreateContraption)){
   if(contraption.isRemoved())continue;
   Vec3 feet=local(contraption,stand.position());
   if(!supports(contraption,feet))continue;
   // Confirm forward and reverse transforms agree; don't snap from far away.
   Vec3 projected=global(contraption,feet);
   if(projected==null||projected.distanceToSqr(stand.position())>.25D)continue;
   return new Attachment(contraption.getUUID(),feet);
  }
  return null;
 }
 private static void track(ServerLevel level,ArmorStand stand){
  for(String tag:stand.entityTags())if(tag.startsWith(OWNER)){
   try{
    UUID owner=UUID.fromString(tag.substring(OWNER.length()));
    PowerArmorRecallIndex.get(level.getServer()).index(stand,level,owner);
   }catch(IllegalArgumentException ignored){}
   break;
  }
 }
 @SubscribeEvent public static void onTick(EntityTickEvent.Post event){
  if(!(event.getEntity() instanceof ArmorStand stand)
     ||!(stand.level() instanceof ServerLevel world)
     ||stand.isRemoved()||!stand.entityTags().contains(MARKER))return;
  UUID id=stand.getUUID();
  Attachment held=ATTACHED.get(id);
  if(held!=null){
   // A removed/disassembled Create contraption releases the suit naturally.
   Entity contraption=find(world,held.contraption(),
       stand.getBoundingBox().inflate(8.0D,8.0D,8.0D));
   if(contraption==null){
    ATTACHED.remove(id);
   }else{
    Vec3 dest=global(contraption,held.local());
    if(dest==null||!Double.isFinite(dest.x)||!Double.isFinite(dest.y)
       ||!Double.isFinite(dest.z)||dest.distanceToSqr(stand.position())>64D){
     ATTACHED.remove(id);
    }else{
     Vec3 delta=dest.subtract(stand.position());
     if(delta.lengthSqr()>1.0E-6D){
      // Never move through real world blocks; moving Create block shapes are
      // internal contraption geometry and deliberately NOT tested here.
      if(world.hasChunkAt(BlockPos.containing(dest))
         &&world.noCollision(stand,stand.getBoundingBox().move(delta))){
       stand.setPos(dest.x,dest.y,dest.z);
       track(world,stand);
      }else ATTACHED.remove(id);
     }
     return;
    }
   }
  }
  // Unattached stands need no work beyond nearby moving-contraption search.
  // Store only UUID/local transform: no items, NBT, forced chunks or mounts.
  Attachment next=attach(world,stand);
  if(next!=null)ATTACHED.put(id,next);
 }
 @SubscribeEvent public static void onLeave(EntityLeaveLevelEvent event){
  if(event.getEntity() instanceof ArmorStand stand
     &&stand.entityTags().contains(MARKER))ATTACHED.remove(stand.getUUID());
 }
}
''',encoding="utf-8")
print("BUILD138_CREATE_PLATFORM_AUTOMATIC PASS: no extra block; optional Create reflection; local support only; stored-world suit intact; recall location follows motion")
