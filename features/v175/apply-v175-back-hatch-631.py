#!/usr/bin/env python3
"""B631: movie-inspired, back-only standing-suit opening. Recall untouched.

Reduce front-shell interference and temporarily fold away the stationary inner
carriage during NORMAL enter/exit ONLY. Keep exterior worn-UV parts moving
on their authentic outer hinges, do not alter flying/recall motion at all.
"""
import hashlib, json, os
from pathlib import Path

A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
MARK="V175_B631_BACK_EXIT_ONLY"
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
protected=[J/"powerarmor/PowerArmorRecall.java",
           J/"powerarmor/PowerArmorSuitWorld.java",
           J/"powerarmor/PowerArmorVisualEntity.java",
           J/"conduit/EnergyConduitTicker.java"]
prior=[digest(p) for p in protected]

for tier in range(1,25):
    name=f"power_armor_visual_mk{tier}"
    modelpath=A/"geckolib/models/entity"/(name+".geo.json")
    animpath=A/"geckolib/animations/entity"/(name+".animation.json")
    texture=A/"textures/entity"/(name+".png")
    before_tex=digest(texture)
    doc=json.loads(modelpath.read_text(encoding="utf-8"))
    clips=json.loads(animpath.read_text(encoding="utf-8"))
    bones=doc["minecraft:geometry"][0]["bones"]
    idx={b["name"]:b for b in bones}
    assert len(idx)==len(bones)==28,(tier,"B629 rig changed")
    assert idx["faceplate"]["parent"]=="helmet" and idx["visor"]["parent"]=="faceplate"
    assert idx["rear_left"]["pivot"]==[-4.4,20,3.4]
    assert idx["rear_right"]["pivot"]==[4.4,20,3.4]
    assert len(idx["spine"]["cubes"])==4,(tier,"B630 original internal wall drift")
    assert idx["torso_inner_spine"]["parent"]=="spine"
    assert len(idx["torso_inner_spine"]["cubes"])==1

    # The external frontal plate stays in the static chest shell.
    # The 2 hollow sidewalls and 1 fixed interior shelf are moved beneath
    # the dedicated interior bone. They occupy EXACTLY the same model space
    # with their original exact worn-atlas pixel UVs when closed or flying.
    internal=idx["spine"]["cubes"][1:]
    idx["spine"]["cubes"]=idx["spine"]["cubes"][:1]
    idx["torso_inner_spine"]["cubes"].extend(internal)
    assert len(idx["spine"]["cubes"])==1
    assert len(idx["torso_inner_spine"]["cubes"])==4

    before={n:json.dumps(clips["animations"]["animation.power_armor."+n],sort_keys=True)
            for n in ("open","close","recall_flight","recall_brake","recall_dock")}
    # Use original normal actions, NOT the MK42-inspired arrival choreography.
    for action in ("equip","unequip"):
        clip=clips["animations"]["animation.power_armor."+action]
        assert clip["animation_length"]==1.0,(tier,action,"normal animation duration changed")
        tracks=clip["bones"]
        assert all(n in tracks for n in
                   ("rear_left","rear_right","chest_left","chest_right",
                    "faceplate","left_arm","right_arm","left_leg","right_leg"))
        # Genuine back hatch: original front chest plates stay locked in place.
        # No sliding front halves, disconnected leg boxes or flying forearms.
        for bn in ("chest_left","chest_right",
                   "left_leg","right_leg","left_boot","right_boot",
                   "left_forearm","right_forearm"):
            if bn not in tracks:continue
            for channel in ("rotation","position"):
                for frame in tracks[bn].get(channel,{}).values():
                    frame["vector"]=[0,0,0]
        # Shoulders can release slightly, but stay mechanically attached.
        for bn in ("left_arm","right_arm"):
            for frame in tracks[bn].get("rotation",{}).values():
                frame["vector"]=[round(x*.30,4) for x in frame["vector"]]
        # Existing well-textured, outer-margin rear doors and single faceplate
        # retain their exact hinge angles and masks/timings from B629.
        # Hide stationary INSIDE geometry only while both rear plates open.
        # Zero-scale here never changes external bone scale or texture; every
        # 20-tick normal animation restores it to (1,1,1) by the end.
        frames={
          "0.0":[1,1,1],
          "0.08":[1,1,1],
          "0.12":[0,0,0],
          "0.76":[0,0,0],
          "0.88":[1,1,1],
          "1.0":[1,1,1]
        }
        tracks["torso_inner_spine"]={
            "scale":{t:{"vector":vec,"easing":"easeInOutSine"} for t,vec in frames.items()}
        }
        assert all(frame["vector"]==[0,0,0] for frame in tracks["chest_left"]["rotation"].values())
        assert "rotation" in tracks["rear_left"] and "rotation" in tracks["rear_right"]
        assert "rotation" in tracks["faceplate"]
    for n,old in before.items():
        assert json.dumps(clips["animations"]["animation.power_armor."+n],sort_keys=True)==old,(tier,n,"RECALL_OR_BASE_CLIP_MODIFIED")
    save(modelpath,doc);save(animpath,clips)
    assert digest(texture)==before_tex,(tier,"original worn-equipment pixels modified")

assert [digest(p) for p in protected]==prior,"B631 must not change runtime, inventory or recall code"
print(MARK+": 24 standing suits open ONLY at the back, fixed worn-textured front, hidden static inner carriage while split, unique mask; unchanged complete recall")
