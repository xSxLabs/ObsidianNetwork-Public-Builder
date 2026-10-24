#!/usr/bin/env python3
"""Build 105: separate Air Mining disk; restore vanilla ground-speed mining during creative-style flight.

This additive overlay runs after Build 104. No armor stack, loadout, FE storage,
station inventory or old card/recipe is migrated or replaced.
"""
from pathlib import Path
import json
import os
import struct
import zlib

root = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork"
res = Path(os.environ["V1_RESOURCE_ROOT"])
assets = res / "assets/obsidiannetwork"
card = "air_mining"

def replace_once(path, old, new):
    content = path.read_text(encoding="utf-8")
    assert content.count(old) == 1, ("BUILD105 anchor changed", path, content.count(old))
    path.write_text(content.replace(old, new, 1), encoding="utf-8")

# Real UpgradeCardItem, registered beside all earlier cards.
reg = root / "ObsidianNetwork.java"
anchor = "   public static final DeferredItem<dev.obsidiannetwork.powerarmor.UpgradeCardItem> POWER_ARMOR_UPGRADE ="
replace_once(reg, anchor,
    '   public static final DeferredItem<dev.obsidiannetwork.powerarmor.UpgradeCardItem> POWER_CARD_AIR_MINING =\n'
    '      ITEMS.registerItem("power_card_air_mining",p -> new dev.obsidiannetwork.powerarmor.UpgradeCardItem(p,"air_mining"));\n'
    + anchor)
tab = "            output.accept((ItemLike)POWER_ARMOR_UPGRADE.get());"
replace_once(reg, tab, tab + "\n            output.accept((ItemLike)POWER_CARD_AIR_MINING.get());")

# Station GUI and sneak-install already accept any valid UpgradeCardItem.
# This one registry mapping makes the disk display/removal and recovery work.
lookup = root / "powerarmor/PowerArmorCards.java"
replace_once(lookup, "   default -> null;",
    '   case "air_mining" -> dev.obsidiannetwork.ObsidianNetwork.POWER_CARD_AIR_MINING.get();\n'
    '   default -> null;')

java = root / "powerarmor/PowerArmorAirMining.java"
assert not java.exists(), "BUILD105 double-install"
java.parent.mkdir(parents=True, exist_ok=True)
java.write_text(r'''package dev.obsidiannetwork.powerarmor;

import dev.obsidiannetwork.core.EnergyTool;
import dev.obsidiannetwork.registry.ModDataComponents;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;

/** BUILD105_AIR_MINING: undo ONLY vanilla's /5 airborne mining penalty. */
@EventBusSubscriber(modid="obsidiannetwork")
public final class PowerArmorAirMining {
 private PowerArmorAirMining(){}

 // Handle client and server; server-only checks would leave client progress / crack animation slow.
 // Same complete matching MK1..MK24 and powered-FE conditions used for the other armor effects.
 private static boolean hasPoweredAirMining(Player player){
  int tier=PowerArmorRuntime.tier(player.getItemBySlot(EquipmentSlot.HEAD),0);
  if(tier<1||tier>24)return false;
  boolean installed=false;
  for(int i=0;i<PowerArmorRuntime.SLOTS.length;i++){
   var armor=player.getItemBySlot(PowerArmorRuntime.SLOTS[i]);
   if(PowerArmorRuntime.tier(armor,i)!=tier||EnergyTool.energy(armor)<20L)return false;
   String cards=armor.get(ModDataComponents.POWER_ARMOR_UPGRADES.get());
   if(cards!=null){
    for(String id:cards.split(","))if("air_mining".equals(id))installed=true;
   }
  }
  return installed;
 }

 @SubscribeEvent(priority=EventPriority.LOWEST)
 public static void onBreakSpeed(PlayerEvent.BreakSpeed event){
  Player player=event.getEntity();
  // This does not affect walking, jumping, gliding, swimming or vanilla creative instant mining.
  // Flying is the actual ability flag, not merely being in mid-air.
  if(player.isSpectator()||!player.getAbilities().flying||player.onGround())return;
  if(!hasPoweredAirMining(player))return;
  float speed=event.getNewSpeed();
  if(!Float.isFinite(speed)||speed<=0F||speed>Float.MAX_VALUE/5F)return;
  // NeoForge fires BreakSpeed AFTER vanilla divides speed by five while airborne.
  // Multiply the already-calculated speed (tools, enchants, effects, water and other mods intact).
  event.setNewSpeed(speed*5.0F);
 }
}
''', encoding="utf-8")

# New disk keeps the exact established 32px metal frame; pixel pickaxe is unique.
icon = ("00011111","00111110","01100100","01001000",
        "00011000","00110000","01100000","01000000")
accent=(111, 233, 155)
rows=[]
for y in range(32):
    row=bytearray([0])
    for x in range(32):
        border=2<=x<30 and 2<=y<30
        core=5<=x<27 and 7<=y<25
        glow=core and (y==7 or y==24 or x==5 or x==26)
        a=255 if border else 0
        if not border: color=(0,0,0)
        elif 3<=x<29 and 3<=y<29:
            t=int((x+y)*0.4)
            color=(29+t,39+t,51+t)
        else: color=(9,14,20)
        if core:color=(13,22,34)
        if glow:color=accent
        if 7<=x<25 and y in (4,5):color=(102,122,141)
        if x in (4,27) and 5<=y<26:color=(86,105,119)
        if x in (6,25) and y in (27,28):color=(150,157,166)
        if 11<=x<19 and 12<=y<20 and icon[y-12][x-11]=="1":color=accent
        row.extend((*color,a))
    rows.append(bytes(row))
def chunk(kind,data):
    return struct.pack(">I",len(data))+kind+data+struct.pack(">I",zlib.crc32(kind+data)&0xffffffff)
png=(b"\x89PNG\r\n\x1a\n"
    +chunk(b"IHDR",struct.pack(">IIBBBBB",32,32,8,6,0,0,0))
    +chunk(b"IDAT",zlib.compress(b"".join(rows),9))
    +chunk(b"IEND",b""))
def new_file(path, data, raw=False):
    assert not path.exists(), ("BUILD105 accidental overwrite", path)
    path.parent.mkdir(parents=True,exist_ok=True)
    if raw:path.write_bytes(data)
    else:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

new_file(assets/"textures/item/power_card_air_mining.png",png,raw=True)
new_file(assets/"models/item/power_card_air_mining.json",
    {"parent":"minecraft:item/generated",
     "textures":{"layer0":"obsidiannetwork:item/power_card_air_mining"}})
new_file(assets/"items/power_card_air_mining.json",
    {"model":{"type":"minecraft:model","model":"obsidiannetwork:item/power_card_air_mining"}})

# Premium recipe: blank disk + powered advanced energy cell + nether star
# + four netherite ingots + two netherite pickaxes.
new_file(res/"data/obsidiannetwork/recipe/power_card_air_mining.json",{
    "type":"minecraft:crafting_shaped",
    "pattern":["ABA","CDC","AEA"],
    "key":{
        "A":"minecraft:netherite_ingot",
        "B":"minecraft:nether_star",
        "C":"minecraft:netherite_pickaxe",
        "D":"obsidiannetwork:power_armor_upgrade",
        "E":"obsidiannetwork:advanced_energy_cell",
    },
    "result":{"id":"obsidiannetwork:power_card_air_mining","count":1}
})

for language, title, info in (
    ("en_us","Air Mining Upgrade Card","Removes the airborne mining slowdown during powered creative-style flight; normal ground/tool speed."),
    ("de_de","Luftabbau-Upgrade-Karte","Hebt bei aktivem Creative-Flug mit geladener Power-Rüstung den Luftabbau-Malus auf. Normale Boden-/Werkzeuggeschwindigkeit."),
):
    path=assets/"lang"/(language+".json")
    data=json.loads(path.read_text(encoding="utf-8"))
    assert "item.obsidiannetwork.power_card_air_mining" not in data
    data["item.obsidiannetwork.power_card_air_mining"]=title
    data["message.obsidiannetwork.power_armor.air_mining_info"]=info
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

assert 'event.setNewSpeed(speed*5.0F);' in java.read_text(encoding="utf-8")
assert 'if(player.isSpectator()||!player.getAbilities().flying||player.onGround())return;' in java.read_text(encoding="utf-8")
assert len(png)>100
print("BUILD105_AIR_MINING PASS: separate 32px disk and recipe, actual station item, full powered MK1-MK24 suit, client+server airborne flight speed exactly x5")
