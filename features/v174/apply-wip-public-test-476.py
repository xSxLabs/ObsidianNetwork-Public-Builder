#!/usr/bin/env python3
"""B476: expose inherited v1.7.3 hologram, printer and schematic systems in v1.7.4.

Build 398 hid functional registry entries while the machines were WIP. Keep
their registry and save IDs untouched. 1.7.4 explicitly includes them in
the full integrated in-game test candidate, so remove only the discovery
barrier and restore recipes. Do not silently claim gameplay is verified.
"""
import json
import os
from pathlib import Path

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
res=Path(os.environ["V1_RESOURCE_ROOT"])
main=root/"ObsidianNetwork.java"
src=main.read_text(encoding="utf-8")
anchor="            output.accept((ItemLike)NETWORK_PLANTER_ITEM.get());"
assert src.count(anchor)==1,("B476_CREATIVE_ANCHOR_DRIFT",src.count(anchor))
fields=(
 "NETWORK_HOLOGRAM_TERMINAL_ITEM",
 "NETWORK_PRINTER_ITEM",
 "NETWORK_BLUEPRINT",
 "NETWORK_SCHEMATIC_QUILL",
)
for field in fields:
 assert field in src,("B476_REGISTRY_MISSING",field)
 assert "output.accept((ItemLike)"+field+".get())" not in src,("B476_ALREADY_PUBLIC",field)
insertion="\n".join("            output.accept((ItemLike)"+field+".get());" for field in fields)
src=src.replace(anchor,anchor+"\n"+insertion,1)
main.write_text(src,encoding="utf-8")

# B398 introduced the entire plugin solely to hide these four items from JEI.
# Deleting that generated file does not touch any stored data or recipe handler.
hidden=root/"compat/jei/WipItemsJeiPlugin.java"
assert hidden.is_file() and "B398_WIP_JEI_HIDE" in hidden.read_text(encoding="utf-8")
hidden.unlink()

recipes={
 "network_hologram_terminal":{
  "type":"minecraft:crafting_shaped","category":"misc",
  "pattern":["GEG","RCR","IOI"],
  "key":{"G":"minecraft:glass_pane","E":"minecraft:ender_eye",
         "R":"minecraft:redstone","C":"obsidiannetwork:network_cable",
         "I":"minecraft:iron_ingot","O":"minecraft:obsidian"},
  "result":{"id":"obsidiannetwork:network_hologram_terminal","count":1}},
 "network_printer":{
  "type":"minecraft:crafting_shaped","category":"misc",
  "pattern":["IPI","RCR","IDI"],
  "key":{"I":"minecraft:iron_ingot","P":"minecraft:piston",
         "R":"minecraft:redstone","C":"minecraft:crafting_table",
         "D":"minecraft:diamond"},
  "result":{"id":"obsidiannetwork:network_printer","count":1}},
 "network_schematic_quill":{
  "type":"minecraft:crafting_shaped","category":"misc",
  "pattern":["  F"," P ","G  "],
  "key":{"F":"minecraft:feather","P":"minecraft:paper",
         "G":"minecraft:gold_ingot"},
  "result":{"id":"obsidiannetwork:network_schematic_quill","count":1}}
}
for name,recipe in recipes.items():
 target=res/"data/obsidiannetwork/recipe"/(name+".json")
 assert not target.exists(),("B476_RECIPE_ID_COLLISION",str(target))
 target.parent.mkdir(parents=True,exist_ok=True)
 target.write_text(json.dumps(recipe,indent=2)+"\n",encoding="utf-8")
assert "NETWORK_HOLOGRAM_TERMINAL.get()" in (root/"registry/ModBlockEntities.java").read_text(encoding="utf-8")
assert "NETWORK_PRINTER.get()" in (root/"registry/ModBlockEntities.java").read_text(encoding="utf-8")
print("B476_V174_WIP_PUBLIC_TEST_PASS: Hologram, Printer, Blueprint, Quill visible; recipes returned; registry/save IDs preserved")
