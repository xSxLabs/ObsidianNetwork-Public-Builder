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
def find_registration(code,name):
 # The exact block ID is a stable registry contract; do not assume the
 # property lambda is formatted over exactly two lines. Lighting and
 # occlusion patches legitimately extend these property chains.
 starts=list(re.finditer(
   r'BLOCKS\.registerBlock\s*\(\s*"'+re.escape(name)+r'"\s*,',code))
 assert len(starts)==1,("B639_BLOCK_REGISTRY_DRIFT",name,len(starts))
 start=starts[0].start()
 end=code.find(");",start)
 assert start<end and end-start<1200,("B639_REGISTRATION_BOUNDARY",name,code[start:start+350])
 return start,end+2,code[start:end+2]

for name in ids:
 start,end,entry=find_registration(s,name)
 # B640: The CURRENT multiblock skin is intentionally installed as
 # .strength(0.0F,0.0F) WITHOUT a correct-tool requirement by a later v1.7.4
 # reconstruction patch. Reapply actual survival mining properties HERE,
 # after all legacy overlays. Don't change constructor, noOcclusion, geometry,
 # render state or multiblock logic. All 12 names get the same rule.
 hits=list(re.finditer(
   r'\.strength\(\s*([0-9]+(?:\.[0-9]+)?F)\s*,\s*([0-9]+(?:\.[0-9]+)?F)\s*\)',entry))
 assert len(hits)==1,("B640_STRENGTH_DRIFT",name,len(hits),entry)
 strength=hits[0]
 old_hard,old_blast=strength.group(1),strength.group(2)
 assert old_hard in ("0.0F","3.0F","3.5F","6.0F"),(
   "B640_UNEXPECTED_EXISTING_HARDNESS",name,old_hard)
 assert old_blast in ("0.0F","9.0F"),(
   "B640_UNEXPECTED_EXISTING_BLAST_RESISTANCE",name,old_blast)
 has_tool=".requiresCorrectToolForDrops()" in entry
 replacement=".strength(6.0F,9.0F)"+("" if has_tool else ".requiresCorrectToolForDrops()")
 entry=entry[:strength.start()]+replacement+entry[strength.end():]
 s=s[:start]+entry+s[end:]
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
for name in ids:
 _start,_end,entry=find_registration(s,name)
 assert ".requiresCorrectToolForDrops()" in entry,(name,"wrong tool drops")
 assert len(re.findall(
   r'\.strength\(\s*6\.0F\s*,\s*[0-9]+(?:\.[0-9]+)?F\s*\)',
   entry))==1,(name,"mining hardness was not updated",entry)

print("V175_B640_ALL_REACTOR_POWERBANK_PICKAXE_PASS: 7 reactor + 5 powerbank blocks; hardness 6.0, correct-tool required, all 12 mineable/pickaxe; ~20 ticks Netherite; no gameplay changes")
