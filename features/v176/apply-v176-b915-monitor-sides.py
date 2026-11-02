#!/usr/bin/env python3
"""B915: restore original Power Monitor casing on non-front faces."""
import os,json
from pathlib import Path
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
dst=A/"models/block/power_terminal.json"
ref=A/"models/block/powerbank_controller.json"
assert dst.is_file() and ref.is_file()
before=json.loads(dst.read_text())
assert before["textures"]["north"]=="obsidiannetwork:block/power_terminal_computer_front"
source=json.loads(ref.read_text())
tex=source.get("textures",{})
def find(*names):
 for name in names:
  val=tex.get(name)
  if isinstance(val,dict):val=val.get("sprite")
  if isinstance(val,str) and val.startswith("#"):val=tex.get(val[1:])
  if isinstance(val,str) and not val.startswith("#"):return val
 return "minecraft:block/iron_block"
side=find("side","all","particle","north","front")
top=find("up","top","all","side")
bottom=find("down","bottom","all","side")
back=find("south","back","all","side")
dst.write_text(json.dumps({"parent":"minecraft:block/cube","textures":{
 "particle":side,"north":"obsidiannetwork:block/power_terminal_computer_front",
 "south":back,"east":side,"west":side,"up":top,"down":bottom
}},indent=2)+"\n")
print("B915_POWER_MONITOR_FRONT_ONLY_OLD_SIDE_MATERIALS_PASS")
