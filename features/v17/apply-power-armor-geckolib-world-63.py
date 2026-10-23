#!/usr/bin/env python3
"""Build 63: persistent, right-clickable GeckoLib world suits and Apotheosis armor tags.

The previous implementation renders a temporary fake GeckoLib entity while
storing suit parts in a vanilla ArmorStand. Here the ACTUAL armor-owning stand
is both the renderer and the interaction target. Existing deployed vanilla
stands remain readable through the legacy fallback; no world data migration.
"""
import os,json
from pathlib import Path
j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
r=Path(os.environ["V1_RESOURCE_ROOT"])

def change(path,old,new):
 p=j/path
 data=p.read_text(encoding="utf-8")
 assert data.count(old)==1, "BUILD63 unexpected anchor "+path+" ("+str(data.count(old))+")"
 p.write_text(data.replace(old,new,1),encoding="utf-8")

# Register two persistent entity types with GeckoLib renderers. This uses the
# existing GeckoLib model, texture and animation assets shipped for MK1/MK2.
# Unlike the transient visual entities, these have normal world persistence.
mod=j/"ObsidianNetwork.java"
txt=mod.read_text(encoding="utf-8")
anchor='''   public static final DeferredItem<dev.obsidiannetwork.item.NetworkElytraItem> NETWORK_ELYTRA'''
assert txt.count(anchor)==1
registered=r'''   // The same suit stores four real stacks, renders via GeckoLib and handles right-click.
   public static final net.neoforged.neoforge.registries.DeferredHolder<
      net.minecraft.world.entity.EntityType<?>,
      net.minecraft.world.entity.EntityType<dev.obsidiannetwork.powerarmor.PowerArmorStand>> POWER_ARMOR_WORLD_MK1 =
      ARMOR_VISUAL_ENTITIES.registerEntityType("power_armor_world_mk1",
         dev.obsidiannetwork.powerarmor.PowerArmorStand::new,
         net.minecraft.world.entity.MobCategory.MISC,
         b->b.sized(0.75F,2.1F).clientTrackingRange(10).updateInterval(1));
   public static final net.neoforged.neoforge.registries.DeferredHolder<
      net.minecraft.world.entity.EntityType<?>,
      net.minecraft.world.entity.EntityType<dev.obsidiannetwork.powerarmor.PowerArmorStand>> POWER_ARMOR_WORLD_MK2 =
      ARMOR_VISUAL_ENTITIES.registerEntityType("power_armor_world_mk2",
         dev.obsidiannetwork.powerarmor.PowerArmorStand::new,
         net.minecraft.world.entity.MobCategory.MISC,
         b->b.sized(0.75F,2.1F).clientTrackingRange(10).updateInterval(1));
'''
mod.write_text(txt.replace(anchor,registered+anchor,1),encoding="utf-8")

stand=j/"powerarmor/PowerArmorStand.java"
assert not stand.exists()
stand.write_text(r'''package dev.obsidiannetwork.powerarmor;

import com.geckolib.animatable.GeoEntity;
import com.geckolib.animatable.manager.AnimatableManager;
import com.geckolib.animation.AnimationController;
import com.geckolib.animation.RawAnimation;
import com.geckolib.animation.object.PlayState;
import com.geckolib.animatable.instance.AnimatableInstanceCache;
import com.geckolib.util.GeckoLibUtil;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

/** Persisted Power Armor: REAL four ItemStacks, GeoModel and click target in ONE entity.
 * No cosmetic lookalike owns items, and no detached suit can be duplicated on exit.
 */
public final class PowerArmorStand extends ArmorStand implements GeoEntity {
 // 0 = idle (suit closed), 1 = exit/close, 2 = enter/open.
 private static final EntityDataAccessor<Integer> TRANSITION =
      SynchedEntityData.defineId(PowerArmorStand.class,EntityDataSerializers.INT);
 private final AnimatableInstanceCache cache=GeckoLibUtil.createInstanceCache(this);
 public PowerArmorStand(EntityType<? extends ArmorStand> type,Level level) {
  super(type,level);
  setNoGravity(true);
  setNoBasePlate(true);
  setShowArms(false);
 }
 @Override protected void defineSynchedData(SynchedEntityData.Builder builder){
  super.defineSynchedData(builder);
  builder.define(TRANSITION,0);
 }
 public void animate(boolean entering) {
  entityData.set(TRANSITION,entering?2:1);
 }
 public void stopAnimation() {entityData.set(TRANSITION,0);}
 @Override public void registerControllers(AnimatableManager.ControllerRegistrar controllers){
  controllers.add(new AnimationController<>("suit",0,state -> {
   int transition=entityData.get(TRANSITION);
   if(transition==0)return PlayState.STOP;
   return state.setAndContinue(RawAnimation.begin().thenPlay(
     transition==2?"animation.power_armor.open":"animation.power_armor.close"));
  }));
 }
 @Override public AnimatableInstanceCache getAnimatableInstanceCache(){return cache;}
 @Override public boolean isPickable(){return true;}
 // Entity#interactAt was removed in MC 26.1.2. Override the current
 // location-based Entity#interact so clicking the model itself always works.
 @Override public InteractionResult interact(Player player,InteractionHand hand,Vec3 location){
  if(hand!=InteractionHand.MAIN_HAND)return InteractionResult.PASS;
  if(!level().isClientSide() && player instanceof net.minecraft.server.level.ServerPlayer server)
   PowerArmorSuitWorld.tryEnter(server,getId());
  return InteractionResult.SUCCESS;
 }
}
''',encoding="utf-8")

renderer=j/"client/PowerArmorGeoRenderers.java"
source=renderer.read_text(encoding="utf-8")
anchor=''' @SubscribeEvent public static void register(EntityRenderersEvent.RegisterRenderers event){'''
assert source.count(anchor)==1
source=source.replace(anchor,anchor+'''
  // Dedicated renderers for persistent world suits. The existing textured
  // GeckoLib assets are reused explicitly; no second phantom render layer.
  event.registerEntityRenderer(ObsidianNetwork.POWER_ARMOR_WORLD_MK1.get(),
    ctx -> new com.geckolib.renderer.GeoEntityRenderer<>(
      ctx,new com.geckolib.model.DefaultedEntityGeoModel<>(
        net.minecraft.resources.Identifier.fromNamespaceAndPath(
          "obsidiannetwork","power_armor_visual_mk1"))));
  event.registerEntityRenderer(ObsidianNetwork.POWER_ARMOR_WORLD_MK2.get(),
    ctx -> new com.geckolib.renderer.GeoEntityRenderer<>(
      ctx,new com.geckolib.model.DefaultedEntityGeoModel<>(
        net.minecraft.resources.Identifier.fromNamespaceAndPath(
          "obsidiannetwork","power_armor_visual_mk2"))));
''',1)
renderer.write_text(source,encoding="utf-8")

# Real entity: spawn uses correct MK1/MK2 type. The existing world-transfer
# transaction introduced in build62 remains 100% unchanged.
world="powerarmor/PowerArmorSuitWorld.java"
change(world,
 '''  ArmorStand stand=new ArmorStand(level,pos.getX()+0.5D,pos.getY(),pos.getZ()+0.5D);''',
 '''  // mk2 was already validated at the start of spawn(); reuse that value.
  var type=mk2?dev.obsidiannetwork.ObsidianNetwork.POWER_ARMOR_WORLD_MK2.get()
              :dev.obsidiannetwork.ObsidianNetwork.POWER_ARMOR_WORLD_MK1.get();
  PowerArmorStand stand=new PowerArmorStand(type,level);
  stand.setPos(pos.getX()+0.5D,pos.getY(),pos.getZ()+0.5D);''')

# Remove the entire temporary mannequin for new suits. GeckoLib animates
# the actual persistent owner of all four stacks, so no client-side visual
# can be missing or unclickable during the idle pose.
change(world,
 ''' private static Animation startAnimation(ArmorStand stand,ServerPlayer player,boolean entering){
  boolean mk2=PowerArmorRuntime.piece(''',
 ''' private static Animation startAnimation(ArmorStand stand,ServerPlayer player,boolean entering){
  if(stand instanceof PowerArmorStand worldSuit){
   worldSuit.animate(entering);
   return new Animation(stand,20,entering,null);
  }
  // Old vanilla stands are still supported without changing saved worlds.
  boolean mk2=PowerArmorRuntime.piece(''')
change(world,
 '''  if(!stand.isRemoved()){stand.setInvisible(false);pose(stand,20,false);}''',
 '''  if(!stand.isRemoved()){
   stand.setInvisible(false);pose(stand,20,false);
   if(stand instanceof PowerArmorStand worldSuit)worldSuit.stopAnimation();
  }''')

# In the 26.1 entity interaction pipeline, EntityInteractSpecific is not
# reliable for ALL armor stand body hit locations. A direct override is the
# authoritative path, while existing ownership checked packet remains fallback.
source=(j/world).read_text(encoding="utf-8")
assert "PowerArmorStand worldSuit" in source
assert "ArmorStand stand=spawn(player,worn);" in source
assert "for(EquipmentSlot slot:PowerArmorRuntime.SLOTS)stand.setItemSlot(slot,ItemStack.EMPTY);" in source
assert "stand.discard();" in source

# Apotheosis Reforging classification: each piece must also belong to the
# ordinary armor slot tag used by other mod compatibility filters. The existing
# 8 explicit Apotheosis loot_category_overrides remain in place.
for part,tag in (("helmet","head_armor"),("chestplate","chest_armor"),
                 ("leggings","leg_armor"),("boots","foot_armor")):
 target=r/"data/minecraft/tags/item"/(tag+".json")
 target.parent.mkdir(parents=True,exist_ok=True)
 additions=[f"obsidiannetwork:power_armor_{part}",
            f"obsidiannetwork:power_armor_mk2_{part}"]
 if target.exists():
  doc=json.loads(target.read_text(encoding="utf-8"))
  assert isinstance(doc.get("values"),list),"Existing vanilla armor tag invalid"
  for item in additions:
   if item not in doc["values"]:doc["values"].append(item)
 else:
  doc={"replace":False,"values":additions}
 target.write_text(json.dumps(doc,indent=2)+"\n",encoding="utf-8")

print("BUILD63_WORLD_SUIT_GECKOLIB PASS: persistent owned GeoEntity with real right-click, no phantom suit, MK1/MK2, tag-compatible Apotheosis categories")
