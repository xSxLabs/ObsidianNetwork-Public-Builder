#!/usr/bin/env python3
"""B638: all seven reactor and five powerbank blocks need a pickaxe and
approximately one second mining with an unenchanted Netherite pickaxe.

Runs AFTER all v1.7.4 multiblock overlays and all v1.7.5 armor overlays.
Only hardness and existing mineable/pickaxe tags are concerned. Does NOT
touch reactor FE production, Powerbank energy IO, multiblock state, drops,
renderer, inventory, world ownership or stored BE data.
"""
import json,os,re,hashlib
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])
ids=(
 "reactor_casing","reactor_glass","reactor_fuel_assembly",
 "reactor_item_port","reactor_fluid_port","reactor_power_port","reactor_controller",
 "powerbank_casing","powerbank_glass","powerbank_controller",
 "powerbank_input_port","powerbank_output_port",
)
assert len(ids)==12 and len(set(ids))==12
mod=J/"ObsidianNetwork.java"
before=mod.read_text(encoding="utf-8")
s=before
for name in ids:
 # Match ONLY the single registration for this exact block ID. v1.7.4's
 # existing correct-tool drop checks remain in place for every component.
 pat=re.compile(
  r'(BLOCKS\.registerBlock\("'+re.escape(name)+
  r'",[^\n]*\n[ \t]*p\s*->\s*p\.mapColor\(MapColor\.METAL\)\.strength\()'
  r'([0-9.]+F)(,9\.0F\)\.requiresCorrectToolForDrops\(\)\);)')
 hits=list(pat.finditer(s))
 assert len(hits)==1,("B638_REACTOR_POWERBANK_REGISTERED_BLOCK_DRIFT",name,len(hits))
 old=hits[0].group(2)
 assert old in ("3.5F","3.0F"),(name,"expected original hardness",old)
 s=s[:hits[0].start(2)]+"6.0F"+s[hits[0].end(2):]
assert s!=before
mod.write_text(s,encoding="utf-8")
# 6.0 hardness @ tool speed 9 (Netherite) -> 30*6/9 = 20 server
# ticks, around 1 second without Efficiency/Haste effects.
# Diamond pickaxe speed 8 -> about 23 ticks. Mining time is NOT
# absolute: real speed depends on the tool/enchantments/status.
tag=R/"data/minecraft/tags/block/mineable/pickaxe.json"
data=json.loads(tag.read_text(encoding="utf-8"))
assert isinstance(data.get("values"),list)
values=data["values"]
for name in ids:
 key="obsidiannetwork:"+name
 assert values.count(key)==1,("B638_PICKAXE_TAG",key,values.count(key))
assert all(s.count(f'BLOCKS.registerBlock("{name}"')==1 for name in ids)
for name in ids:
 m=re.search(r'BLOCKS\.registerBlock\("'+re.escape(name)+r'",[^\n]*\n[ \t]*p\s*->\s*p\.mapColor\(MapColor\.METAL\)\.strength\(6\.0F,9\.0F\)\.requiresCorrectToolForDrops\(\)\);',s)
 assert m,(name,"pickaxe-only loot and >0 hardness missing")
print("V175_B638_ALL_REACTOR_POWERBANK_PICKAXE_PASS: 7 reactor + 5 powerbank blocks; hardness 6.0, correct-tool required, all 12 mineable/pickaxe; ~20 ticks Netherite; no gameplay changes")
