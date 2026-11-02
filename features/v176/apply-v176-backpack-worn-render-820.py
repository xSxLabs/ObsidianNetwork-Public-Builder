#!/usr/bin/env python3
"""B820: render each real 3D backpack on every equipped player's back.

Uses NeoForge/Minecraft 26.1 submit-node rendering API, not removed legacy
ItemRenderer.renderStatic. Chest equipment first; optional Curios back second.
Only render one bag. Never render a bag held in the hands on the player's back.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
client=J/"client/V176BackpackWornRenderer.java"
client.parent.mkdir(parents=True,exist_ok=True)
assert not client.exists(),("B820_RENDER_ALREADY_PRESENT",client)
client.write_text('''package dev.obsidiannetwork.client;

import com.mojang.math.Axis;
import dev.obsidiannetwork.backpack.NetworkBackpackItem;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.item.ItemStackRenderState;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.ModList;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.RenderPlayerEvent;

/** Render original color-matched BlockItem model on actual worn players.
 * Server-synced equipment/Curios state determines the visual tier.
 */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class V176BackpackWornRenderer {
 private V176BackpackWornRenderer(){}
 private static ItemStack equipped(LivingEntity player){
  ItemStack chest=player.getItemBySlot(EquipmentSlot.CHEST);
  if(chest.getItem() instanceof NetworkBackpackItem)return chest;
  if(ModList.get().isLoaded("curios")){
   try{
    var cls=Class.forName("dev.obsidiannetwork.client.V176BackpackWornCurios");
    Object item=cls.getMethod("find",LivingEntity.class).invoke(null,player);
    if(item instanceof ItemStack bag && bag.getItem() instanceof NetworkBackpackItem)
     return bag;
   }catch(ReflectiveOperationException ignored){
    // Optional Curios API must never crash a world without Curios.
   }
  }
  return ItemStack.EMPTY;
 }
 @SubscribeEvent public static void render(RenderPlayerEvent.Post<?> event){
  Minecraft game=Minecraft.getInstance();
  if(game.level==null||event.getRenderState().isSpectator)return;
  var entity=game.level.getEntity(event.getRenderState().id);
  if(!(entity instanceof LivingEntity player))return;
  ItemStack bag=equipped(player);
  if(bag.isEmpty())return;
  var model=new ItemStackRenderState();
  game.getItemModelResolver().updateForLiving(
      model,bag,ItemDisplayContext.FIXED,player);
  if(model.isEmpty())return;
  var pose=event.getPoseStack();
  pose.pushPose();
  // Orient the bag with its wearer's torso rather than world north.
  pose.mulPose(Axis.YP.rotationDegrees(180.0F-event.getRenderState().bodyRot));
  pose.translate(0.0F,event.getRenderState().isCrouching?-.51F:-.69F,.29F);
  pose.scale(.66F,.66F,.66F);
  model.submit(pose,event.getSubmitNodeCollector(),
       event.getRenderState().lightCoords,OverlayTexture.NO_OVERLAY,0);
  pose.popPose();
 }
}
''',encoding="utf-8")
curios=J/"client/V176BackpackWornCurios.java"
assert not curios.exists(),("B820_WORN_CURIOS_DUPLICATE",curios)
curios.write_text('''package dev.obsidiannetwork.client;

import dev.obsidiannetwork.backpack.NetworkBackpackItem;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import top.theillusivec4.curios.api.CuriosApi;

/** Loaded only behind runtime ModList guard; optional visual integration. */
public final class V176BackpackWornCurios {
 private V176BackpackWornCurios(){}
 public static ItemStack find(LivingEntity player){
  var inventory=CuriosApi.getCuriosInventory(player);
  if(inventory.isEmpty())return ItemStack.EMPTY;
  var handler=inventory.get().getStacksHandler("back");
  if(handler.isEmpty())return ItemStack.EMPTY;
  var items=handler.get().getStacks();
  for(int i=0;i<items.getSlots();i++){
   var candidate=items.getStackInSlot(i);
   if(candidate.getItem() instanceof NetworkBackpackItem)return candidate;
  }
  return ItemStack.EMPTY;
 }
}
''',encoding="utf-8")
print("V176_B820_REAL_24_VARIANT_BACKPACK_WORN_RENDERER_CURIO_BACK_PASS")
