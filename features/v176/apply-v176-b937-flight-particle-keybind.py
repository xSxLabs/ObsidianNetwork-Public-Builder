#!/usr/bin/env python3
"""B937: optional rebindable creative-flight particle key; default UNBOUND.
Only toggles the client-side jets while using the Power Armor flight upgrade.
Does not affect creative flight, FE, Elytra, or particle types on the server.
Apply after B637 and after other 1.7.6 client patches.
"""
import os,json
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])

def modify(path, old, new):
 p=J/path
 txt=p.read_text(encoding="utf-8")
 assert txt.count(old)==1,("B937_DRIFT",path,txt.count(old),old[:130])
 p.write_text(txt.replace(old,new,1),encoding="utf-8")

path=J/"client/V176CreativeFlightParticlesClient.java"
assert not path.exists(),("B937_DUPLICATE_BINDING",str(path))
path.write_text('''package dev.obsidiannetwork.client;

import com.mojang.blaze3d.platform.InputConstants;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.network.chat.Component;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.RegisterKeyMappingsEvent;
import net.neoforged.neoforge.client.event.ClientTickEvent;

/** Local visual preference, not a gameplay permission or flight mode.
 * The key lives in Options > Controls > Key Binds and is UNBOUND by default.
 */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class V176CreativeFlightParticlesClient {
 private V176CreativeFlightParticlesClient(){}
 private static KeyMapping key;
 private static boolean enabled=true;

 public static boolean enabled(){return enabled;}

 @SubscribeEvent public static void register(RegisterKeyMappingsEvent event){
  key=new KeyMapping("key.obsidiannetwork.creative_flight_particles",
     InputConstants.Type.KEYSYM,InputConstants.UNKNOWN.getValue(),
     KeyMapping.Category.MISC);
  event.register(key);
 }
 @SubscribeEvent public static void onTick(ClientTickEvent.Post event){
  if(key==null)return;
  Minecraft mc=Minecraft.getInstance();
  if(mc.player==null||mc.screen!=null)return;
  while(key.consumeClick()){
   enabled=!enabled;
   mc.player.displayClientMessage(Component.literal(
      "Power Armor Creative Flight Partikel: "+(enabled?"AN":"AUS")),true);
  }
 }
}
''',encoding="utf-8")

# All particle emitters of this flight effect share one loop, so prevent both
# CLOUD and END_ROD effects when hovering. Elytra jets remain identical.
visual="client/PowerArmorBuild98Client.java"
modify(visual,
 """   boolean boost=gliding && p.isShiftKeyDown() && EnergyTool.energy(chest)>=1500L;
   if(!boost && p.tickCount%2!=0)continue;""",
 """   boolean boost=gliding && p.isShiftKeyDown() && EnergyTool.energy(chest)>=1500L;
   // Cosmetic client preference ONLY for the Creative Flight hover card.
   // Elytra/gliding particles always behave as before.
   if(creativeArmor&&!V176CreativeFlightParticlesClient.enabled())continue;
   if(!boost && p.tickCount%2!=0)continue;""")

for lang,caption in (
 ("de_de","Creative-Flight-Partikel ein/aus"),
 ("en_us","Toggle Creative Flight Particles")
):
 p=R/f"assets/obsidiannetwork/lang/{lang}.json"
 data=json.loads(p.read_text(encoding="utf-8"))
 key="key.obsidiannetwork.creative_flight_particles"
 assert key not in data,("B937_KEY_ALREADY_TRANSLATED",lang)
 data[key]=caption
 p.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

src=path.read_text(encoding="utf-8")
client=(J/visual).read_text(encoding="utf-8")
assert 'RegisterKeyMappingsEvent event' in src
assert 'ClientTickEvent.Post event' in src
assert 'InputConstants.UNKNOWN.getValue()' in src
assert 'KeyMapping.Category.MISC' in src
assert 'while(key.consumeClick())' in src
assert 'if(creativeArmor&&!V176CreativeFlightParticlesClient.enabled())continue;' in client
assert 'ParticleTypes.END_ROD' in client and 'ParticleTypes.CLOUD' in client
assert 'if(!gliding&&!hover)continue;' in client
print("B937_REBINDABLE_UNBOUND_CREATIVE_FLIGHT_PARTICLES_ONLY_TOGGLE_READY")
