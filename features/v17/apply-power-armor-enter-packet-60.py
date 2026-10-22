#!/usr/bin/env python3
"""Build 60: reliable right-click-to-enter for standing MK1 and MK2 armor.

The vanilla ArmorStand interaction varies by click part/client-side result.
A second explicit client->server packet calls the SAME ownership-validated entry
path; it cannot transfer items twice and has no permission to mutate inventories.
"""
import os
from pathlib import Path
j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
world=j/"powerarmor/PowerArmorSuitWorld.java"
body=world.read_text(encoding="utf-8")
anchor=''' private static void enter(ArmorStand stand,net.minecraft.world.entity.player.Player actor){'''
assert body.count(anchor)==1
body=body.replace(anchor,''' /** Explicit fallback for local right-clicks that vanilla ArmorStand consumes.
  * Server checks: entity ID exists in THIS dimension, proximity, owner tags,
  * actual full armor, no pending transition, and valid backup before transfer.
  */
 public static void tryEnter(ServerPlayer player,int entityId){
  Entity entity=player.level().getEntity(entityId);
  if(!(entity instanceof ArmorStand stand))return;
  if(stand.isRemoved()||!mine(stand,player))return;
  if(player.distanceToSqr(stand)>36.0D)return;
  enter(stand,player);
 }
'''+anchor,1)
world.write_text(body,encoding="utf-8")
payload=j/"powerarmor/PowerArmorEnterPayload.java"
assert not payload.exists()
payload.write_text(r'''package dev.obsidiannetwork.powerarmor;

import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;

/** Entity ID is untrusted; server verifies distance, suit marker and owner. */
public record PowerArmorEnterPayload(int entityId) implements CustomPacketPayload {
 public static final Type<PowerArmorEnterPayload> TYPE = new Type<>(
   Identifier.fromNamespaceAndPath("obsidiannetwork","power_armor_enter"));
 public static final StreamCodec<RegistryFriendlyByteBuf,PowerArmorEnterPayload> STREAM_CODEC =
    StreamCodec.of(
      (buf,value)->buf.writeVarInt(value.entityId()),
      buf->new PowerArmorEnterPayload(buf.readVarInt()));
 @Override public Type<? extends CustomPacketPayload> type(){return TYPE;}
 @EventBusSubscriber(modid="obsidiannetwork")
 public static final class Handler {
  private Handler(){}
  @SubscribeEvent public static void register(RegisterPayloadHandlersEvent e){
   e.registrar("1").playToServer(TYPE,STREAM_CODEC,
    (payload,context)->{
     if(context.player() instanceof ServerPlayer player)
       PowerArmorSuitWorld.tryEnter(player,payload.entityId());
    });
  }
 }
}
''',encoding="utf-8")
client=j/"powerarmor/PowerArmorEnterClient.java"
assert not client.exists()
client.write_text(r'''package dev.obsidiannetwork.powerarmor;

import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;

/** Send server the actual clicked entity ID; NEVER transfer suit items client-side. */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class PowerArmorEnterClient {
 private PowerArmorEnterClient(){}
 @SubscribeEvent public static void interact(PlayerInteractEvent.EntityInteractSpecific event){
  if(event.getHand()!=InteractionHand.MAIN_HAND)return;
  if(!(event.getTarget() instanceof ArmorStand stand))return;
  // Do not cancel vanilla interaction: normal armor stands still work.
  // Owner tags may not be synchronized on clients; server validates them.
  net.neoforged.neoforge.client.network.ClientPacketDistributor.sendToServer(
    new PowerArmorEnterPayload(stand.getId()));
 }
}
''',encoding="utf-8")
assert "player.distanceToSqr(stand)>36.0D" in body
assert "if(stand.isRemoved()||!mine(stand,player))return;" in body
print("BUILD60_RIGHT_CLICK PASS: client click -> validated server entry for MK1/MK2; existing backup/FE untouched")
