#!/usr/bin/env python3
"""v1.7.2: Create moving contraption support for persistent Power Armor stands.
No mandatory Create classes in bytecode. Moves ENTITY, never its equipment.
"""
import os
from pathlib import Path
root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/powerarmor"
p=root/"PowerArmorCreatePlatformSupport.java"
assert not p.exists()
p.write_text(r'''package dev.obsidiannetwork.powerarmor;
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
import net.neoforged.neoforge.event.tick.EntityTickEvent;

/** V172_CREATE_MOVING_PLATFORM: Create Elevator + Mechanical Piston.
 * Stationary persistent ArmorStands have noGravity, so vanilla cannot follow
 * a platform when it goes DOWN. Move the original stand with the platform
 * WITHOUT cloning, mounting, deserializing or touching any of its real armor.
 * Works with and without Create installed (reflection, no hard linkage).
 */
@EventBusSubscriber(modid="obsidiannetwork")
public final class PowerArmorCreatePlatformSupport {
 private static final String SUIT="xsxlabs_power_armor_suit_v17";
 private record Follow(UUID carrier,Vec3 anchor,Vec3 suitPos,long seen){}
 private static final Map<UUID,Follow> TRACK=new HashMap<>();
 private PowerArmorCreatePlatformSupport(){}
 private static boolean isCreateCarrier(Entity e){
  Class<?> c=e.getClass();
  while(c!=null){
   if(c.getName().equals("com.simibubi.create.content.contraptions.AbstractContraptionEntity"))
    return true;
   c=c.getSuperclass();
  }
  return false;
 }
 private static boolean supports(Entity vehicle,ArmorStand suit){
  // Only actual platform blocks, never entire moving contraption AABB.
  // Unpowered / unloaded Create is never a hard dependency.
  try{
   // DEDICATED_SERVER_CREATE_SAFE_HOTFIX: getMethod() enumerates unrelated
   // Create method signatures and can resolve client-only PoseStack on servers.
   // Resolve ONLY the exact server-side descriptors through MethodHandles.
   Class<?> type=Class.forName("com.simibubi.create.content.contraptions.Contraption",
       false,vehicle.getClass().getClassLoader());
   MethodHandle get=MethodHandles.publicLookup().findVirtual(vehicle.getClass(),
       "getContraption",MethodType.methodType(type));
   Object contraption=get.invoke(vehicle);
   if(contraption==null)return false;
   MethodHandle getBlocks=MethodHandles.publicLookup().findVirtual(contraption.getClass(),
       "getBlocks",MethodType.methodType(Map.class));
   Object map=getBlocks.invoke(contraption);
   if(!(map instanceof Map<?,?> blocks))return false;
   MethodHandle toWorld=MethodHandles.publicLookup().findVirtual(vehicle.getClass(),
       "toGlobalVector",MethodType.methodType(Vec3.class,Vec3.class,float.class));
   int scanned=0;
   for(Object local:blocks.keySet()){
    if(!(local instanceof BlockPos block))continue;
    if(++scanned>16384)return false; // no unbounded server tick work
    Vec3 surface=(Vec3)toWorld.invoke(vehicle,
       new Vec3(block.getX()+.5D,block.getY()+1D,block.getZ()+.5D),1F);
    double dx=surface.x-suit.getX(),dz=surface.z-suit.getZ();
    if(dx*dx+dz*dz>.64D)continue;
    // Detect foot contact on a 1-block surface. Do not attach to a wall,
    // multiple floors above or a passing moving platform.
    if(Math.abs(surface.y-suit.getY())<.44D)return true;
   }
  }catch(Throwable failure){
   // Optional Create absent, incompatible or using a client-only method:
   // fail closed for this attachment, never crash the dedicated server.
   if(failure instanceof VirtualMachineError fatal)throw fatal;
   if(failure instanceof ThreadDeath fatal)throw fatal;
  }
  return false;
 }
 private static Entity find(ServerLevel world,ArmorStand suit){
  AABB area=suit.getBoundingBox().inflate(2.5D,3D,2.5D);
  for(Entity e:world.getEntitiesOfClass(Entity.class,area,
      entity->isCreateCarrier(entity)&&!entity.isRemoved()))
   if(supports(e,suit))return e;
  return null;
 }
 @SubscribeEvent public static void onSuitTick(EntityTickEvent.Post event){
  if(!(event.getEntity() instanceof ArmorStand suit)
      ||!(suit.level() instanceof ServerLevel world)
      ||!suit.entityTags().contains(SUIT)||!PowerArmorSuitWorld.full(suit))return;
  UUID id=suit.getUUID();
  Follow old=TRACK.get(id);
  Entity carrier=null;
  if(old!=null){
   carrier=world.getEntity(old.carrier());
   if(carrier==null||carrier.isRemoved()||!isCreateCarrier(carrier))
    carrier=null;
  }
  if(carrier==null){
   carrier=find(world,suit);
   if(carrier==null){TRACK.remove(id);return;}
   TRACK.put(id,new Follow(carrier.getUUID(),carrier.position(),suit.position(),world.getGameTime()));
   return;
  }
  Vec3 delta=carrier.position().subtract(old.anchor());
  if(delta.lengthSqr()>.0000001D&&delta.lengthSqr()<4D){
   Vec3 target=old.suitPos().add(delta);
   // Create's own collision handler may already have moved the stand.
   // Avoid applying the same platform displacement twice.
   if(suit.position().distanceToSqr(target)>.0004D){
    // Do not drag unrelated armor across the world: must remain inside
    // the moving contraption's expanded entity bounds.
    if(carrier.getBoundingBox().inflate(2.5D,2.5D,2.5D).contains(target))
     suit.setPos(target.x,target.y,target.z);
   }
   if(suit.position().distanceToSqr(old.suitPos())>.00001D){
    // The saved cross-dimensional recall coordinate follows the moved
    // physical stand, never an earlier platform stop.
    UUID owner=null;
    for(String tag:suit.entityTags())if(tag.startsWith("xsxlabs_power_armor_owner_")){
     try{owner=UUID.fromString(tag.substring("xsxlabs_power_armor_owner_".length()));}
     catch(IllegalArgumentException ignored){}
     break;
    }
    if(owner!=null)PowerArmorRecallIndex.get(world.getServer()).index(suit,world,owner);
   }
  }
  // When stationary: verify surface periodically, so armor can be removed
  // from the lift without remaining bound to an unrelated Create contraption.
  if(world.getGameTime()%20L==0L&&!supports(carrier,suit)){
   TRACK.remove(id);
   return;
  }
  TRACK.put(id,new Follow(carrier.getUUID(),carrier.position(),suit.position(),world.getGameTime()));
  if(TRACK.size()>2048)TRACK.entrySet().removeIf(entry->world.getGameTime()-entry.getValue().seen()>1200L);
 }
}
''',encoding="utf-8")
print("V172_CREATE_MOVING_PLATFORM PASS: optional Create support, moves real suit with elevator and mechanical piston")
