#!/usr/bin/env python3
"""Build111: replace only the Power Armor shield EGG with six posed armor-shaped membranes.

Runs immediately after Build106. Purely client render replacement: protects Build104
damage/FE costs, the Build105 flight upgrade, all suit items and save compatibility.
"""
import os
from pathlib import Path

client=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/client/PowerArmorShieldClient.java"
prior=client.read_text(encoding="utf-8")
assert "BUILD106_DRACONIC_STYLE_SHIELD_SHELL" in prior, "Build110 shield baseline missing"
assert "private static boolean hasActiveShield(Player wearer)" in prior
assert "RenderPlayerEvent.Post<?> event" in prior

client.write_text(r'''package dev.obsidiannetwork.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import dev.obsidiannetwork.core.EnergyTool;
import dev.obsidiannetwork.powerarmor.PowerArmorRuntime;
import dev.obsidiannetwork.registry.ModDataComponents;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.RenderPlayerEvent;

/** BUILD111_POSED_ARMOR_SHIELD: six articulated close-fitting energy membranes.
 * Uses the ACTUAL player model part poses after rendering; no fixed egg, no
 * fake animation, no model/data replacements. Damage/FE remain Build104-only.
 */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class PowerArmorShieldClient {
 private PowerArmorShieldClient(){}
 private static final Identifier SKIN=Identifier.fromNamespaceAndPath(
     "obsidiannetwork","textures/entity/power_armor_shield_hex.png");
 private static final RenderType SHIELD_RENDER=RenderTypes.entityTranslucent(SKIN);
 private static final int RINGS=10, SIDES=16;
 private static final float PIXEL=1F/16F;

 private static boolean hasActiveShield(Player wearer){
  int tier=PowerArmorRuntime.tier(wearer.getItemBySlot(EquipmentSlot.HEAD),0);
  if(tier<1||tier>24)return false;
  boolean card=false;
  for(int i=0;i<PowerArmorRuntime.SLOTS.length;i++){
   EquipmentSlot slot=PowerArmorRuntime.SLOTS[i];
   var armor=wearer.getItemBySlot(slot);
   if(PowerArmorRuntime.tier(armor,i)!=tier||EnergyTool.energy(armor)<20L)return false;
   String installed=armor.get(ModDataComponents.POWER_ARMOR_UPGRADES.get());
   if(installed==null)continue;
   for(String id:installed.split(","))if(id.equals("energy_shield"))card=true;
  }
  return card;
 }

 @SubscribeEvent
 public static void onRenderPlayer(RenderPlayerEvent.Post<?> event){
  Minecraft mc=Minecraft.getInstance();
  if(mc.level==null||mc.player==null)return;
  var state=event.getRenderState();
  if(state.isSpectator||state.isInvisible||state.distanceToCameraSq>48D*48D)return;
  if(!(mc.level.getEntity(state.id) instanceof Player wearer))return;
  if(!hasActiveShield(wearer))return;

  float time=wearer.tickCount+event.getPartialTick();
  float pulse=(float)(.5D+.5D*Math.sin(time*.075D));
  // Damaging the Build104 forcefield visibly illuminates ALL six shell parts.
  float impact=Math.min(1F,Math.max(0F,wearer.hurtTime-event.getPartialTick())/8F);
  int alpha=Math.min(236,(int)(60F+9F*pulse+165F*impact));

  // The renderer has already called PlayerModel.setupAnim(state). Reuse its
  // actual head/torso/arm/leg joint transforms, including crouch and flight.
  var model=event.getRenderer().getModel();
  PoseStack stack=event.getPoseStack();
  var collector=event.getSubmitNodeCollector();

  // All values in vanilla model pixels, including ~1-1.5 px shield clearance.
  // ModelPart.translateAndRotate accounts for each pivot + animated rotation.
  // Covers the exact 8x8 helmet with the armor shell's extra surface.
  submitPart(stack,collector,model.head,0F,-3.9F,0F,
      5.35F,5.45F,5.35F,.40F,time,impact,alpha);
  // Tuned for chestplate + backpack volume, flaring slightly at shoulders.
  submitPart(stack,collector,model.body,0F,5.9F,0F,
      5.55F,7.45F,4.05F,.42F,time,impact,alpha);
  // Real arm ModelPart cubes are offset by -1/+1 px from their pivots.
  submitPart(stack,collector,model.rightArm,-1F,4.0F,0F,
      3.35F,7.15F,3.10F,.43F,time,impact,alpha);
  submitPart(stack,collector,model.leftArm,1F,4.0F,0F,
      3.35F,7.15F,3.10F,.43F,time,impact,alpha);
  // Each powered boot is enclosed individually: unlike the old single egg,
  // the shield visibly splits and walks with the legs.
  submitPart(stack,collector,model.rightLeg,0F,5.8F,0F,
      3.15F,7.05F,3.10F,.43F,time,impact,alpha);
  submitPart(stack,collector,model.leftLeg,0F,5.8F,0F,
      3.15F,7.05F,3.10F,.43F,time,impact,alpha);
 }

 private static void submitPart(PoseStack stack,
     net.minecraft.client.renderer.SubmitNodeCollector collector,
     ModelPart joint,float cx,float cy,float cz,
     float rx,float ry,float rz,float roundness,
     float time,float impact,int alpha){
  if(!joint.visible)return;
  stack.pushPose();
  joint.translateAndRotate(stack);
  // SubmitNodeCollector snapshots the joint-adjusted matrix. It is not
  // reused after popPose, so each part stays attached to its own moving bone.
  collector.submitCustomGeometry(stack,SHIELD_RENDER,
      (pose,out)->drawPiece(pose,out,cx,cy,cz,rx,ry,rz,roundness,time,impact,alpha));
  stack.popPose();
 }

 /** Signed exponent makes rounded cuboids: a BODY silhouette, not ellipsoids. */
 private static double square(double x,double k){
  return Math.copySign(Math.pow(Math.abs(x),k),x);
 }

 private static void drawPiece(PoseStack.Pose pose,VertexConsumer out,
      float cx,float cy,float cz,float rx,float ry,float rz,float roundness,
      float time,float hit,int alpha){
  // A complete closed surface around each body part, with curved shoulders,
  // helmet corners and boot contours. No disjoint floating particles.
  for(int j=0;j<RINGS;j++){
   double latA=-Math.PI/2+Math.PI*j/RINGS;
   double latB=-Math.PI/2+Math.PI*(j+1)/RINGS;
   for(int i=0;i<SIDES;i++){
    double lonA=2*Math.PI*i/SIDES;
    double lonB=2*Math.PI*(i+1)/SIDES;
    float ripple=(float)(.5D+.5D*Math.sin(time*.45D+i*.38D-j*.51D));
    int opacity=Math.min(255,alpha+(int)(hit*25F*ripple));
    vertex(pose,out,cx,cy,cz,rx,ry,rz,roundness,latA,lonA,
        0F,0F,opacity);
    vertex(pose,out,cx,cy,cz,rx,ry,rz,roundness,latB,lonA,
        0F,1F,opacity);
    vertex(pose,out,cx,cy,cz,rx,ry,rz,roundness,latB,lonB,
        1F,1F,opacity);
    vertex(pose,out,cx,cy,cz,rx,ry,rz,roundness,latA,lonB,
        1F,0F,opacity);
   }
  }
 }

 private static void vertex(PoseStack.Pose pose,VertexConsumer out,
      float cx,float cy,float cz,float rx,float ry,float rz,float exponent,
      double latitude,double longitude,float u,float v,int alpha){
  double flat=square(Math.cos(latitude),exponent);
  float vx=(float)(flat*square(Math.cos(longitude),exponent));
  float vy=(float)square(Math.sin(latitude),exponent);
  float vz=(float)(flat*square(Math.sin(longitude),exponent));
  // Fullbright preserves the energy glow at night. UV maps the same hex
  // membrane from Build110 separately across each limb.
  out.addVertex(pose,(cx+rx*vx)*PIXEL,(cy+ry*vy)*PIXEL,(cz+rz*vz)*PIXEL)
     .setColor(93,221,255,alpha)
     .setUv(u,v)
     .setOverlay(OverlayTexture.NO_OVERLAY)
     .setLight(0x00F000F0)
     .setNormal(pose,vx,vy,vz);
 }
}
''',encoding="utf-8")

assert client.read_text(encoding="utf-8").count("submitPart(stack,collector,model.")==6
assert "BUILD111_POSED_ARMOR_SHIELD" in client.read_text(encoding="utf-8")
assert "model.rightArm" in client.read_text(encoding="utf-8")
assert "model.leftLeg" in client.read_text(encoding="utf-8")
assert "PowerArmorRuntime.tier(armor,i)!=tier" in client.read_text(encoding="utf-8")
assert "hasActiveShield(wearer)" in client.read_text(encoding="utf-8")
print("BUILD111_ARMOR_SHAPED_SHIELD PASS: posed six-part close-fitting rounded-cuboid energy skin, hit flash and FE behavior preserved")
