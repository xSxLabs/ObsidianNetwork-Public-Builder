#!/usr/bin/env python3
"""B937: rebinding-ready Creative Flight particle toggle.
The hotkey appears in Minecraft's regular Controls menu and starts UNBOUND.
Client-side visuals only; does not change FE, flight ability, Elytra, gameplay.
Runs AFTER v175 B637 creative flight and B936 visual/monitor fixes.
"""
import os,json
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])

src=J/"client/V176CreativeFlightParticles.java"
assert not src.exists(),("B937_DUPLICATE_CREATIVE_PARTICLES",str(src))
src.parent.mkdir(parents=True,exist_ok=True)
src.write_text('''package dev.obsidiannetwork.client;

import com.mojang.blaze3d.platform.InputConstants;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.network.chat.Component;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.RegisterKeyMappingsEvent;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import org.lwjgl.glfw.GLFW;

/** Client-only visual option, not a flight or energy mode change. */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class V176CreativeFlightParticles {
 private V176CreativeFlightParticles(){}
 // Visible in Options -> Controls -> Key Binds. Default UNBOUND to
 // prevent conflicts with custom modpacks and player controls.
 private static final KeyMapping TOGGLE=new KeyMapping(
  "key.obsidiannetwork.creative_flight_particles",
  InputConstants.Type.KEYSYM,GLFW.GLFW_KEY_UNKNOWN,
  KeyMapping.Category.MISC);
 private static boolean enabled=true;
 public static boolean enabled(){return enabled;}

 @SubscribeEvent public static void clientTick(ClientTickEvent.Post event){
  while(TOGGLE.consumeClick()){
   enabled=!enabled;
   var p=Minecraft.getInstance().player;
   if(p!=null)p.displayClientMessage(Component.literal(
    enabled?"Creative Flight-Partikel AN":"Creative Flight-Partikel AUS"),true);
  }
 }
 // NeoForge 26.1 automatically routes this event to the MOD bus;
 // the removed Bus.MOD annotation attribute would fail compilation.
 @SubscribeEvent public static void register(RegisterKeyMappingsEvent event){
  event.register(TOGGLE);
 }
}
''',encoding="utf-8")

target=J/"client/PowerArmorBuild98Client.java"
s=target.read_text(encoding="utf-8")
needle="   boolean boost=gliding && p.isShiftKeyDown() && EnergyTool.energy(chest)>=1500L;\n   if(!boost && p.tickCount%2!=0)continue;"
assert s.count(needle)==1,("B937_CREATIVE_EMITTER_GATE_DRIFT",s.count(needle))
s=s.replace(needle,needle+'''
   // Toggle ONLY the visual jets of Power Armor Creative Flight.
   // Never suppress Elytra particles or interfere with flight/FE logic.
   if(creativeArmor && !V176CreativeFlightParticles.enabled())continue;''',1)
target.write_text(s,encoding="utf-8")
assert s.count("if(creativeArmor && !V176CreativeFlightParticles.enabled())continue;")==1
assert "boolean boost=gliding &&" in s
assert "ParticleTypes.END_ROD" in s
assert "ParticleTypes.CLOUD" in s

for language,label in (
 ("de_de","Creative Flight: Partikel ein/aus"),
 ("en_us","Creative Flight: Toggle Particles")
):
 lang=R/f"assets/obsidiannetwork/lang/{language}.json"
 data=json.loads(lang.read_text(encoding="utf-8"))
 key="key.obsidiannetwork.creative_flight_particles"
 assert key not in data,("B937_KEY_COLLISION",language)
 data[key]=label
 lang.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("B937_REBINDABLE_CREATIVE_FLIGHT_PARTICLES_ONLY_NO_ELYTRA_OR_FE_CHANGE_PASS")
