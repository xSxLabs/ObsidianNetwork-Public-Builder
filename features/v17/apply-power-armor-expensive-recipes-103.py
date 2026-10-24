#!/usr/bin/env python3
"""Build 103: balanced, expensive Power Armor MK1-MK24 and module recipes.

Every armor piece consumes exactly ONE real ObsidianNetwork Basic Energy Cell.
Every MK is cosmetic: identical input cost, except unique color dyes.
The 23 enabled module cards require an expensive empty upgrade board and
large, distinct ingredient costs. Never mutate saved items, JEI state,
upgrades on existing suits, or any registration.
Run AFTER Build93's MK recipes and the Build98 presentation patches.
"""
import ast
import json
import os
from pathlib import Path

resources=Path(os.environ["V1_RESOURCE_ROOT"])
recipes=resources/"data/obsidiannetwork/recipe"
asset=resources/"assets/obsidiannetwork"
script=Path(__file__).with_name("apply-power-armor-bundle-93.py")
source=ast.parse(script.read_text(encoding="utf-8"))
def literal_assignment(name):
 for node in source.body:
  if isinstance(node,ast.Assign) and any(isinstance(n,ast.Name) and n.id==name for n in node.targets):
   return ast.literal_eval(node.value)
 raise AssertionError("Build103 missing palette source: "+name)
palettes=literal_assignment("finishes")
trim_dyes=literal_assignment("new_trim_dyes")
assert set(palettes)==set(range(3,25))
assert set(trim_dyes)==set(range(13,25))

# Dye pairs for MK1..MK12 preserve historical red/gold, graphite/steel and
# MK3..MK12 color identities, without touching existing icon PNGs.
legacy_trim={
 1:("red_dye","yellow_dye"),2:("black_dye","light_gray_dye"),
 3:("blue_dye","light_gray_dye"),4:("white_dye","blue_dye"),
 5:("green_dye","yellow_dye"),6:("red_dye","gray_dye"),
 7:("purple_dye","magenta_dye"),8:("cyan_dye","orange_dye"),
 9:("magenta_dye","light_gray_dye"),10:("orange_dye","light_blue_dye"),
 11:("lime_dye","yellow_dye"),12:("light_blue_dye","blue_dye"),
}
assert len(legacy_trim)==12
dye_pairs=dict(legacy_trim)
for tier in range(13,25):
 dye_pairs[tier]=(palettes[tier][4],trim_dyes[tier])
assert set(dye_pairs)==set(range(1,25))
assert len(set(dye_pairs.values()))==24,"Duplicate MK color recipes"
assert all(dye_pairs[t][0]==palettes[t][4] for t in range(3,25))

CELL="obsidiannetwork:basic_energy_cell"
PARTS={
 "helmet":"netherite_helmet",
 "chestplate":"netherite_chestplate",
 "leggings":"netherite_leggings",
 "boots":"netherite_boots",
}

def write_recipe(key,obj):
 p=recipes/(key+".json")
 assert p.is_file(),f"Build103 missing historical recipe {key}"
 old=json.loads(p.read_text(encoding="utf-8"))
 assert old["result"]["id"]=="obsidiannetwork:"+key,("Unexpected output",key)
 assert old["result"].get("count",1)==1,("Unrecognized prior recipe",key)
 p.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")

# 3 netherite ingots + 2 diamond blocks + 1 original netherite piece
# + exactly one Basic Energy Cell + two distinctive suit colors.
# A N A    A=netherite ingot (2), N=cell (1)
# B C B    B=diamond block (2), C=base netherite armor (1)
# D E F    D+E=armor dyes (2), F=netherite ingot (1)
# Nine filled recipe slots, no ambiguous matching across MKs.
armor_signatures=set()
for tier in range(1,25):
 for part,netherite_item in PARTS.items():
  ident="power_armor_"+(f"mk{tier}_" if tier>1 else "")+part
  assert (asset/"items"/(ident+".json")).is_file(),("Unknown armor item",ident)
  primary,secondary=dye_pairs[tier]
  obj={
   "type":"minecraft:crafting_shaped",
   "pattern":["ANA","BCB","DEF"],
   "key":{
    "A":"minecraft:netherite_ingot",
    "N":CELL,
    "B":"minecraft:diamond_block",
    "C":"minecraft:"+netherite_item,
    "D":"minecraft:"+primary,
    "E":"minecraft:"+secondary,
    "F":"minecraft:netherite_ingot",
   },
   "result":{"id":"obsidiannetwork:"+ident,"count":1},
  }
  signature=json.dumps([obj["pattern"],obj["key"]],sort_keys=True)
  assert signature not in armor_signatures,("Duplicate MK recipe",ident)
  armor_signatures.add(signature)
  assert sum(obj["key"].get(ch)==CELL for row in obj["pattern"] for ch in row)==1
  write_recipe(ident,obj)
assert len(armor_signatures)==96

# Physical, blank upgrade circuit/disk. Same base board used by every card.
BOARD="obsidiannetwork:power_armor_upgrade"
write_recipe("power_armor_upgrade",{
 "type":"minecraft:crafting_shaped",
 "pattern":["IRI","NCN","IRI"],
 "key":{
  "I":"minecraft:netherite_ingot",   # 4
  "R":"minecraft:redstone_block",    # 2
  "N":"minecraft:diamond_block",    # 2
  "C":"minecraft:copper_block",     # 1
 },
 "result":{"id":BOARD,"count":1},
})

# The same 25 original card types exist, but these two obsolete upgrades
# remain deliberately uncraftable as they were in Build101.
FEATURE_INGREDIENT={
 "flight":"minecraft:elytra",
 "night_vision":"minecraft:golden_carrot",
 "water_breathing":"minecraft:heart_of_the_sea",
 "protection":"minecraft:netherite_ingot",
 "fire_protection":"minecraft:magma_cream",
 "blast_protection":"minecraft:obsidian",
 "projectile_protection":"minecraft:shield",
 "feather_falling":"minecraft:phantom_membrane",
 "respiration":"minecraft:nautilus_shell",
 "aqua_affinity":"minecraft:prismarine_crystals",
 "thorns":"minecraft:cactus",
 "depth_strider":"minecraft:prismarine_shard",
 "frost_walker":"minecraft:blue_ice",
 "soul_speed":"minecraft:soul_soil",
 "swift_sneak":"minecraft:echo_shard",
 "strength":"minecraft:blaze_rod",
 "resistance":"minecraft:nether_star",
 "speed":"minecraft:sugar",
 "haste":"minecraft:beacon",
 "regeneration":"minecraft:totem_of_undying",
 "fire_resistance":"minecraft:ancient_debris",
 "jump_boost":"minecraft:rabbit_foot",
 "network_elytra":"obsidiannetwork:network_elytra",
 "energy_shield":"obsidiannetwork:advanced_energy_cell",
}
RARE={
 "flight","strength","resistance","speed","haste",
 "regeneration","fire_resistance","jump_boost","network_elytra","energy_shield",
}
assert len(FEATURE_INGREDIENT)==24 and RARE<=set(FEATURE_INGREDIENT)
card_signatures=set()
for card,token in FEATURE_INGREDIENT.items():
 ident="power_card_"+card
 assert (asset/"items"/(ident+".json")).is_file(),ident
 rare=card in RARE
 obj={
  "type":"minecraft:crafting_shaped",
  "pattern":["ABA","CDC","AEA"],
  "key":{
   "A":"minecraft:netherite_ingot" if rare else "minecraft:iron_block",
   "B":"minecraft:nether_star" if rare else "minecraft:redstone_block",
   "C":token,
   "D":BOARD,
   "E":"minecraft:diamond_block",
  },
  "result":{"id":"obsidiannetwork:"+ident,"count":1},
 }
 signature=json.dumps([obj["pattern"],obj["key"]],sort_keys=True)
 assert signature not in card_signatures,("Duplicate module card",card)
 card_signatures.add(signature)
 write_recipe(ident,obj)
assert len(card_signatures)==24
for disabled in ("mending","unbreaking"):
 obsolete=recipes/("power_card_"+disabled+".json")
 if obsolete.exists():obsolete.unlink()
 assert not obsolete.exists(),disabled

# Source integrity: the generator only touches recipes from existing items;
# all completed suits, SavedData backups, station inventories and FE remain
# exactly as they were before the overlay.
print("BUILD103_POWER_ARMOR_EXPENSIVE_RECIPES PASS: 96 armor recipes, one Basic Energy Cell per item, uniform MK1..MK24 price, unique dyes, one premium blank board, 24 costly upgrade cards and 2 disabled legacy cards")
