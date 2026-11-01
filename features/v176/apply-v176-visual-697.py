#!/usr/bin/env python3
"""v1.7.6 B697: real attached 3D wrist barrels (24 tier-tinted styles).

Uses 26.1.2 render submission; does not touch legacy armor or recall rigs.
Only visible with Micro-MG plus authoritative Attack/Turret mode token.
"""
import json,os
from pathlib import Path
from PIL import Image

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"

def edit(rel,old,new):
 p=J/rel
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("V176_B697_ANCHOR_DRIFT",rel,s.count(old),old[:120])
 p.write_text(s.replace(old,new,1),encoding="utf-8")

# The standing suit has no client-side scoreboard tags. Persist an explicit
# weapon state inside its already-synchronized chestplate upgrades component.
edit("powerarmor/V176CompanionMode.java",
 '''  if(!was)suit.addTag(requested);
  display(player,(turret?"Turret":"Follow")+" Mode: "+(was?"OFF":"ON"));''',
 '''  if(!was)suit.addTag(requested);
  ItemStack chest=suit.getItemBySlot(EquipmentSlot.CHEST);
  String installed=chest.get(ModDataComponents.POWER_ARMOR_UPGRADES.get());
  if(installed!=null){
   var values=new java.util.ArrayList<String>(Arrays.asList(installed.split(",")));
   values.removeIf("micro_mg_turret_on"::equals);
   if(turret&&!was&&values.contains("micro_mg"))values.add("micro_mg_turret_on");
   chest.set(ModDataComponents.POWER_ARMOR_UPGRADES.get(),String.join(",",values));
   suit.setItemSlot(EquipmentSlot.CHEST,chest.copy());
  }
  display(player,(turret?"Turret":"Follow")+" Mode: "+(was?"OFF":"ON"));''')

# In-game module removal must disarm the stand, not leave a stale turret tag.
edit("powerarmor/V176CompanionMode.java",
 '''  if(!turret||!hasModule(suit))return;
  ItemStack chest=suit.getItemBySlot(EquipmentSlot.CHEST);''',
 '''  if(turret&&!hasModule(suit)){
   suit.removeTag(TURRET);
   return;
  }
  if(!turret)return;
  ItemStack chest=suit.getItemBySlot(EquipmentSlot.CHEST);''')

# The original equipment atlas is the palette source for all 24 variants;
# no alteration of worn armor textures/UVs or entry/exit GeckoLib clips.
for tier in range(1,25):
 stem="power_armor" if tier==1 else f"power_armor_mk{tier}"
 source=A/"textures/entity/equipment/humanoid"/(stem+".png")
 assert source.is_file(),("V176_B697_TIER_TEXTURE_MISSING",tier)
 with Image.open(source) as im:
  sample=im.convert("RGBA")
  palette=[(r,g,b) for r,g,b,a in sample.getdata()
           if a>=200 and max(r,g,b)>=55 and (max(r,g,b)-min(r,g,b))>=12]
  if not palette:
   palette=[(r,g,b) for r,g,b,a in sample.getdata() if a>=200 and max(r,g,b)>45]
  assert palette,("V176_B697_NO_ARMOR_PIGMENTS",tier)
  main=tuple(sum(c[i] for c in palette)//len(palette) for i in range(3))
 out=Image.new("RGBA",(32,32))
 for y in range(32):
  for x in range(32):
   # Laser-marked alloy housing, narrow cooling vents, shaded muzzle ring.
   scratch=((x*9+y*7)%11)-5
   if x in (0,1,30,31) or y in (0,1,30,31):
    v=(12,17,22)
   elif (x//4+y//5)%5==0:
    v=(40,47,55)
   elif x in (5,6,7) and y in range(12,26):
    v=(28,34,42)
   else:
    v=tuple(max(18,min(242,int(main[i]*.78+scratch))) for i in range(3))
   out.putpixel((x,y),(*v,255))
 dst=A/"textures/entity"/(f"micro_mg_mk{tier}.png")
 dst.parent.mkdir(parents=True,exist_ok=True)
 assert not dst.exists(),("V176_B697_DUPLICATE_ASSET",dst)
 out.save(dst)

p=J/"client/V176MicroMgVisualClient.java"
assert not p.exists(),("V176_B697_DUPLICATE_RENDERER",p)
p.write_text(r'''package dev.obsidiannetwork.client;

import com.mojang.blaze3d.vertex.PoseStack;
import dev.obsidiannetwork.powerarmor.PowerArmorRuntime;
import dev.obsidiannetwork.registry.ModDataComponents;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.AABB;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.RenderArmEvent;
import net.neoforged.neoforge.client.event.RenderLivingEvent;
import net.neoforged.neoforge.client.event.RenderPlayerEvent;
import net.minecraft.client.renderer.SubmitNodeCollector;
import java.util.Arrays;
import java.util.Map;
import java.util.HashMap;

/** Animated solid 3D wrist barrel attached to actual arm pose, never a HUD icon. */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class V176MicroMgVisualClient {
 private V176MicroMgVisualClient(){}
 private static final ModelPart BARREL=createBarrel();
 private static final Map<Integer,Float> EXTENSION=new HashMap<>();

 private static ModelPart createBarrel(){
  MeshDefinition mesh=new MeshDefinition();
  mesh.getRoot().addOrReplaceChild("barrel",
    CubeListBuilder.create()
      .texOffs(0,0).addBox(-1.0F,5.5F,-9.0F,2.0F,2.0F,7.0F)
      .texOffs(0,10).addBox(-1.25F,5.25F,-9.5F,2.5F,2.5F,1.5F)
      .texOffs(0,16).addBox(-1.5F,5.0F,-4.0F,3.0F,3.0F,3.0F),
    PartPose.ZERO);
  return LayerDefinition.create(mesh,32,32).bakeRoot().getChild("barrel");
 }
 private static boolean has(ItemStack chest,String key){
  if(chest.isEmpty())return false;
  String raw=chest.get(ModDataComponents.POWER_ARMOR_UPGRADES.get());
  return raw!=null&&Arrays.asList(raw.split(",")).contains(key);
 }
 private static int tier(LivingEntity entity){
  int tier=PowerArmorRuntime.tier(entity.getItemBySlot(EquipmentSlot.HEAD),0);
  if(tier<1||tier>24)return 0;
  for(int i=1;i<4;i++)
   if(PowerArmorRuntime.tier(entity.getItemBySlot(PowerArmorRuntime.SLOTS[i]),i)!=tier)
    return 0;
  return tier;
 }
 private static float extension(int key,boolean armed){
  float old=EXTENSION.getOrDefault(key,0.0F);
  float next=armed?Math.min(1.0F,old+0.12F):Math.max(0.0F,old-0.12F);
  if(next==0.0F)EXTENSION.remove(key);
  else EXTENSION.put(key,next);
  return next;
 }
 private static Identifier texture(int tier){
  return Identifier.fromNamespaceAndPath("obsidiannetwork",
    "textures/entity/micro_mg_mk"+tier+".png");
 }
 private static void drawArm(PoseStack pose,SubmitNodeCollector nodes,int light,
     ModelPart parent,int tier,float extension){
  if(extension<=0.001F)return;
  pose.pushPose();
  parent.translateAndRotate(pose);
  // Sub-armor housing stays hidden until extended; smooth mechanical slide.
  pose.translate(0.0F,0.0F,(1.0F-extension)*0.40F);
  nodes.submitModelPart(BARREL,pose,RenderTypes.entitySolid(texture(tier)),
      light,OverlayTexture.NO_OVERLAY,null,false,false,0xFFFFFFFF,null,0);
  pose.popPose();
 }
 private static void drawPair(PoseStack pose,SubmitNodeCollector nodes,int light,
      HumanoidModel<?> model,int tier,float extension){
  drawArm(pose,nodes,light,model.leftArm,tier,extension);
  drawArm(pose,nodes,light,model.rightArm,tier,extension);
 }

 @SubscribeEvent public static void worn(RenderPlayerEvent.Post<?> event){
  Minecraft mc=Minecraft.getInstance();
  if(mc.level==null)return;
  Entity entity=mc.level.getEntity(event.getRenderState().id);
  if(!(entity instanceof Player player))return;
  int tier=tier(player);
  if(tier==0)return;
  ItemStack chest=player.getItemBySlot(EquipmentSlot.CHEST);
  boolean armed=has(chest,"micro_mg")&&has(chest,"micro_mg_on");
  float amount=extension(entity.getId(),armed);
  if(amount>0.0F)
   drawPair(event.getPoseStack(),event.getSubmitNodeCollector(),
      event.getRenderState().lightCoords,event.getRenderer().getModel(),tier,amount);
 }
 @SubscribeEvent public static void firstPerson(RenderArmEvent event){
  var player=event.getPlayer();
  int tier=tier(player);
  if(tier==0)return;
  ItemStack chest=player.getItemBySlot(EquipmentSlot.CHEST);
  if(!has(chest,"micro_mg")||!has(chest,"micro_mg_on"))return;
  // The hand event pose already follows the actual first-person arm.
  PoseStack pose=event.getPoseStack();
  pose.pushPose();
  pose.translate(0.0F,0.0F,-0.28F);
  event.getSubmitNodeCollector().submitModelPart(BARREL,pose,
    RenderTypes.entitySolid(texture(tier)),event.getPackedLight(),
    OverlayTexture.NO_OVERLAY,null,false,false,0xFFFFFFFF,null,0);
  pose.popPose();
 }
 @SubscribeEvent public static void worldSuit(RenderLivingEvent.Post<?,?,?> event){
  if(event.getRenderState().entityType!=EntityType.ARMOR_STAND)return;
  Minecraft mc=Minecraft.getInstance();
  if(mc.level==null)return;
  var state=event.getRenderState();
  var box=new AABB(state.x-0.20,state.y-0.20,state.z-0.20,
                    state.x+0.20,state.y+0.20,state.z+0.20);
  for(ArmorStand stand:mc.level.getEntitiesOfClass(ArmorStand.class,box)){
   if(Math.abs(stand.getX()-state.x)>.15||Math.abs(stand.getZ()-state.z)>.15)continue;
   int tier=tier(stand);
   if(tier==0)continue;
   ItemStack chest=stand.getItemBySlot(EquipmentSlot.CHEST);
   boolean armed=has(chest,"micro_mg")&&has(chest,"micro_mg_turret_on");
   float amount=extension(stand.getId(),armed);
   if(amount>0F && event.getRenderer().getModel() instanceof HumanoidModel<?> model)
    drawPair(event.getPoseStack(),event.getSubmitNodeCollector(),
       state.lightCoords,model,tier,amount);
   break;
  }
 }
}
''',encoding="utf-8")
print("V176_B697_24_TEXTURED_SYNCED_3D_WEAPON_BARRELS_PASS")
