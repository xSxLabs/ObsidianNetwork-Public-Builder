#!/usr/bin/env python3
"""B584 exact red Item Cable input geometry cloned for blue Energy Cable.
No simulation / BlockState / capability changes, only visual shape and atlas.
"""
import json,os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
p=J/"client/EnergyCableInputRenderer.java"
s=p.read_text(encoding="utf-8")
def once(old,new):
 global s
 assert s.count(old)==1,("B584_COLLAR_SOURCE_DRIFT",old[:100],s.count(old))
 s=s.replace(old,new,1)

# Keep renderer's six independent INPUT flags, actual energy-cable stem and
# true block light; remove BOTH fake oversized black frame and cyan center.
once("  public final BlockModelRenderState dark=new BlockModelRenderState();\n","")
once("  if(out.active)resolver.update(out.dark,Blocks.BLACK_CONCRETE.defaultBlockState(),DISPLAY);","")
# B552 already replaced the iron model with the registered solid collar.
# Retain it when present; only adapt an older iron-backed source if needed.
actual="resolver.update(out.cap,dev.obsidiannetwork.ObsidianNetwork.XSX_ENERGY_INPUT_COLLAR.get().defaultBlockState(),DISPLAY);"
if actual not in s:
 once("resolver.update(out.cap,Blocks.IRON_BLOCK.defaultBlockState(),DISPLAY);",actual)
else:
 assert s.count(actual)==1,("B588_DUPLICATE_BLUE_MODEL",s.count(actual))
start=s.index(" // B579_ENERGY_INPUT_BLACK_FRAME:")
end=s.index(" @Override public void submit(InputState state,PoseStack pose,",start)
s=s[:start]+''' // B584_ITEM_CABLE_IDENTICAL_INPUT: 4/16 wide, 2/16 thick per
 // original item_cable_input_{direction}.json, with energy cable atlas.
'''+s[end:]
# Use exact original input collar shape and position in *all* six directions.
# 0 DOWN 1 UP 2 NORTH 3 SOUTH 4 WEST 5 EAST (get3DDataValue).
src=["if(state.input[0]){dark(","if(state.input[1]){dark(","if(state.input[2]){dark(",
     "if(state.input[3]){dark(","if(state.input[4]){dark(","if(state.input[5]){dark("]
target=[
 "if(state.input[0])cap(state,pose,collector,6/16f,0,6/16f,4/16f,2/16f,4/16f);",
 "if(state.input[1])cap(state,pose,collector,6/16f,14/16f,6/16f,4/16f,2/16f,4/16f);",
 "if(state.input[2])cap(state,pose,collector,6/16f,6/16f,0,4/16f,4/16f,2/16f);",
 "if(state.input[3])cap(state,pose,collector,6/16f,6/16f,14/16f,4/16f,4/16f,2/16f);",
 "if(state.input[4])cap(state,pose,collector,0,6/16f,6/16f,2/16f,4/16f,4/16f);",
 "if(state.input[5])cap(state,pose,collector,14/16f,6/16f,6/16f,2/16f,4/16f,4/16f);"]
for i,needle in enumerate(src):
 lines=s.splitlines(keepends=True)
 matching=[k for k,v in enumerate(lines) if needle in v]
 assert len(matching)==1,("B584_FACE_MISSING",i,matching)
 line=lines[matching[0]]
 assert "cap(state,pose,collector," in line and line.rstrip().endswith(");}") ,(i,line)
 lines[matching[0]]=line[:len(line)-len(line.lstrip())]+target[i]+"\n"
 s="".join(lines)
assert "dark(state" not in s and "BLACK_CONCRETE" not in s
assert s.count("cap(state,pose,collector,")==6
p.write_text(s,encoding="utf-8")

# Actual energy texture, no pale-iron or artificial giant black surround.
tex=A/"textures/block"
(tex/"xsx_energy_input_collar.png").write_bytes((tex/"energy_cable.png").read_bytes())

# Clone the exact original red geometry for all six faces, changing ONLY the
# two texture resource IDs. The renderer uses the same AABB as the 2nd element
# of this model; the first element is already drawn by the base Energy Cable.
models=A/"models/block"
for d in ("down","up","north","south","east","west"):
 source=json.loads((models/("item_cable_input_"+d+".json")).read_text(encoding="utf-8"))
 assert len(source["elements"])==2,("B584_ORIGINAL_MODEL_CHANGED",d)
 assert all(x=="obsidiannetwork:block/item_cable" for x in source["textures"].values())
 source["textures"]={"all":"obsidiannetwork:block/energy_cable",
                     "particle":"obsidiannetwork:block/energy_cable"}
 out=models/("energy_cable_input_"+d+".json")
 out.write_text(json.dumps(source,indent=2)+"\n",encoding="utf-8")
print("B584_EXACT_RED_COLLAR_GEOMETRY_BLUE_BLACK_ORIGINAL_ENERGY_TEXTURE_PASS")
