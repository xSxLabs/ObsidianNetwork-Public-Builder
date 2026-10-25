#!/usr/bin/env python3
"""v1.7.3 Network Vision: Power Armor upgrade card, configurable AR key and HUD."""
import json,os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
D=Path(os.environ["V1_RESOURCE_ROOT"])/"data/obsidiannetwork"
def once(path,old,new):
 p=J/path;s=p.read_text()
 assert s.count(old)==1,(path,s.count(old),old[:80])
 p.write_text(s.replace(old,new,1))
def save(path,s):
 p=J/path;assert not p.exists(),p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
def obj(p,data):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,indent=2)+"\n")
once("ObsidianNetwork.java",
 '   public static final DeferredItem<dev.obsidiannetwork.powerarmor.UpgradeCardItem> POWER_ARMOR_UPGRADE =',
 '''   // V173_NETWORK_VISION: installed at the existing Armor Station.
   public static final DeferredItem<dev.obsidiannetwork.powerarmor.UpgradeCardItem> POWER_CARD_NETWORK_VISION =
      ITEMS.registerItem("power_card_network_vision",p -> new dev.obsidiannetwork.powerarmor.UpgradeCardItem(p,"network_vision"));
   public static final DeferredItem<dev.obsidiannetwork.powerarmor.UpgradeCardItem> POWER_ARMOR_UPGRADE =''')
once("ObsidianNetwork.java",
 '            output.accept((ItemLike)POWER_ARMOR_UPGRADE.get());',
 '            output.accept((ItemLike)POWER_ARMOR_UPGRADE.get());\n            output.accept((ItemLike)POWER_CARD_NETWORK_VISION.get());')
once("powerarmor/PowerArmorCards.java",
 '   default -> null;',
 '   case "network_vision" -> dev.obsidiannetwork.ObsidianNetwork.POWER_CARD_NETWORK_VISION.get();\n   default -> null;')
once("powerarmor/PowerArmorExitKeyClient.java",
 ''' public static final KeyMapping NIGHT=new KeyMapping(''',
 ''' public static final KeyMapping VISION=new KeyMapping(
   "key.obsidiannetwork.network_vision",
   InputConstants.Type.KEYSYM,GLFW.GLFW_KEY_K,
   CATEGORY);
 public static final KeyMapping NIGHT=new KeyMapping(''')
once("client/ClientModEvents.java",
 "  event.register(dev.obsidiannetwork.powerarmor.PowerArmorExitKeyClient.NIGHT);",
 "  event.register(dev.obsidiannetwork.powerarmor.PowerArmorExitKeyClient.NIGHT);\n  event.register(dev.obsidiannetwork.powerarmor.PowerArmorExitKeyClient.VISION);")
save("client/NetworkVisionClient.java",r'''package dev.obsidiannetwork.client;

import dev.obsidiannetwork.ObsidianNetwork;
import dev.obsidiannetwork.core.EnergyTool;
import dev.obsidiannetwork.powerarmor.PowerArmorExitKeyClient;
import dev.obsidiannetwork.powerarmor.PowerArmorRuntime;
import dev.obsidiannetwork.registry.ModDataComponents;
import net.minecraft.client.Minecraft;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import net.neoforged.neoforge.client.event.RenderGuiEvent;

/** V173_NETWORK_VISION: no x-ray into inventories, bounded local cable overlay.
 * Enabled only with powered, full suit and actual installed upgrade card.
 * Configurable K key in existing xSxLabs controls category.
 */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class NetworkVisionClient {
 private NetworkVisionClient(){}
 private static boolean enabled=false;
 private static int visible=0;
 private static final DustParticleOptions CABLE=new DustParticleOptions(0x27c9ff,.64f);
 private static final DustParticleOptions ENERGY=new DustParticleOptions(0xf2c05c,.70f);
 private static final DustParticleOptions DEVICE=new DustParticleOptions(0xc059ff,.7f);

 private static boolean ready(){
  var mc=Minecraft.getInstance();
  if(mc.player==null)return false;
  int tier=PowerArmorRuntime.tier(mc.player.getItemBySlot(EquipmentSlot.HEAD),0);
  if(tier<1)return false;
  boolean card=false;
  for(int i=0;i<PowerArmorRuntime.SLOTS.length;i++){
   var stack=mc.player.getItemBySlot(PowerArmorRuntime.SLOTS[i]);
   if(PowerArmorRuntime.tier(stack,i)!=tier||EnergyTool.energy(stack)<100L)return false;
   String tags=stack.get(ModDataComponents.POWER_ARMOR_UPGRADES.get());
   if(tags!=null)for(String id:tags.split(","))if(id.equals("network_vision"))card=true;
  }
  return card;
 }
 @SubscribeEvent public static void tick(ClientTickEvent.Post event){
  var mc=Minecraft.getInstance();
  while(PowerArmorExitKeyClient.VISION.consumeClick()){
   if(mc.screen==null&&ready())enabled=!enabled;
  }
  if(mc.player==null||mc.level==null||mc.isPaused()){enabled=false;return;}
  if(!ready()){enabled=false;visible=0;return;}
  if(!enabled||mc.player.tickCount%7!=0)return;
  // Bound both rendering and world reads: 9x5x9 around the wearer.
  BlockPos center=mc.player.blockPosition();
  int drawn=0;
  for(int y=-2;y<=2;y++)for(int x=-4;x<=4;x++)for(int z=-4;z<=4;z++){
   if(drawn>=55)break;
   BlockPos p=center.offset(x,y,z);
   if(!mc.level.hasChunkAt(p))continue;
   BlockState s=mc.level.getBlockState(p);
   DustParticleOptions color;
   if(s.is(ObsidianNetwork.NETWORK_CABLE.get()))color=CABLE;
   else if(s.is(ObsidianNetwork.ENERGY_CABLE.get()))color=ENERGY;
   else if(s.getBlock() instanceof dev.obsidiannetwork.block.NetworkPlanterBlock
      || s.getBlock() instanceof dev.obsidiannetwork.block.NetworkDeviceBlock)color=DEVICE;
   else continue;
   double t=mc.player.tickCount*.055;
   mc.level.addParticle(color,p.getX()+.5+.27*Math.cos(t),p.getY()+.55,
          p.getZ()+.5+.27*Math.sin(t),0,.002,0);
   drawn++;
  }
  visible=drawn;
 }
 @SubscribeEvent public static void hud(RenderGuiEvent.Post event){
  if(!enabled||!ready())return;
  var mc=Minecraft.getInstance();
  var g=event.getGuiGraphics();
  int x=8,y=8;
  g.fill(x-3,y-3,x+153,y+35,0xb0071a2b);
  g.fill(x-3,y-3,x+153,y-1,0xff22bfe0);
  g.text(mc.font,"xSxLabs  /  NETWORK VISION",x,y,0xff66f8ff);
  g.text(mc.font,"Cyan: Network | Gold: FE",x,y+12,0xffd8e6ee);
  g.text(mc.font,"Violet: Machines | Nodes: "+visible,x,y+23,0xffc7a9ff);
 }
}
''')
obj(R/"models/item/power_card_network_vision.json",
    {"parent":"minecraft:item/generated","textures":{"layer0":"obsidiannetwork:item/power_armor_upgrade"}})
obj(R/"items/power_card_network_vision.json",{"model":{"type":"minecraft:model","model":"obsidiannetwork:item/power_card_network_vision"}})
obj(D/"recipe/power_card_network_vision.json",{"type":"minecraft:crafting_shaped","pattern":["IRI","NCN","IRI"],
    "key":{"I":"minecraft:diamond_block","R":"minecraft:ender_eye","N":"minecraft:netherite_ingot","C":"obsidiannetwork:power_armor_upgrade"},
    "result":{"id":"obsidiannetwork:power_card_network_vision","count":1}})
for lang in ("de_de","en_us"):
 p=R/"lang"/(lang+".json");data=json.loads(p.read_text())
 data["item.obsidiannetwork.power_card_network_vision"]="Network Vision Upgrade Card" if lang=="en_us" else "Netzwerksicht-Upgrade-Karte"
 data["key.obsidiannetwork.network_vision"]="Toggle Network Vision" if lang=="en_us" else "Netzwerksicht umschalten"
 obj(p,data)
print("V173_NETWORK_VISION_READY: new real station card, xSxLabs hotkey and colored bounded client AR overlay")
