#!/usr/bin/env python3
"""B584 exact match of all red item import collar coordinates to blue, plus
unchanged runtime FE contracts."""
import json,os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
s=(J/"client/EnergyCableInputRenderer.java").read_text()
assert "B584_ITEM_CABLE_IDENTICAL_INPUT" in s
assert "XSX_ENERGY_INPUT_COLLAR.get().defaultBlockState()" in s
assert "BLACK_CONCRETE" not in s and "Blocks.IRON_BLOCK.defaultBlockState()" not in s
assert s.count("cap(state,pose,collector,")==6
assert "dark(state" not in s
geometries=[
 ("down","[6.0, 0.0, 6.0]","[10.0, 2.0, 10.0]"),
 ("up","[6.0, 14.0, 6.0]","[10.0, 16.0, 10.0]"),
 ("north","[6.0, 6.0, 0.0]","[10.0, 10.0, 2.0]"),
 ("south","[6.0, 6.0, 14.0]","[10.0, 10.0, 16.0]"),
 ("west","[0.0, 6.0, 6.0]","[2.0, 10.0, 10.0]"),
 ("east","[14.0, 6.0, 6.0]","[16.0, 10.0, 10.0]")]
for d,_,_ in geometries:
 red=json.loads((A/"models/block"/("item_cable_input_"+d+".json")).read_text())
 blue=json.loads((A/"models/block"/("energy_cable_input_"+d+".json")).read_text())
 assert red["elements"]==blue["elements"],("GEOMETRY_DRIFT",d)
 assert blue["textures"]["all"]=="obsidiannetwork:block/energy_cable"
 assert blue["textures"]["particle"]=="obsidiannetwork:block/energy_cable"
 a=blue["elements"][1]
 assert all(float(z)>float(x) for x,z in zip(a["from"],a["to"]))
assert (A/"textures/block/xsx_energy_input_collar.png").read_bytes()==(A/"textures/block/energy_cable.png").read_bytes()
expected=[
 "cap(state,pose,collector,6/16f,0,6/16f,4/16f,2/16f,4/16f)",
 "cap(state,pose,collector,6/16f,14/16f,6/16f,4/16f,2/16f,4/16f)",
 "cap(state,pose,collector,6/16f,6/16f,0,4/16f,4/16f,2/16f)",
 "cap(state,pose,collector,6/16f,6/16f,14/16f,4/16f,4/16f,2/16f)",
 "cap(state,pose,collector,0,6/16f,6/16f,2/16f,4/16f,4/16f)",
 "cap(state,pose,collector,14/16f,6/16f,6/16f,2/16f,4/16f,4/16f)"
]
assert all(a in s for a in expected),("COLLAR_REGION_NOT_EQUAL_TO_RED",expected)
r=(J/"reactor/ReactorControllerBlockEntity.java").read_text()
assert "B579_REACTOR_GENERATE_EVERY_TICK" in r
assert "B581_REACTOR_CACHE" in r
assert "b581CachedSink(world,at,next,dir)" in r
print("B584_SIX_FACE_ITEM_CABLE_PIXEL_AND_GEOMETRY_PARITY_FE_UNCHANGED_PASS")
