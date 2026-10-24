#!/usr/bin/env python3
"""Build104: Draconic-inspired rechargeable Power Armor Forcefield card.
Installed at station like existing discs; client aura/visual flash and a
server-authoritative high-FE-per-hit defensive layer. Runs after Build103.
"""
from pathlib import Path
import os,json

j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
resources=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"

server=j/"powerarmor/PowerArmorEnergyShield.java"
client=j/"client/PowerArmorShieldClient.java"
assert not server.exists() and not client.exists(),"BUILD104 duplicate forcefield"
server.parent.mkdir(parents=True,exist_ok=True)
client.parent.mkdir(parents=True,exist_ok=True)
server.write_text(r'''package dev.obsidiannetwork.powerarmor;

import dev.obsidiannetwork.core.EnergyTool;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.entity.EquipmentSlot;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.living.LivingDamageEvent;

/** BUILD104_FORCEFIELD: no per-player NBT, no duplication, FE fully server authoritative. */
@EventBusSubscriber(modid="obsidiannetwork")
public final class PowerArmorEnergyShield {
 private PowerArmorEnergyShield(){}
 // Minimum 20k FE per damaging hit, PLUS 10k FE for each damage point
 // absorbed. Normal suit idle is 80 FE per five ticks.
 private static final long HIT_BASE_COST=20_000L;
 private static final double FE_PER_DAMAGE_ABSORBED=10_000.0D;
 private static final float ABSORB_FRACTION=0.60F;

 // Runs AFTER existing PowerArmorRuntime protection on the same Pre event.
 // Remaining damage is attenuated, never set to zero, and damage bypassing
 // invulnerability (e.g. /kill, void-type mechanics) is not intercepted.
 @SubscribeEvent(priority=EventPriority.LOWEST)
 public static void onDamage(LivingDamageEvent.Pre event){
  if(!(event.getEntity() instanceof ServerPlayer p))return;
  if(!PowerArmorRuntime.powered(p)||!PowerArmorRuntime.hasCard(p,"energy_shield"))return;
  if(p.isCreative()||p.isSpectator())return;
  if(event.getSource().is(DamageTypeTags.BYPASSES_INVULNERABILITY))return;
  float remaining=event.getNewDamage();
  if(!Float.isFinite(remaining)||remaining<=0F)return;
  float absorbed=remaining*ABSORB_FRACTION;
  double raw=HIT_BASE_COST+FE_PER_DAMAGE_ABSORBED*absorbed;
  // Saturation prevents overflow and refuses hits larger than the available FE.
  long totalCost=(long)Math.ceil(Math.min(1_000_000_000.0D,raw));
  long perPart=(totalCost+3L)/4L;
  for(EquipmentSlot slot:PowerArmorRuntime.SLOTS){
   if(EnergyTool.energy(p.getItemBySlot(slot))<perPart+20L)return;
  }
  // Do not mutate HP until every armor component has passed the energy preflight.
  for(EquipmentSlot slot:PowerArmorRuntime.SLOTS)
   EnergyTool.consume(p.getItemBySlot(slot),perPart);
  event.setNewDamage(remaining-absorbed);

  // Immediately replicate the bright shield impact to nearby clients,
  // even if armor prevents the usual full knockback/hurt flash.
  ServerLevel world=p.serverLevel();
  world.sendParticles(new DustParticleOptions(0x74dfff,1.3F),
      p.getX(),p.getY()+.95D,p.getZ(),44,.68D,.88D,.68D,.015D);
  world.sendParticles(ParticleTypes.END_ROD,
      p.getX(),p.getY()+.95D,p.getZ(),15,.63D,.85D,.63D,.02D);
 }
}
''',encoding="utf-8")

client.write_text(r'''package dev.obsidiannetwork.client;

import dev.obsidiannetwork.core.EnergyTool;
import dev.obsidiannetwork.powerarmor.PowerArmorRuntime;
import dev.obsidiannetwork.registry.ModDataComponents;
import net.minecraft.client.Minecraft;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ClientTickEvent;

/** BUILD104_FORCEFIELD_AURA: cheap, translucent-looking cyan ellipsoid shell. */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class PowerArmorShieldClient {
 private PowerArmorShieldClient(){}
 private static final DustParticleOptions SOFT=new DustParticleOptions(0x5bbfe8,0.53F);
 private static final DustParticleOptions IMPACT=new DustParticleOptions(0x8debff,0.95F);

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

 @SubscribeEvent public static void aura(ClientTickEvent.Post event){
  Minecraft mc=Minecraft.getInstance();
  if(mc.level==null||mc.player==null||mc.isPaused())return;
  int drawn=0;
  for(Player wearer:mc.level.players()){
   if(++drawn>12)break; // bounded, even with many nearby players
   if(wearer.distanceToSqr(mc.player)>24D*24D)continue;
   if(wearer.tickCount%3!=0||!hasActiveShield(wearer))continue;
   // Each sample lies on an ellipsoid that fits a 2-block tall human.
   // The phase changes over time to suggest gently rotating shield arcs.
   double phase=wearer.tickCount*.19D + wearer.getId()*.73D;
   for(int k=0;k<7;k++){
    double v=-.87D+(k+.5D)/7D*1.74D;
    double a=phase+k*2.399963229728653D;
    double rad=Math.sqrt(Math.max(0D,1D-v*v));
    double dx=.79D*rad*Math.cos(a);
    double dz=.79D*rad*Math.sin(a);
    double dy=.92D*v;
    mc.level.addParticle(SOFT,
      wearer.getX()+dx,wearer.getY()+.95D+dy,wearer.getZ()+dz,
      0D,0.0008D,0D);
   }
   // Extra vivid surface points during the conventional hurt animation.
   // Server also broadcasts hit sparks when actual FE absorption succeeds.
   if(wearer.hurtTime>=8){
    for(int k=0;k<8;k++){
     double a=phase+k*Math.PI/4D;
     double h=((k%3)-1)*.55D;
     mc.level.addParticle(IMPACT,
       wearer.getX()+.80D*Math.cos(a),
       wearer.getY()+.95D+h,
       wearer.getZ()+.80D*Math.sin(a),
       0D,0D,0D);
    }
   }
  }
 }
}
''',encoding="utf-8")

for language,card,info in (
 ("en_us","Energy Shield","Energy Shield: always-on aura, bright hit flash, consumes FE to absorb 60% of remaining damage"),
 ("de_de","Energieschild","Energieschild: dauerhafte Aura, heller Trefferblitz, absorbiert 60 % des Restschadens gegen viel FE"),
):
 p=resources/"lang"/(language+".json")
 data=json.loads(p.read_text(encoding="utf-8"))
 data["item.obsidiannetwork.power_card_energy_shield"]=card+" Upgrade Card" if language=="en_us" else card+"-Upgrade-Karte"
 data["message.obsidiannetwork.power_armor.energy_shield_info"]=info
 data["jade.obsidiannetwork.power_armor.energy_shield"]=info
 p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

assert 'PowerArmorRuntime.hasCard(p,"energy_shield")' in server.read_text(encoding="utf-8")
assert "perPart+20L" in server.read_text(encoding="utf-8")
assert "event.setNewDamage(remaining-absorbed)" in server.read_text(encoding="utf-8")
assert 'if(id.equals("energy_shield"))card=true;' in client.read_text(encoding="utf-8")
print("BUILD104_FORCEFIELD PASS: installed card only, 24 powered suit tiers, ambient sphere, per-hit visible pulse and guaranteed expensive 20k+10k FE per absorbed damage")
