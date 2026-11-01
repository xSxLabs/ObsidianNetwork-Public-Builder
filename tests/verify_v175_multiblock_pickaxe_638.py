#!/usr/bin/env python3
"""B638 generated source contract, all 12 blocks and existing loot."""
import os,re,json
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])
names=["reactor_casing","reactor_glass","reactor_fuel_assembly",
"reactor_item_port","reactor_fluid_port","reactor_power_port","reactor_controller",
"powerbank_casing","powerbank_glass","powerbank_controller",
"powerbank_input_port","powerbank_output_port"]
s=(J/"ObsidianNetwork.java").read_text(encoding="utf-8")
t=json.loads((R/"data/minecraft/tags/block/mineable/pickaxe.json").read_text(encoding="utf-8"))
assert len(names)==12
for n in names:
 assert len(re.findall(r'BLOCKS\.registerBlock\("'+n+'"',s))==1,n
 p=(r'BLOCKS\.registerBlock\("'+n+r'",[^\n]*\n'
    r'[ \t]*p\s*->\s*p\.mapColor\(MapColor\.METAL\)'
    r'\.strength\(6\.0F,9\.0F\)\.requiresCorrectToolForDrops\(\)\);')
 assert re.search(p,s),("hardness/tool",n)
 assert t["values"].count("obsidiannetwork:"+n)==1,("tag",n)
 loot=R/"data/obsidiannetwork/loot_table/blocks"/(n+".json")
 assert loot.exists(),("original drops not found",n)
 # Loot must remain the original corresponding block and not be replaced
 # by a newly generated texture, item or unrelated drop.
 j=json.loads(loot.read_text(encoding="utf-8"))
 entries=j["pools"][0]["entries"]
 assert any(e.get("name")=="obsidiannetwork:"+n for e in entries),(n,entries)
 assert (R/"assets/obsidiannetwork/blockstates"/(n+".json")).exists(),n
print("V175_B638_12_SURVIVAL_PICKAXE_HARDNESS_LOOT_GATE_PASS")
