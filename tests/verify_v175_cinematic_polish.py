#!/usr/bin/env python3
"""B622 source-asset fail-closed cinematic coverage before full NeoForge compile."""
import json, os, math
from pathlib import Path
from PIL import Image
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
added={"rear_left_hinge","rear_right_hinge","rear_left_gasket",
       "rear_right_gasket","faceplate_left_rail","faceplate_right_rail",
       "faceplate_forehead_lock","torso_inner_spine"}
names=("open","close","equip","unequip","recall_flight","recall_brake","recall_dock")
for tier in range(1,25):
    stem=f"power_armor_visual_mk{tier}"
    model=json.loads((A/"geckolib/models/entity"/(stem+".geo.json")).read_text())
    anim=json.loads((A/"geckolib/animations/entity"/(stem+".animation.json")).read_text())
    bs=model["minecraft:geometry"][0]["bones"]
    bones={b["name"]:b for b in bs}
    assert len(bs)==len(bones)==28 and added.issubset(bones),(tier,"missing plates")
    assert bones["rear_left"]["pivot"]==[-4.4,20,3.4]
    assert bones["rear_right"]["pivot"]==[4.4,20,3.4]
    assert bones["faceplate"]["parent"]=="helmet"
    assert bones["visor"]["parent"]=="faceplate"
    # The helmet must have no second full-face panel outside animated faceplate.
    for cube in bones["helmet"]["cubes"]:
        width,height,depth=cube["size"]
        assert width<8 or height<7.6 or depth<.99,(tier,"duplicate fixed faceplate")
    all_cubes=[(bn,cube) for bn,b in bones.items() for cube in b.get("cubes",[])]
    for bn,cube in all_cubes:
        uv=cube["uv"]
        if bn in {"root"}:continue
        assert isinstance(uv,dict) or bn in ("chest_left","chest_right","left_arm",
           "right_arm","left_leg","right_leg","visor","reactor","left_shoulder",
           "right_shoulder"),(tier,bn,"flat legacy cube UV on rebuilt bone")
        if isinstance(uv,dict):
            assert set(uv)=={"north","south","east","west","up","down"},(tier,bn,set(uv))
            for face,rect in uv.items():
                u,v=rect["uv"];w,h=rect["uv_size"]
                assert 0<=u<128 and 0<=v<128 and w>0 and h>0
                assert u+w<=128.01 and v+h<=128.01,(tier,bn,face,rect)
    # Outer mask: OLD tier texture location. Inner mask: new engineered art.
    face=bones["faceplate"]["cubes"][0]["uv"]
    assert face["north"]["uv"]==[9,34]
    assert face["south"]["uv"]==[25,83]
    assert len(anim["animations"])==7
    clips=anim["animations"]
    assert set(clips)=={"animation.power_armor."+n for n in names}
    f=clips["animation.power_armor.recall_flight"]["bones"]["root"]["rotation"]
    assert all(abs(frame["vector"][0]-90)<.0001 for frame in f.values()),tier
    b=clips["animation.power_armor.recall_brake"]["bones"]["root"]["rotation"]
    assert b["0"]["vector"][0]==90 and b["1.0"]["vector"][0]==0,tier
    for n in ("equip","unequip"):
        clip=clips["animation.power_armor."+n]["bones"]
        assert abs(clip["rear_left"]["rotation"]["0.55"]["vector"][1])>=75,tier
        assert abs(clip["rear_left"]["position"]["0.55"]["vector"][0])<.5,tier
        assert clip["faceplate"]["rotation"]["1.0"]["vector"]==[0,0,0],tier
    for b in added:
        assert bones[b]["parent"] in bones,(tier,b)
    texture=A/"textures/entity"/(stem+".png")
    with Image.open(texture) as im:
        assert im.size==(128,128) and im.mode=="RGBA",tier
        # Multiple brush/vent/emissive colors in the NEW inner texel areas.
        colors={im.getpixel((x,y)) for x in range(2,124,2) for y in range(84,126,2)}
        assert len(colors)>20,(tier,"untextured interiors",len(colors))
for locale in ("en_us","de_de"):
    lang=json.loads((A/"lang"/(locale+".json")).read_text())
    for tier in range(1,25):
        assert lang.get(f"entity.obsidiannetwork.power_armor_visual_mk{tier}"),(locale,tier)
world=(J/"powerarmor/PowerArmorSuitWorld.java").read_text()
rec=(J/"powerarmor/PowerArmorRecall.java").read_text()
vis=(J/"powerarmor/PowerArmorVisualEntity.java").read_text()
assert 'stand.addTag("xsxlabs_v175_temporarily_hidden_world_suit")' in world
assert "stand.setInvisible(true)" in world
assert "stand.setInvisible(false)" in world
assert "v175RestoreWorldSuitOnLoad" in world
assert 'stand.entityTags().contains("xsxlabs_v175_temporarily_hidden_world_suit")' in world
assert "stand.getTags()" not in world
assert "stand.removeTag" in world
assert "PowerArmorSuitWorld.recallEquip(stand,player)" in rec
assert "V175_RECOVERY_SAFE_DOCK" in rec
assert "V175_HEAD_FIRST_JETS" in rec
assert "tail=visual.position().subtract(dir.scale(.72D))" in rec
assert "visual.noPhysics=true" in rec
assert "PowerArmorRecall.isVisualActive(getUUID())" in vis
assert "V175_RECALL_VISUAL_LIFETIME" in vis
assert '"animation.power_armor.equip":"animation.power_armor.unequip"' in vis
print("V175_B622_CINEMATIC_GATE_PASS: 24/24*28 bone six-face interiors, single mask, head-first 90deg flight, no duplicate stand, recovery, localized entities")
