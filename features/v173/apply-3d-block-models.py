#!/usr/bin/env python3
"""Build174: custom cuboid geometry for real 3D signal antennas and machines."""
from pathlib import Path
import os,json
R=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
T={"case":"minecraft:block/iron_block","dark":"minecraft:block/polished_deepslate",
 "light":"minecraft:block/light_blue_concrete","orange":"minecraft:block/orange_concrete",
 "glass":"minecraft:block/cyan_stained_glass","blueprint":"minecraft:block/blue_concrete"}
def box(a,b,material):
 return {"from":list(a),"to":list(b),"faces":{
  face:{"texture":"#"+material} for face in ("down","up","north","south","west","east")}}
def write(slug,elements):
 tex={**T,"particle":T["case"]}
 base={"textures":tex,"elements":elements}
 for rel,data in [
  ("models/block/"+slug+".json",base),
  ("blockstates/"+slug+".json",{"variants":{"":{"model":"obsidiannetwork:block/"+slug}}}),
  ("models/item/"+slug+".json",{"parent":"obsidiannetwork:block/"+slug}),
  ("items/"+slug+".json",{"model":{"type":"minecraft:model","model":"obsidiannetwork:item/"+slug}})]:
  p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
  p.write_text(json.dumps(data,indent=2)+"\n")
for slug,tip in [("network_signal_transmitter","orange"),("network_signal_receiver","light")]:
 e=[box((2,0,2),(14,3,14),"case"),
  box((4,3,4),(12,5,12),"dark"),box((7,5,7),(9,16,9),"case"),
  box((6,8,6),(10,10,10),tip),box((4,13,7),(12,14,9),tip),
  box((7,13,4),(9,14,12),tip),box((5,10,7),(11,11,9),"dark"),
  box((7,10,5),(9,11,11),"dark"),box((6,15,6),(10,16,10),tip),
  box((1,1,6),(3,3,10),"dark"),box((13,1,6),(15,3,10),"dark")]
 write(slug,e)
printer=[box((0,0,0),(16,2,16),"case"),box((2,2,3),(14,4,13),"blueprint")]
for x,z in [(1,1),(13,1),(1,13),(13,13)]:
 printer.append(box((x,2,z),(x+2,16,z+2),"case"))
printer += [
 box((2,14,1),(14,16,3),"case"),box((2,14,13),(14,16,15),"case"),
 box((2,13,2),(14,15,14),"case"),box((6,12,6),(10,13,10),"dark"),
 box((7,6,7),(9,12,9),"case"),box((7,4,7),(9,6,9),"orange"),
 box((3,4,0),(13,12,1),"dark"),box((4,6,0),(12,10,1),"glass"),
 box((5,10,0),(11,12,1),"light"),box((3,4,14),(13,5,16),"case")]
write("network_printer",printer)
hologram=[box((1,0,1),(15,3,15),"case"),
 box((3,3,3),(13,5,13),"dark"),box((6,5,6),(10,7,10),"light"),
 box((4,7,4),(12,8,12),"glass"),box((3,8,3),(13,9,13),"light"),
 box((4,9,4),(12,10,12),"glass"),box((5,10,5),(11,11,11),"light"),
 box((6,11,6),(10,14,10),"glass")]
for x,z in ((2,2),(12,2),(2,12),(12,12)):
 hologram.append(box((x,2,z),(x+2,4,z+2),"light"))
write("network_hologram_terminal",hologram)
print("V173_CUSTOM_3D_BLOCK_MODELS174_PASS")
