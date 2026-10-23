#!/usr/bin/env python3
"""Build 70: register vanilla-compatible base attributes for all GeckoLib suit entities.

PowerArmorVisualEntity and PowerArmorStand extend LivingEntity via ArmorStand.
Without EntityAttributeCreationEvent -> event.put, the custom EntityType's
AttributeMap starts with a null supplier. Spawning an animated model then
crashes with AttributeSupplier.getValue(...), confirmed in Build 69 GameTest.
This is the only gameplay change: all item transfers and save data stay intact.
"""
import os
from pathlib import Path

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
mod=(root/"ObsidianNetwork.java").read_text(encoding="utf-8")
for registry in ("ARMOR_VISUAL_ENTITY_MK1","ARMOR_VISUAL_ENTITY_MK2",
                 "POWER_ARMOR_WORLD_MK1","POWER_ARMOR_WORLD_MK2"):
 assert registry in mod, "Build 70 entity type registration missing: "+registry
p=root/"powerarmor/PowerArmorAttributes.java"
assert not p.exists(), "Build 70 attribute registration already exists"
p.write_text(r'''package dev.obsidiannetwork.powerarmor;

import dev.obsidiannetwork.ObsidianNetwork;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.EntityAttributeCreationEvent;

/** Required for all ArmorStand-derived GeckoLib types, including cosmetic ones.
 *  No ItemStack, FE, loot, or ownership state is stored in these attributes.
 */
@EventBusSubscriber(modid="obsidiannetwork")
public final class PowerArmorAttributes {
 private PowerArmorAttributes(){}
 @SubscribeEvent public static void register(EntityAttributeCreationEvent event){
  // Build 69 crashed because the visual GeckoLib living entity had no
  // AttributeSupplier; register on both logical sides via mod-bus lifecycle.
  AttributeSupplier vanillaStandBase=LivingEntity.createLivingAttributes().build();
  event.put(ObsidianNetwork.ARMOR_VISUAL_ENTITY_MK1.get(),vanillaStandBase);
  event.put(ObsidianNetwork.ARMOR_VISUAL_ENTITY_MK2.get(),vanillaStandBase);
  // The persistent custom world entity types remain registered even though
  // Build 65 moved actual inventory ownership back to vanilla ArmorStand.
  event.put(ObsidianNetwork.POWER_ARMOR_WORLD_MK1.get(),vanillaStandBase);
  event.put(ObsidianNetwork.POWER_ARMOR_WORLD_MK2.get(),vanillaStandBase);
 }
}
''',encoding="utf-8")
print("BUILD70_POWER_ARMOR_ATTRIBUTES PASS: custom MK1/MK2 visual and world entity attributes registered")
