#!/usr/bin/env python3
"""Build204: Power Armor upgrades, portal resources, Blueprint/Printer reliability.

Kept after all v1.7.3 scripts so stable v1.7.2 is untouched.
"""
import os,json
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
def patch(rel,old,new):
 p=J/rel
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,(rel,s.count(old),old[:100])
 p.write_text(s.replace(old,new,1),encoding="utf-8")
def dump(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# 18 instead of 15 actual card positions, all armor tiers share the same
# Armor Station install/remove validation and survive existing stacks.
patch("powerarmor/ArmorStationBlock.java",
 'if(entries.length>=15||count>=(card.upgradeId.equals("protection")?4:1))',
 'if(entries.length>=18||count>=(card.upgradeId.equals("protection")?4:1))')

# Clarify diagnostics: "upgrade missing" used to hide low-charge/incomplete suit.
patch("portal/PortalActionPayload.java",
 '''  if(!hasUpgrade(player)){
   tell(player,"Equip a powered Power Armor and install its Portal Upgrade Card at the Armor Station.");
   return;
  }''',
 '''  if(!hasUpgrade(player)){
   if(!dev.obsidiannetwork.powerarmor.PowerArmorRuntime.full(player))
    tell(player,"Portal: complete matching four-piece Power Armor required.");
   else if(!dev.obsidiannetwork.powerarmor.PowerArmorRuntime.hasCard(player,"portal"))
    tell(player,"Portal: install Portal Upgrade Card in Armor Station.");
   else tell(player,"Portal: charge ALL four Power Armor pieces (at least 20 FE each).");
   return;
  }''')
patch("portal/PortalActionPayload.java",
 '''  if(!hasUpgrade(player)){
   tell(player,"Portal B requires powered Power Armor with Portal Upgrade Card.");
   return;
  }''',
 '''  if(!hasUpgrade(player)){
   if(!dev.obsidiannetwork.powerarmor.PowerArmorRuntime.full(player))
    tell(player,"Portal B: complete matching Power Armor set required.");
   else if(!dev.obsidiannetwork.powerarmor.PowerArmorRuntime.hasCard(player,"portal"))
    tell(player,"Portal B: install Portal Upgrade Card at Armor Station.");
   else tell(player,"Portal B: charge all Power Armor pieces.");
   return;
  }''')

# Same 20 FE baseline as the runtime; tell the player what went wrong.
patch("client/NetworkVisionClient.java",
 'PowerArmorRuntime.tier(stack,i)!=tier||EnergyTool.energy(stack)<100L',
 'PowerArmorRuntime.tier(stack,i)!=tier||EnergyTool.energy(stack)<20L')
patch("client/NetworkVisionClient.java",
 '''   if(mc.screen==null&&ready())enabled=!enabled;''',
 '''   if(mc.screen==null&&mc.player!=null){
    if(ready()){
     enabled=!enabled;
     mc.player.sendOverlayMessage(net.minecraft.network.chat.Component.literal(
       enabled?"Network Vision: EIN":"Network Vision: AUS"));
    }else{
     enabled=false;
     mc.player.sendOverlayMessage(net.minecraft.network.chat.Component.literal(
       "Network Vision: volle, geladene Power Armor + Vision-Karte erforderlich"));
    }
   }''')

# Minecraft's modern item-model resolver requires a separate model in
# models/item, not merely an entry under models/block.
dump(R/"models/item/network_portal_a.json",{
 "parent":"obsidiannetwork:block/network_portal_a"
})
dump(R/"items/network_portal_a.json",{
 "model":{"type":"minecraft:model","model":"obsidiannetwork:item/network_portal_a"}
})
# All coordinates fit a standard 16x16x16 block. Previously the portal
# block-model had 31-high unbounded elements; these fail in some renderers.
# Keep the shape/portal functionality while making each model self-contained.
for kind,window in (("a","minecraft:block/purple_stained_glass"),
                    ("b","minecraft:block/light_blue_stained_glass")):
 name="network_portal_"+kind
 def elem(x1,y1,z1,x2,y2,z2,tex):
  return {"from":[x1,y1,z1],"to":[x2,y2,z2],
          "faces":{face:{"texture":"#"+tex} for face in
                    ("down","up","north","south","east","west")}}
 dump(R/("models/block/"+name+".json"),{
  "ambientocclusion":False,"render_type":"minecraft:translucent",
  "textures":{"frame":"minecraft:block/obsidian","window":window,
              "particle":"minecraft:block/obsidian"},
  "elements":[elem(1,0,6,3,16,10,"frame"),
              elem(13,0,6,15,16,10,"frame"),
              elem(3,14,6,13,16,10,"frame"),
              elem(3,0,6,13,2,10,"frame"),
              elem(3,2,7.5,13,14,8.5,"window")]})
# New registration now has both item + block keys, avoiding raw registry IDs
for language in ("de_de","en_us"):
 p=R/"lang"/(language+".json");data=json.loads(p.read_text())
 data["item.obsidiannetwork.network_portal_a"]=(
  "Netzwerkportal A" if language=="de_de" else "Network Portal A")
 dump(p,data)
# Opaque physical antennas: NEVER render as a translucent/see-through layer.
for name in ("network_signal_transmitter","network_signal_receiver"):
 p=R/("models/block/"+name+".json");obj=json.loads(p.read_text())
 obj["ambientocclusion"]=True
 obj["render_type"]="minecraft:solid"
 dump(p,obj)

# A held Blueprint must display a preview BEFORE the target is finalized.
# Client-only ghost is bounded and does not mutate world, or force chunk loads.
patch("client/NetworkBlueprintPreviewClient.java",
 '''  if(!origin.startsWith(prefix))return;
  String[] pos=origin.substring(prefix.length()).split("[|]");''',
 '''  if(!origin.startsWith(prefix)){
   if(!(mc.hitResult instanceof net.minecraft.world.phys.BlockHitResult hit))return;
   var p=hit.getBlockPos().relative(hit.getDirection());
   origin=prefix+p.getX()+"|"+p.getY()+"|"+p.getZ();
  }
  String[] pos=origin.substring(prefix.length()).split("[|]");''')
patch("client/NetworkBlueprintPreviewClient.java",
 'mc.player.tickCount%8!=0',
 'mc.player.tickCount%3!=0')
patch("client/NetworkBlueprintPreviewClient.java",
 'int count=0,phase=mc.player.tickCount/8%4;',
 'int count=0,phase=mc.player.tickCount/3%4;')

# Finalize only AFTER a fully successful print; no conversion if blocked,
# FE-starved, material-starved, paused or unloaded.
patch("blockentity/NetworkDeviceBlockEntity.java",
 '''  if(index>=plan.size()){running=false;setStatus("COMPLETE "+completed+"/"+plan.size());sync();return;}''',
 '''  if(index>=plan.size()){
   running=false;
   blueprint=new ItemStack(ObsidianNetwork.NETWORK_SCHEMATIC_QUILL.get());
   missing=ItemStack.EMPTY;
   setStatus("COMPLETE: Schematic & Quill returned");
   sync();return;
  }''')
patch("blockentity/NetworkDeviceBlockEntity.java",
 '''   index++;setStatus("SKIPPED BLOCKED POSITION "+index+"/"+plan.size());sync();return;''',
 '''   setStatus("BLOCKED: clear position "+dest.toShortString());return;''')
print("V173_BUILD204_FIELD_REPAIRS_PASS")
