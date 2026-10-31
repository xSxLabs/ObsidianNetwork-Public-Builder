#!/usr/bin/env python3
"""B632: align original animated outer-shell proportions to the wearer.

Only 3D cube origins/sizes change.  All Mk1..24 equipment-pixel UV mappings
from B630, all seven animation clips (including entire recall), bone pivots,
ownership/lifecycle and real armor/gameplay are invariant.
"""
import hashlib,json,os
from pathlib import Path

A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
MARK="V175_B632_CANONICAL_WORN_SHELL"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cube(index,bn,number=0):
    return index[bn]["cubes"][number]
def fit(index,bn,number,origin,size):
    obj=cube(index,bn,number)
    assert isinstance(obj["uv"],dict) and len(obj["uv"])==6,("B632_SOURCE_UV_DRIFT",bn,number)
    assert len(obj["origin"])==3 and len(obj["size"])==3
    assert all(v>0 for v in size)
    obj["origin"]=origin
    obj["size"]=size
def persist(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
protect=[J/"powerarmor/PowerArmorRecall.java",
         J/"powerarmor/PowerArmorSuitWorld.java",
         J/"powerarmor/PowerArmorVisualEntity.java",
         J/"conduit/EnergyConduitTicker.java"]
prior={str(p):sha(p) for p in protect}
for mk in range(1,25):
    stem=f"power_armor_visual_mk{mk}"
    modelpath=A/"geckolib/models/entity"/(stem+".geo.json")
    animationpath=A/"geckolib/animations/entity"/(stem+".animation.json")
    texturepath=A/"textures/entity"/(stem+".png")
    assert all(p.is_file() for p in (modelpath,animationpath,texturepath))
    original_animation=sha(animationpath)
    original_texture=sha(texturepath)
    model=json.loads(modelpath.read_text(encoding="utf-8"))
    bones=model["minecraft:geometry"][0]["bones"]
    idx={b["name"]:b for b in bones}
    assert len(bones)==len(idx)==28,(mk,"B631 28-bone rig")
    before_pivots={name:tuple(b["pivot"]) for name,b in idx.items()}
    before_hierarchy={name:b.get("parent") for name,b in idx.items()}
    before_uv={(name,i):json.dumps(c["uv"],sort_keys=True) for name,b in idx.items()
               for i,c in enumerate(b.get("cubes",[]))}
    assert len(idx["spine"]["cubes"])==1 and len(idx["torso_inner_spine"]["cubes"])==4
    assert idx["rear_left"]["pivot"]==[-4.4,20,3.4] and idx["rear_right"]["pivot"]==[4.4,20,3.4]
    assert idx["faceplate"]["parent"]=="helmet"
    # The B629 front double chest plates were each wider than half the full
    # torso and protruded 1.6 px FORWARD of the worn armor's silhouette.
    # Align the front pair to the two halves of the exact torso skin instead.
    # Y 13..25 provides the 12px height of the actual worn torso UV.
    fit(idx,"spine",0,[-4.4,13,-3.4],[8.8,12,.8])
    fit(idx,"chest_left",0,[-4.4,13,-3.55],[4.35,12,.20])
    fit(idx,"chest_right",0,[.05,13,-3.55],[4.35,12,.20])
    # For genuine rear doors, the original animated panels remain hinged on
    # the outer lateral edges; only cover the full 12px worn back vertically.
    fit(idx,"rear_left",0,[-4.4,13,2.5],[4.35,12,.9])
    fit(idx,"rear_right",0,[.05,13,2.5],[4.35,12,.9])
    # Inner sidewalls meet the chest and rear flush without sticking through.
    # In B631 they are on the interior carrier: they disappear ONLY while
    # normal rear hatch opens, remain perfectly present during recall flight.
    fit(idx,"torso_inner_spine",1,[-4.4,13,-2.6],[.95,12,5.1])
    fit(idx,"torso_inner_spine",2,[3.45,13,-2.6],[.95,12,5.1])
    fit(idx,"torso_inner_spine",3,[-3.45,13,2.5],[6.9,1,.9])
    # Head uses one single full-face plate, fitted flush between upper rim
    # and chin; UV remains the ORIGINAL 8x8 worn mask artwork.
    fit(idx,"faceplate",0,[-4.5,25,-4.5],[9,8.5,.95])
    # Worn humanoid armor arms are ~5px thick, NOT the original 6.8px
    # deep detached color cuboids. Each 12px limb has a mechanical elbow.
    fit(idx,"left_arm",0,[-9.45,19,-2.5],[5,6,5])
    fit(idx,"right_arm",0,[4.45,19,-2.5],[5,6,5])
    fit(idx,"left_forearm",0,[-9.45,13,-2.5],[5,6,5])
    fit(idx,"right_forearm",0,[4.45,13,-2.5],[5,6,5])
    fit(idx,"left_shoulder",0,[-9.45,22,-2.6],[5,3,5.2])
    fit(idx,"right_shoulder",0,[4.45,22,-2.6],[5,3,5.2])
    # Humanoid worn leggings and boots similarly have ~5px front-back depth.
    # Thigh/boot parts now meet exactly at y=4 instead of overlapping.
    fit(idx,"left_leg",0,[-5.1,4,-2.5],[4.9,9,5])
    fit(idx,"right_leg",0,[.2,4,-2.5],[4.9,9,5])
    fit(idx,"left_boot",0,[-5.1,0,-2.5],[4.9,4,5])
    fit(idx,"right_boot",0,[.2,0,-2.5],[4.9,4,5])
    # Preserve chest arc location; the original worn reactor art remains
    # on the same pixels and follows the spine.
    assert idx["reactor"]["parent"]=="spine"
    assert idx["faceplate"]["cubes"][0]["uv"]["north"]=={"uv":[8,8],"uv_size":[8,8]}
    assert idx["rear_left"]["cubes"][0]["uv"]["south"]=={"uv":[32,20],"uv_size":[4,12]}
    assert idx["rear_right"]["cubes"][0]["uv"]["south"]=={"uv":[36,20],"uv_size":[4,12]}
    assert before_pivots=={name:tuple(b["pivot"]) for name,b in idx.items()},(mk,"pivot moved")
    assert before_hierarchy=={name:b.get("parent") for name,b in idx.items()},(mk,"bone hierarchy altered")
    assert before_uv=={(name,i):json.dumps(c["uv"],sort_keys=True) for name,b in idx.items()
                       for i,c in enumerate(b.get("cubes",[]))},(mk,"original worn UV changed")
    persist(modelpath,model)
    assert sha(animationpath)==original_animation,(mk,"RECALL_OR_NORMAL_ANIMATION_CHANGED")
    assert sha(texturepath)==original_texture,(mk,"WORN_TEXTURE_PIXEL_CHANGED")
assert prior=={str(p):sha(p) for p in protect},("B632_GAMEPLAY_SOURCE_CHANGED")
print(MARK+": 24 original worn-skin torso/head/arm/leg outer proportions, no floating front blocks, same 28 bones and full recall keyframes")
