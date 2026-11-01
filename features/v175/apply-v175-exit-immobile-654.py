#!/usr/bin/env python3
"""B654: never abort exit on player movement. Server holds the actual wearer at
the original exit position, client suppresses movement input immediately after
the server-synced exit preview appears. No invisibility, no early transfer.
The 64-tick opened-shell->real-world-suit handoff remains rollback-safe.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def edit(s,a,b,label):
 n=s.count(a)
 assert n==1,("B654_ANCHOR_DRIFT",label,n)
 return s.replace(a,b,1)
helper=J/"powerarmor/PowerArmorExitSequence650.java"
s=helper.read_text(encoding="utf8")
s=edit(s,"visual.beginPhase(7); // open fully, then hold until safe transfer",
'''visual.beginPhase(7); // open fully, then hold until safe transfer
  visual.setExitOwner654(p.getUUID()); // client receives actual lock owner via EntityData''',"owner")
s=edit(s,"PENDING.put(id,new Pending(visual,p.position(),p.tickCount+64));",
'''PENDING.put(id,new Pending(visual,p.position(),p.tickCount+64));
  // No visible step before opening. Freeze from the very first server tick.
  p.setDeltaMovement(Vec3.ZERO);''',"initial")
s=edit(s,''' @SubscribeEvent public static void tick(PlayerTickEvent.Post e){''',
''' /** Both logical sides see the client preview; server is authoritative for
  * coordinates. Never cancel an ordinary exit just because W/A/S/D was held.
  * PlayerTick Pre prevents movement during the tick; Post corrects any other
  * velocity or vehicle/physics movement before it can leak into the handoff.
  */
 private static void hold(ServerPlayer p,Pending x){
  p.setDeltaMovement(Vec3.ZERO);
  Vec3 origin=x.start();
  if(p.position().distanceToSqr(origin)>.000001D)
   p.setPos(origin.x,origin.y,origin.z);
 }
 @SubscribeEvent public static void pre(PlayerTickEvent.Pre e){
  if(!(e.getEntity() instanceof ServerPlayer p))return;
  Pending x=PENDING.get(p.getUUID());
  if(x==null)return;
  if(!p.isAlive()||!PowerArmorRuntime.full(p)||x.preview().isRemoved()){
   cancel(p);return;
  }
  hold(p,x);
 }
 @SubscribeEvent public static void tick(PlayerTickEvent.Post e){''',"pre")
s=edit(s,'''  if(!p.isAlive()||!PowerArmorRuntime.full(p)||pending.preview().isRemoved()
     ||p.position().distanceToSqr(pending.start())>1.0D){cancel(p);return;}
  if(p.tickCount<pending.deadline())return;''',
'''  if(!p.isAlive()||!PowerArmorRuntime.full(p)||pending.preview().isRemoved()){
   cancel(p);return;
  }
  // Movement is NOT an abort condition. Restore exact entry position even
  // if the client sent a movement packet just before this event.
  hold(p,pending);
  if(p.tickCount<pending.deadline())return;''',"no_movement_cancel")
assert "distanceToSqr(pending.start())>1.0D" not in s
assert "p.tickCount+64" in s
assert "PowerArmorSuitWorld.exit(p)" in s
assert "setInvisible(" not in s
helper.write_text(s,encoding="utf8")
visual=J/"powerarmor/PowerArmorVisualEntity.java"
s=visual.read_text(encoding="utf8")
s=edit(s,''' private final AnimatableInstanceCache geoCache=GeckoLibUtil.createInstanceCache(this);''',
''' // B654 ownership is synced to the client, preventing nearby players
 // from being movement-locked by somebody else's cinematic exit.
 private static final EntityDataAccessor<String> EXIT_OWNER_654=
     SynchedEntityData.defineId(PowerArmorVisualEntity.class,EntityDataSerializers.STRING);
 private final AnimatableInstanceCache geoCache=GeckoLibUtil.createInstanceCache(this);''',"synched_field")
s=edit(s,"  builder.define(V175_PHASE,0);",
'''  builder.define(V175_PHASE,0);
  builder.define(EXIT_OWNER_654,"");''',"sync_default")
s=edit(s," public void beginPhase(int next){",
''' public void setExitOwner654(java.util.UUID uuid){
  entityData.set(EXIT_OWNER_654,uuid.toString());
 }
 public boolean isOpeningFor654(java.util.UUID uuid){
  return entityData.get(V175_PHASE)==7 &&
      entityData.get(EXIT_OWNER_654).equals(uuid.toString());
 }
 public void beginPhase(int next){''',"owner_read")
assert "case 7 ->" in s and "next>7" in s
visual.write_text(s,encoding="utf8")
client=J/"client/PowerArmorExitInputLock654.java"
assert not client.exists(),"B654 client event duplicate"
client.write_text('''package dev.obsidiannetwork.client;

import dev.obsidiannetwork.powerarmor.PowerArmorVisualEntity;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.ClientInput;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.phys.Vec3;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ClientTickEvent;

/** B654: freeze LOCAL input only while the server-synced 64-tick
 * exit-opening visual belongs to this exact player. Never hide the player
 * or modify equipment; restore original key input promptly on completion.
 */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class PowerArmorExitInputLock654 {
 private static final ClientInput ZERO_INPUT=new ClientInput();
 private static ClientInput previousInput;
 private static java.util.UUID lockedPlayer;
 private PowerArmorExitInputLock654(){}
 private static boolean opening(LocalPlayer p){
  return p.level().getEntitiesOfClass(PowerArmorVisualEntity.class,
      p.getBoundingBox().inflate(1.6D),
      v->v.isOpeningFor654(p.getUUID())).size()>0;
 }
 private static void restore(LocalPlayer p){
  if(previousInput!=null && p!=null) p.input=previousInput;
  previousInput=null;
  lockedPlayer=null;
 }
 @SubscribeEvent public static void pre(ClientTickEvent.Pre event){
  Minecraft mc=Minecraft.getInstance();
  LocalPlayer p=mc.player;
  if(p==null || mc.level==null){
   restore(null);return;
  }
  if(!opening(p)){
   if(previousInput!=null)restore(p);
   return;
  }
  if(previousInput==null || lockedPlayer==null ||
      !lockedPlayer.equals(p.getUUID())){
   previousInput=p.input==ZERO_INPUT?new ClientInput():p.input;
   lockedPlayer=p.getUUID();
  }
  p.input=ZERO_INPUT; // no WASD, jump, sneak, sprint or flying input
  p.setDeltaMovement(Vec3.ZERO);
 }
 @SubscribeEvent public static void post(ClientTickEvent.Post event){
  Minecraft mc=Minecraft.getInstance();
  LocalPlayer p=mc.player;
  if(p!=null && previousInput!=null && lockedPlayer!=null &&
     lockedPlayer.equals(p.getUUID()) && opening(p)){
   p.setDeltaMovement(Vec3.ZERO);
  }
 }
}
''',encoding="utf8")
print("B654: original player held on server pre/post; exact-owner client input suppressed; no motion-triggered abort, never invisible, 64-tick transfer")
