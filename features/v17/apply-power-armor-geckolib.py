#!/usr/bin/env python3
"""Build 56: replace five Z-fighting ItemDisplays with one GeckoLib 5 entity.

The animated model is cosmetic ONLY. The protected ArmorStand still owns the
four real ItemStacks, power, upgrades, and armor loadout/recovery transaction.
"""
import json
import os
import re
import struct
import zlib
from pathlib import Path

j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
resources=Path(os.environ["V1_RESOURCE_ROOT"])
mod=j/"ObsidianNetwork.java"
code=mod.read_text(encoding="utf-8")
assert "ARMOR_VISUAL_ENTITIES" not in code
registration=r"""
   // BUILD56_GECKOLIB: ephemeral visual ONLY; never holds real Power Armor.
   public static final net.neoforged.neoforge.registries.DeferredRegister.Entities ARMOR_VISUAL_ENTITIES =
       net.neoforged.neoforge.registries.DeferredRegister.createEntities("obsidiannetwork");
   public static final net.neoforged.neoforge.registries.DeferredHolder<net.minecraft.world.entity.EntityType<?>,
       net.minecraft.world.entity.EntityType<dev.obsidiannetwork.powerarmor.PowerArmorVisualEntity>> ARMOR_VISUAL_ENTITY_MK1 =
       ARMOR_VISUAL_ENTITIES.registerEntityType("power_armor_visual_mk1",
         dev.obsidiannetwork.powerarmor.PowerArmorVisualEntity::new,
         net.minecraft.world.entity.MobCategory.MISC,
         b->b.sized(1.6F,2.5F).clientTrackingRange(8).updateInterval(1).noSave());
   public static final net.neoforged.neoforge.registries.DeferredHolder<net.minecraft.world.entity.EntityType<?>,
       net.minecraft.world.entity.EntityType<dev.obsidiannetwork.powerarmor.PowerArmorVisualEntity>> ARMOR_VISUAL_ENTITY_MK2 =
       ARMOR_VISUAL_ENTITIES.registerEntityType("power_armor_visual_mk2",
         dev.obsidiannetwork.powerarmor.PowerArmorVisualEntity::new,
         net.minecraft.world.entity.MobCategory.MISC,
         b->b.sized(1.6F,2.5F).clientTrackingRange(8).updateInterval(1).noSave());
"""
anchor='   public static final DeferredItem<dev.obsidiannetwork.item.NetworkElytraItem> NETWORK_ELYTRA'
assert code.count(anchor)==1
code=code.replace(anchor,registration+anchor,1)
reg=re.findall(r'\bBLOCKS\.register\(([^;\n]+)\);',code)
assert len(reg)==1, f"Block registry event-bus drift: {reg}"
code=code.replace('BLOCKS.register('+reg[0]+');',
   'BLOCKS.register('+reg[0]+');\n      ARMOR_VISUAL_ENTITIES.register('+reg[0]+');',1)
mod.write_text(code,encoding="utf-8")

visual=j/"powerarmor/PowerArmorVisualEntity.java"
assert not visual.exists()
visual.write_text(r'''package dev.obsidiannetwork.powerarmor;

import com.geckolib.animatable.GeoEntity;
import com.geckolib.animatable.manager.AnimatableManager;
import com.geckolib.animation.AnimationController;
import com.geckolib.animation.RawAnimation;
import com.geckolib.cache.object.AnimatableInstanceCache;
import com.geckolib.util.GeckoLibUtil;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.level.Level;

/** Non-persistent 20-tick GeckoLib silhouette: no slots, drops, FE or inventory. */
public final class PowerArmorVisualEntity extends ArmorStand implements GeoEntity {
 private static final EntityDataAccessor<Boolean> ENTERING =
      SynchedEntityData.defineId(PowerArmorVisualEntity.class,EntityDataSerializers.BOOLEAN);
 private final AnimatableInstanceCache geoCache=GeckoLibUtil.createInstanceCache(this);

 public PowerArmorVisualEntity(EntityType<? extends ArmorStand> type,Level level){
  super(type,level);
  setInvulnerable(true);setNoGravity(true);setNoBasePlate(true);setShowArms(false);
 }
 @Override protected void defineSynchedData(SynchedEntityData.Builder builder){
  super.defineSynchedData(builder);
  builder.define(ENTERING,false);
 }
 public void begin(boolean entering){entityData.set(ENTERING,entering);}
 @Override public void registerControllers(AnimatableManager.ControllerRegistrar controllers){
  controllers.add(new AnimationController<>(this,"suit",0,state ->
   state.setAndContinue(RawAnimation.begin().thenPlay(
     entityData.get(ENTERING)?"animation.power_armor.close":"animation.power_armor.open"))));
 }
 @Override public AnimatableInstanceCache getAnimatableInstanceCache(){return geoCache;}
 @Override public void tick(){
  super.tick();
  if(!level().isClientSide()&&tickCount>23)discard();
 }
 @Override public boolean isPickable(){return false;}
}
''',encoding="utf-8")
client=j/"client/PowerArmorGeoRenderers.java"
client.parent.mkdir(parents=True,exist_ok=True)
assert not client.exists()
client.write_text(r'''package dev.obsidiannetwork.client;

import dev.obsidiannetwork.ObsidianNetwork;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.EntityRenderersEvent;

/** Client-only GeckoLib 5 render registration; no client classes on servers. */
@EventBusSubscriber(modid="obsidiannetwork", value=Dist.CLIENT)
public final class PowerArmorGeoRenderers {
 private PowerArmorGeoRenderers(){}
 @SubscribeEvent public static void register(EntityRenderersEvent.RegisterRenderers event){
  event.registerEntityRenderer(ObsidianNetwork.ARMOR_VISUAL_ENTITY_MK1.get(),
    ctx -> new com.geckolib.renderer.GeoEntityRenderer<>(
      ctx,ObsidianNetwork.ARMOR_VISUAL_ENTITY_MK1.get()));
  event.registerEntityRenderer(ObsidianNetwork.ARMOR_VISUAL_ENTITY_MK2.get(),
    ctx -> new com.geckolib.renderer.GeoEntityRenderer<>(
      ctx,ObsidianNetwork.ARMOR_VISUAL_ENTITY_MK2.get()));
 }
}
''',encoding="utf-8")

world=j/"powerarmor/PowerArmorSuitWorld.java"
body=world.read_text(encoding="utf-8")
start=body.index(" private record Animation(")
end=body.index(" @SubscribeEvent public static void transitionTick(",start)
old=body[start:end]
assert "ItemDisplay" in old and "movePanels" in old and "startAnimation" in old
body=body[:start]+r''' private record Animation(ArmorStand stand,int ticks,boolean entering,
                          PowerArmorVisualEntity visual){}
 private static final java.util.Map<UUID,Animation> ACTIVE=new java.util.HashMap<>();
 private static final String VISUAL_MARK="xsxlabs_power_armor_visual_transient";
 private static void pose(ArmorStand stand,int progress,boolean entering){
  // Keep vanilla suit neutral; GeckoLib performs all hinged bone movements.
  stand.setLeftArmPose(new net.minecraft.core.Rotations(0F,0F,0F));
  stand.setRightArmPose(new net.minecraft.core.Rotations(0F,0F,0F));
  stand.setHeadPose(new net.minecraft.core.Rotations(0F,0F,0F));
  stand.setLeftLegPose(new net.minecraft.core.Rotations(0F,0F,0F));
  stand.setRightLegPose(new net.minecraft.core.Rotations(0F,0F,0F));
  stand.setBodyPose(new net.minecraft.core.Rotations(0F,0F,0F));
 }
 private static void cleanup(Animation transition){
  if(transition.visual()!=null&&!transition.visual().isRemoved())
   transition.visual().discard();
  ArmorStand stand=transition.stand();
  if(!stand.isRemoved()){stand.setInvisible(false);pose(stand,20,false);}
 }
 private static Animation startAnimation(ArmorStand stand,ServerPlayer player,boolean entering){
  boolean mk2=PowerArmorRuntime.piece(
     stand.getItemBySlot(PowerArmorRuntime.SLOTS[0]),0,true);
  var type=mk2?dev.obsidiannetwork.ObsidianNetwork.ARMOR_VISUAL_ENTITY_MK2.get()
              :dev.obsidiannetwork.ObsidianNetwork.ARMOR_VISUAL_ENTITY_MK1.get();
  PowerArmorVisualEntity visual=new PowerArmorVisualEntity(type,stand.level());
  visual.addTag(VISUAL_MARK);
  visual.addTag(owner(player));
  visual.setPos(stand.getX(),stand.getY(),stand.getZ());
  visual.setYRot(stand.getYRot());
  visual.setYBodyRot(stand.getYRot());
  visual.begin(entering);
  if(!stand.level().addFreshEntity(visual)){
   return new Animation(stand,20,entering,null);
  }
  // The four actual ItemStacks never enter the cosmetic GeckoLib entity.
  stand.setInvisible(true);
  return new Animation(stand,20,entering,visual);
 }
''' + body[end:]
assert body.count("  movePanels(animation,t);")==1
body=body.replace("  movePanels(animation,t);","  // Bone pose interpolations are now client-side GeckoLib animations.",1)
assert body.count("animation.panels()")==1
body=body.replace("animation.panels()","animation.visual()",1)
oldcleanup='''    for(var visual:player.level().getEntitiesOfClass(
        net.minecraft.world.entity.Display.ItemDisplay.class,area,
        e->e.entityTags().contains(VISUAL_MARK)
            &&e.entityTags().contains(owner(player))))visual.discard();'''
assert body.count(oldcleanup)==1
body=body.replace(oldcleanup,oldcleanup+'''
    for(var visual:player.level().getEntitiesOfClass(
        PowerArmorVisualEntity.class,area,
        e->e.entityTags().contains(VISUAL_MARK)
            &&e.entityTags().contains(owner(player))))visual.discard();''',1)
assert "movePanels(animation" not in body and "animation.panels()" not in body
world.write_text(body,encoding="utf-8")

# Separate solid cuboids and pivoting bones; NO five overlapping baked planes.
def bone(name,pivot,cubes,parent="root"):
 out={"name":name,"parent":parent,"pivot":pivot}
 if cubes:out["cubes"]=[{"origin":origin,"size":size,"uv":uv,"inflate":0} for origin,size,uv in cubes]
 return out
bones=[
 {"name":"root","pivot":[0,0,0]},
 bone("spine",[0,17,0],[([-4.4,15,-3.4],[8.8,10,6.8],[0,0])]),
 bone("chest_left",[-4.0,23,-2],[([-6.8,16,-5],[5.7,9,2.0],[28,0])]),
 bone("chest_right",[4.0,23,-2], [([1.1,16,-5],[5.7,9,2.0],[28,14])]),
 bone("helmet",[0,25,0],[([-4.5,25,-4.5],[9,8.5,9],[0,25])]),
 bone("left_arm",[-6.3,23,0],[([-9.4,13,-3.4],[4.0,11,6.8],[52,0])]),
 bone("right_arm",[6.3,23,0],[([5.4,13,-3.4],[4.0,11,6.8],[52,17])]),
 bone("left_leg",[-2.8,14.8,0],[([-5.1,0,-3.6],[4.9,14.3,7.2],[0,47])]),
 bone("right_leg",[2.8,14.8,0],[([0.2,0,-3.6],[4.9,14.3,7.2],[18,47])]),
]
animation_open={
 "animation_length":1.0,"loop":"hold_on_last_frame",
 "bones":{
 "chest_left":{"rotation":{"0.0":[0,0,0],"1.0":[0,-74,-8]},"position":{"0.0":[0,0,0],"1.0":[-5,0,-2]}},
 "chest_right":{"rotation":{"0.0":[0,0,0],"1.0":[0,74,8]},"position":{"0.0":[0,0,0],"1.0":[5,0,-2]}},
 "helmet":{"rotation":{"0.0":[0,0,0],"1.0":[-50,0,0]},"position":{"0.0":[0,0,0],"1.0":[0,7,0]}},
 "left_arm":{"rotation":{"0.0":[0,0,0],"1.0":[0,0,-38]}},
 "right_arm":{"rotation":{"0.0":[0,0,0],"1.0":[0,0,38]}},
 "left_leg":{"rotation":{"0.0":[0,0,0],"1.0":[0,0,-17]}},
 "right_leg":{"rotation":{"0.0":[0,0,0],"1.0":[0,0,17]}}
}}
def reversed_animation(src):
 result=json.loads(json.dumps(src))
 for movement in result["bones"].values():
  for curve in movement.values():
   if "0.0" in curve and "1.0" in curve:curve["0.0"],curve["1.0"]=curve["1.0"],curve["0.0"]
 return result

def chunk(kind,raw):
 return struct.pack(">I",len(raw))+kind+raw+struct.pack(">I",zlib.crc32(kind+raw)&0xffffffff)
def png(tier):
 w=h=128
 # Per-tier palette, textured industrial shell, warm/cool visor detailing.
 main=(169,35,42) if tier=="mk1" else (34,42,53)
 edge=(205,157,55) if tier=="mk1" else (129,150,165)
 scan=(46,205,226) if tier=="mk1" else (63,194,239)
 rows=[]
 for y in range(h):
  line=bytearray([0])
  for x in range(w):
   if y<42: col=main if x<64 else edge
   elif y<82:col=edge if x<42 else main
   else:col=main if x<78 else scan
   drift=((x*17+y*13)%11)-5
   stripe=13 if (x+y//4)%19<3 else 0
   v=tuple(max(0,min(255,k+drift+stripe)) for k in col)
   line.extend((*v,255))
  rows.append(bytes(line))
 header=b'\x89PNG\r\n\x1a\n'
 image=header+chunk(b'IHDR',struct.pack(">IIBBBBB",w,h,8,6,0,0,0))
 image+=chunk(b'IDAT',zlib.compress(b"".join(rows),9))
 return image+chunk(b'IEND',b'')
for tier in ("mk1","mk2"):
 name=f"power_armor_visual_{tier}"
 dest=resources/"assets/obsidiannetwork"
 model=dest/f"geckolib/models/entity/{name}.geo.json"
 anim=dest/f"geckolib/animations/entity/{name}.animation.json"
 texture=dest/f"textures/entity/{name}.png"
 for f in (model,anim,texture):f.parent.mkdir(parents=True,exist_ok=True)
 model.write_text(json.dumps({"format_version":"1.12.0","minecraft:geometry":[{
 "description":{"identifier":f"geometry.{name}","texture_width":128,
                "texture_height":128,"visible_bounds_width":3,
                "visible_bounds_height":4,"visible_bounds_offset":[0,1.5,0]},
 "bones":bones}]},indent=2)+"\n",encoding="utf-8")
 anim.write_text(json.dumps({"format_version":"1.8.0","animations":{
   "animation.power_armor.open":animation_open,
   "animation.power_armor.close":reversed_animation(animation_open)}},indent=2)+"\n",encoding="utf-8")
 texture.write_bytes(png(tier))
print("BUILD56_GECKOLIB PASS: single mesh/bone animation, 2 tiers, 8 bones each, recovery untouched")
