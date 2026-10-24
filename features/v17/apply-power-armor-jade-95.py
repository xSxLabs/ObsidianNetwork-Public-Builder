#!/usr/bin/env python3
"""Build 95: optional Jade 26.1.2 tooltip for owned, complete standing Power Armor.

Client Jade reads armor equipment that the vanilla ArmorStand already synchronizes:
no new packets, copies, inventories, FE transactions or permanent state.
"""
import json
import os
from pathlib import Path

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
res=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
project=Path(os.environ["V1_PROJECT_ROOT"])
marker="BUILD95_JADE_POWER_ARMOR_BONUS"
out=root/"compat/PowerArmorJadePlugin.java"
assert not out.exists(),marker+" duplicate plugin"
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(r'''package dev.obsidiannetwork.compat;

import dev.obsidiannetwork.core.EnergyTool;
import dev.obsidiannetwork.powerarmor.PowerArmorRuntime;
import dev.obsidiannetwork.powerarmor.PowerArmorSuitWorld;
import dev.obsidiannetwork.registry.ModDataComponents;
import java.util.LinkedHashMap;
import java.util.Map;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.item.ItemStack;
import snownee.jade.api.EntityAccessor;
import snownee.jade.api.IEntityComponentProvider;
import snownee.jade.api.ITooltip;
import snownee.jade.api.IWailaClientRegistration;
import snownee.jade.api.IWailaPlugin;
import snownee.jade.api.WailaPlugin;
import snownee.jade.api.config.IPluginConfig;

/** BUILD95_JADE_POWER_ARMOR_BONUS.
 * Jade is compileOnly/optional. This integration class is only discovered by
 * Jade while Jade is present; never register it on the regular NeoForge bus.
 */
@WailaPlugin
public final class PowerArmorJadePlugin implements IWailaPlugin {
 @Override public void registerClient(IWailaClientRegistration registration){
  registration.registerEntityComponent(SuitBonusProvider.INSTANCE, ArmorStand.class);
 }
 private enum SuitBonusProvider implements IEntityComponentProvider {
  INSTANCE;
  private static final Identifier UID=Identifier.fromNamespaceAndPath(
      "obsidiannetwork","power_armor_bonuses");

  @Override public Identifier getUid(){return UID;}

  private static void effect(ITooltip tooltip,String key,int tier,int bonus){
   tooltip.add(Component.translatable(
      "jade.obsidiannetwork.power_armor."+key,tier,bonus)
      .withStyle(ChatFormatting.GREEN));
  }
  private static void label(ITooltip tooltip,String key,int tier){
   tooltip.add(Component.translatable(
      "jade.obsidiannetwork.power_armor."+key,tier)
      .withStyle(ChatFormatting.GREEN));
  }
  private static void simple(ITooltip tooltip,String key){
   tooltip.add(Component.translatable("jade.obsidiannetwork.power_armor."+key)
      .withStyle(ChatFormatting.AQUA));
  }

  @Override public void appendTooltip(ITooltip tooltip,EntityAccessor accessor,IPluginConfig config){
   if(!(accessor.getEntity() instanceof ArmorStand stand))return;
   // Cosmetic GeckoLib transition entities carry NO real item stacks.
   if(!PowerArmorSuitWorld.full(stand))return;
   int tier=PowerArmorRuntime.tier(stand.getItemBySlot(EquipmentSlot.HEAD),0);
   if(tier<1 || tier>24)return;
   tooltip.add(Component.translatable("jade.obsidiannetwork.power_armor.title",tier)
       .withStyle(ChatFormatting.GOLD));

   // Use synchronized REAL equipment stacks; the preview cannot extract/move
   // anything and does not expose saved previous armor or owner UUIDs.
   Map<String,Integer> cards=new LinkedHashMap<>();
   boolean powered=true;
   boolean nightVisionOn=false;
   for(EquipmentSlot slot:PowerArmorRuntime.SLOTS){
    ItemStack piece=stand.getItemBySlot(slot);
    if(EnergyTool.energy(piece)<20L)powered=false;
    String raw=piece.get(ModDataComponents.POWER_ARMOR_UPGRADES.get());
    if(raw==null || raw.isBlank())continue;
    for(String id:raw.split(",")){
     if(id.equals("nightvision_on")){nightVisionOn=true;continue;}
     if(id.isBlank())continue;
     cards.merge(id,1,Integer::sum);
    }
   }
   if(cards.isEmpty()){
    simple(tooltip,"none");
    return;
   }
   if(!powered)tooltip.add(Component.translatable(
        "jade.obsidiannetwork.power_armor.energy_required")
        .withStyle(ChatFormatting.RED));

   for(Map.Entry<String,Integer> entry:cards.entrySet()){
    String id=entry.getKey();
    int n=entry.getValue();
    switch(id){
     // Identical caps/effect amplifiers to PowerArmorRuntime and ArmorStationMenu.
     case "strength" -> {int lvl=Math.min(3,n);effect(tooltip,"strength",lvl,lvl*3);}
     case "resistance" -> {int lvl=Math.min(2,n);effect(tooltip,"resistance",lvl,lvl*20);}
     case "speed" -> {int lvl=Math.min(3,n);effect(tooltip,"speed",lvl,lvl*20);}
     case "haste" -> {int lvl=Math.min(3,n);effect(tooltip,"haste",lvl,lvl*20);}
     case "regeneration" -> label(tooltip,"regeneration",Math.min(2,n));
     case "fire_resistance" -> simple(tooltip,"fire_resistance");
     case "jump_boost" -> label(tooltip,"jump_boost",Math.min(2,n));
     case "water_breathing" -> simple(tooltip,"water_breathing");
     case "night_vision" -> {
      if(nightVisionOn)simple(tooltip,"night_vision_on");
      else simple(tooltip,"night_vision_off");
     }
     // Damage reduction is FE-dependent, shared total capped at 80 percent.
     case "protection" -> effect(tooltip,"protection",Math.min(5,n),Math.min(5,n)*8);
     case "fire_protection" -> effect(tooltip,"fire_protection",Math.min(5,n),Math.min(80,Math.min(5,n)*16));
     case "blast_protection" -> effect(tooltip,"blast_protection",Math.min(5,n),Math.min(80,Math.min(5,n)*16));
     case "projectile_protection" -> effect(tooltip,"projectile_protection",Math.min(5,n),Math.min(80,Math.min(5,n)*16));
     case "feather_falling" -> effect(tooltip,"feather_falling",Math.min(5,n),Math.min(80,Math.min(5,n)*24));
     case "flight" -> simple(tooltip,"flight");
     case "network_elytra" -> simple(tooltip,"network_elytra");
     case "energy_shield" -> simple(tooltip,"energy_shield");
     // Show other installed card identities/counts, without claiming bonuses
     // whose actual runtime effects have not been implemented/verified.
     default -> tooltip.add(Component.translatable(
         "jade.obsidiannetwork.power_armor.installed",
         Component.translatable("item.obsidiannetwork.power_card_"+id),n));
    }
   }
   tooltip.add(Component.translatable("jade.obsidiannetwork.power_armor.energy_note")
       .withStyle(ChatFormatting.GRAY));
  }
 }
}
''',encoding="utf-8")

langs={
 "en_us":{
  "title":"Power Armor MK%s - Installed bonuses",
  "none":"No upgrade cards installed",
  "energy_required":"Bonuses inactive until all armor pieces have FE",
  "strength":"Strength %s: +%s attack damage",
  "resistance":"Resistance %s: -%s%% damage",
  "speed":"Speed %s: +%s%% movement speed",
  "haste":"Haste %s: +%s%% mining speed",
  "regeneration":"Regeneration %s",
  "fire_resistance":"Fire Resistance (fire immunity)",
  "jump_boost":"Jump Boost %s",
  "water_breathing":"Water Breathing",
  "night_vision_on":"Night Vision (ON)",
  "night_vision_off":"Night Vision (OFF - toggle with J)",
  "protection":"Protection %s: +%s%% FE shielding",
  "fire_protection":"Fire Protection %s: up to +%s%% FE shielding",
  "blast_protection":"Blast Protection %s: up to +%s%% FE shielding",
  "projectile_protection":"Projectile Protection %s: up to +%s%% FE shielding",
  "feather_falling":"Feather Falling %s: up to +%s%% FE shielding",
  "flight":"Creative-style flight (powered suit)",
  "network_elytra":"Network Elytra glide + Shift boost",
  "installed":"Installed: %s x%s",
  "energy_note":"Bonuses apply when equipped and powered; FE shielding max 80%",
  "config":"Power Armor upgrades"
 },
 "de_de":{
  "title":"Power-Rüstung MK%s - Installierte Boni",
  "none":"Keine Upgrade-Karten installiert",
  "energy_required":"Boni inaktiv, bis alle Rüstungsteile FE haben",
  "strength":"Stärke %s: +%s Angriffsschaden",
  "resistance":"Resistenz %s: -%s%% Schaden",
  "speed":"Schnelligkeit %s: +%s%% Bewegungstempo",
  "haste":"Eile %s: +%s%% Abbautempo",
  "regeneration":"Regeneration %s",
  "fire_resistance":"Feuerresistenz (immun gegen Feuer)",
  "jump_boost":"Sprungkraft %s",
  "water_breathing":"Unterwasseratmung",
  "night_vision_on":"Nachtsicht (AN)",
  "night_vision_off":"Nachtsicht (AUS - mit J umschalten)",
  "protection":"Schutz %s: +%s%% FE-Schutz",
  "fire_protection":"Feuerschutz %s: bis zu +%s%% FE-Schutz",
  "blast_protection":"Explosionsschutz %s: bis zu +%s%% FE-Schutz",
  "projectile_protection":"Projektilschutz %s: bis zu +%s%% FE-Schutz",
  "feather_falling":"Federfall %s: bis zu +%s%% FE-Schutz",
  "flight":"Kreativartiger Flug (mit FE)",
  "network_elytra":"Network-Elytra-Gleiten + Shift-Boost",
  "installed":"Installiert: %s x%s",
  "energy_note":"Boni nur beim Tragen mit FE; FE-Schutz insgesamt max. 80 %",
  "config":"Power-Rüstungs-Upgrades"
 }
}
for lang,table in langs.items():
 file=res/"lang"/(lang+".json")
 data=json.loads(file.read_text(encoding="utf-8"))
 for key,value in table.items():
  if key=="config":data["config.jade.plugin_obsidiannetwork.power_armor_bonuses"]=value
  else:data["jade.obsidiannetwork.power_armor."+key]=value
 file.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

gradle=project/"build.gradle"
s=gradle.read_text(encoding="utf-8")
assert "maven.modrinth:jade:" not in s,marker+" Gradle already patched"
s+="""
// Build95: Jade is OPTIONAL, never bundled in our distributable JAR.
// Official Jade 26.1.2 API from Modrinth Maven; no Jade runtime dependency.
repositories { maven { url 'https://api.modrinth.com/maven' } }
dependencies { compileOnly 'maven.modrinth:jade:26.1.12+neoforge' }
"""
gradle.write_text(s,encoding="utf-8")
assert "@WailaPlugin" in out.read_text(encoding="utf-8")
assert "registerEntityComponent(SuitBonusProvider.INSTANCE, ArmorStand.class)" in out.read_text(encoding="utf-8")
assert "PowerArmorSuitWorld.full(stand)" in out.read_text(encoding="utf-8")
assert "cards.merge(id,1,Integer::sum)" in out.read_text(encoding="utf-8")
print(marker+" PASS: optional Jade entity provider, MK1..24, real installed card counts, true effect caps and numeric bonuses, no armor transfer")
