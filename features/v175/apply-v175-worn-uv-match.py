#!/usr/bin/env python3
"""B630: match animated suit outer surfaces to the EXACT worn Equipment textures.

Pixels come from the game's own humanoid and humanoid_leggings equipment PNGs
for each MK tier. GeckoLib asset/animation bone hierarchy, poses, timings and
server inventory/recall mechanics are never changed. Separate material exists
only on inner cutaway faces. This is NOT a palette approximation.
"""
import hashlib,json,os
from pathlib import Path
from PIL import Image
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
MARK="V175_B630_EXACT_WORN_OUTER_UV"
def stable(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def rect(u,v,w,h):
    assert u>=0 and v>=0 and w>0 and h>0 and u+w<=128.001 and v+h<=128.001,(u,v,w,h)
    return {"uv":[u,v],"uv_size":[w,h]}
def inner(w,h,d):
    # Only the hidden / newly exposed interior mechanical contact surfaces
    # use the existing tier-tinted industrial inner metal atlas.
    return {
     "north":rect(25,83,w,h),"south":rect(42,83,w,h),
     "west":rect(58,83,d,h),"east":rect(75,83,d,h),
     "up":rect(25,103,w,d),"down":rect(42,103,w,d)
    }
def cover(cube,**sides):
    u=inner(*cube["size"])
    for side,uv in sides.items():
        assert side in u and isinstance(uv,dict)
        u[side]=uv
    cube["uv"]=u
def preflight(a):
    assert a.size==(64,32),("B630_SOURCE_ARMOR_SIZE",a.size)
    assert a.getbbox() is not None,"B630_WORN_ATLAS_EMPTY"

# Worn 64x32 Minecraft armor UV coordinates. Head base (0,0), torso (16,16),
# arms (40,16), and leg (0,16) are the SAME used by HumanoidArmorModel.
# The first 64x32 of the 128 atlas are exact armor PNG bytes decoded as pixels,
# the next 64x32 are the actual leggings PNG. No generated surface art replaces
# the front or back design. Native 64x32 sprite UVs are used on 3D components.
HEAD={
 "front":rect(8,8,8,8),"back":rect(24,8,8,8),
 "left":rect(0,8,8,8),"right":rect(16,8,8,8),
 "top":rect(8,0,8,8),"bottom":rect(16,0,8,8)}
BODY={
 "front":rect(20,20,8,12),"back":rect(32,20,8,12),
 "left":rect(16,20,4,12),"right":rect(28,20,4,12),
 "top":rect(20,16,8,4),"bottom":rect(28,16,8,4)}
ARM={
 "front":rect(44,20,4,12),"back":rect(52,20,4,12),
 "left":rect(40,20,4,12),"right":rect(48,20,4,12),
 "top":rect(44,16,4,4),"bottom":rect(48,16,4,4)}
LEG_LEGGINGS={
 "front":rect(4,52,4,12),"back":rect(12,52,4,12),
 "left":rect(0,52,4,12),"right":rect(8,52,4,12),
 "top":rect(4,48,4,4),"bottom":rect(8,48,4,4)}
LEG_BOOTS={
 "front":rect(4,20,4,12),"back":rect(12,20,4,12),
 "left":rect(0,20,4,12),"right":rect(8,20,4,12),
 "top":rect(4,16,4,4),"bottom":rect(8,16,4,4)}
def strip(t,side,part):
    # Split the canonical body-part UV into actual component segments while
    # retaining its pixel identity and original north/south orientations.
    uv=t[side]
    u,v=uv["uv"];w,h=uv["uv_size"]
    if part=="top_arm":return rect(u,v,w,5 if h>=12 else h)
    if part=="forearm":return rect(u,v+5,w,7) if h>=12 else uv
    if part=="thigh":return rect(u,v,w,9) if h>=12 else uv
    if part=="boot":return rect(u,v+9,w,3) if h>=12 else uv
    if part=="shoulder":return rect(u,v,w,4) if h>=12 else uv
    return uv
def cube(b,idx=0):
    assert b.get("cubes") and len(b["cubes"])>idx,("B630_BONE_CUBE_GONE",b["name"],idx)
    return b["cubes"][idx]
def check_skin(mk,skin):
    # Register-defined asset names must correspond to actual equipped items.
    asset="power_armor" if mk==1 else "power_armor_mk"+str(mk)
    equip=A/"equipment"/(asset+".json")
    assert equip.is_file(),("B630_EQUIPMENT_ASSET_MISSING",mk)
    spec=json.loads(equip.read_text(encoding="utf-8"))
    assert spec["layers"]["humanoid"][0]["texture"]=="obsidiannetwork:"+asset,(mk,"main equipment ref")
    assert spec["layers"]["humanoid_leggings"][0]["texture"]=="obsidiannetwork:"+asset,(mk,"leggings equipment ref")
    for lay in ("humanoid","humanoid_leggings"):
        p=A/"textures/entity/equipment"/lay/(asset+".png")
        assert p.exists(),(mk,lay)
        with Image.open(p) as loaded:
            png=loaded.convert("RGBA")
        preflight(png)
        yield lay,png,p

# Everything outside these modeled surfaces remains identical B629.
protected=[J/"powerarmor/PowerArmorRecall.java",
           J/"powerarmor/PowerArmorSuitWorld.java",
           J/"powerarmor/PowerArmorVisualEntity.java",
           J/"conduit/EnergyConduitTicker.java"]
prior=[stable(p) for p in protected]
animations=[]
for mk in range(1,25):
    stem=f"power_armor_visual_mk{mk}"
    pngpath=A/"textures/entity"/(stem+".png")
    modelpath=A/"geckolib/models/entity"/(stem+".geo.json")
    animpath=A/"geckolib/animations/entity"/(stem+".animation.json")
    assert pngpath.is_file() and modelpath.is_file() and animpath.is_file(),("B630_RIG_FILES",mk)
    animations.append((animpath,stable(animpath)))
    layers={lay:(im,path) for lay,im,path in check_skin(mk,stem)}
    worn=layers["humanoid"][0]
    legs=layers["humanoid_leggings"][0]
    with Image.open(pngpath) as image:
        atlas=image.convert("RGBA")
    assert atlas.size==(128,128),(mk,atlas.size)
    # Source pixel-for-pixel accuracy.  No layer stretch, filter or palette
    # replacement. Rest of the atlas retains the suit's B625 inner detail.
    atlas.paste(worn,(0,0))
    atlas.paste(legs,(0,32))
    assert atlas.crop((0,0,64,32)).tobytes()==worn.tobytes()
    assert atlas.crop((0,32,64,64)).tobytes()==legs.tobytes()
    # Recolor ONLY the actual hidden inner hardware (rows 82..127) with the
    # material colors of the true worn sprite, not a guessed base green/red.
    visible=[pixel[:3] for pixel in worn.getdata() if pixel[3]>128
        and max(pixel[:3])-min(pixel[:3])>5 and max(pixel[:3])>30]
    assert len(visible)>12,(mk,"no valid equipment plate colors")
    visible.sort(key=lambda rgb: sum(rgb))
    plate=visible[len(visible)//2]
    px=atlas.load()
    for y in range(82,128):
        for x in range(128):
            # Preserve B625 engraved seams, vents, rivets and glowing channels
            # while tinting only old painted plate-fill surfaces.
            orig=px[x,y]
            r,g,b,a=orig
            if a==0:continue
            if max(r,g,b)<36 or min(r,g,b)>155:continue
            if b>r*1.3 and b>g*1.08:continue
            grain=((x*5+y*13+mk*3)%7)-3
            px[x,y]=tuple(max(10,min(245,round(c*.76+25+grain))) for c in plate)+(a,)
    atlas.save(pngpath,optimize=True)

    md=json.loads(modelpath.read_text(encoding="utf-8"))
    bones=md["minecraft:geometry"][0]["bones"]
    index={b["name"]:b for b in bones}
    assert len(bones)==len(index)==28,(mk,"expected unchanged 28-bone B629 rig")
    assert index["faceplate"]["parent"]=="helmet" and index["visor"]["parent"]=="faceplate"
    assert len(index["helmet"]["cubes"])==5
    # One true moving face, with exactly the vanilla worn head UV.
    cover(cube(index["faceplate"]),north=HEAD["front"],
          up=HEAD["top"],down=HEAD["bottom"])
    # A SECOND flat visor from the old visual atlas covered the real eyes.
    # Actual worn eye details now belong to the single moving faceplate.
    index["visor"].pop("cubes",None)
    head=index["helmet"]["cubes"]
    cover(head[0],south=HEAD["back"],up=HEAD["top"])
    cover(head[1],west=HEAD["left"],up=HEAD["top"])
    cover(head[2],east=HEAD["right"],up=HEAD["top"])
    cover(head[3],up=HEAD["top"],west=HEAD["left"],east=HEAD["right"])
    cover(head[4],down=HEAD["bottom"],west=HEAD["left"],east=HEAD["right"])

    torso=index["spine"]["cubes"]
    assert len(torso)==4,(mk,"torso split")
    cover(torso[0],north=BODY["front"],up=BODY["top"],down=BODY["bottom"])
    cover(torso[1],west=BODY["left"],up=BODY["top"])
    cover(torso[2],east=BODY["right"],up=BODY["top"])
    cover(torso[3],south=BODY["back"],down=BODY["bottom"])
    # Exact split of the original, continuous eight-pixel torso back panel.
    for side,bone in (("left","rear_left"),("right","rear_right")):
        u=32 if side=="left" else 36
        cover(cube(index[bone]),south=rect(u,20,4,12),
              up=rect(20 if side=="left" else 24,16,4,4),
              west=BODY["left"] if side=="left" else inner(1,10,1)["west"],
              east=BODY["right"] if side=="right" else inner(1,10,1)["east"])
    # Exterior chest catches use the exact front half of worn torso artwork.
    for side,bone in (("left","chest_left"),("right","chest_right")):
        u=20 if side=="left" else 24
        cover(cube(index[bone]),north=rect(u,20,4,12),
              up=rect(u,16,4,4),
              west=BODY["left"] if side=="left" else inner(1,10,1)["west"],
              east=BODY["right"] if side=="right" else inner(1,10,1)["east"])
    # Separate real upper-arm and forearm plates; segments preserve contiguous
    # source pixel rows so a bending elbow does not draw the same patch twice.
    for arm,forearm,shoulder in (
        ("left_arm","left_forearm","left_shoulder"),
        ("right_arm","right_forearm","right_shoulder")
    ):
        for bone,segment in ((arm,"top_arm"),(forearm,"forearm"),(shoulder,"shoulder")):
            faces={direction:strip(ARM,original,segment)
                    for direction,original in (("north","front"),("south","back"),
                                                ("west","left"),("east","right"),
                                                ("up","top"),("down","bottom"))}
            cover(cube(index[bone]),**faces)
    for leg,boot in (("left_leg","left_boot"),("right_leg","right_boot")):
        for bone,skin,segment in ((leg,LEG_LEGGINGS,"thigh"),(boot,LEG_BOOTS,"boot")):
            faces={direction:strip(skin,original,segment)
                  for direction,original in (("north","front"),("south","back"),
                                             ("west","left"),("east","right"),
                                             ("up","top"),("down","bottom"))}
            cover(cube(index[bone]),**faces)

    # Reactor's raised face reproduces the center of the ACTUAL worn chest
    # texture, not a separately drawn turquoise square.
    cover(cube(index["reactor"]),north=rect(22,23,4,4),
          south=rect(22,23,4,4))

    # Moving hinges/catches are colored with the EXACT same worn outer-panel
    # source, while their hidden contact surfaces keep the toned mechanism.
    mechanism={
        "rear_left_hinge":("south",rect(32,20,2,12)),
        "rear_right_hinge":("south",rect(38,20,2,12)),
        "rear_left_gasket":("south",rect(34,20,2,12)),
        "rear_right_gasket":("south",rect(36,20,2,12)),
        "faceplate_left_rail":("north",rect(8,8,1,8)),
        "faceplate_right_rail":("north",rect(15,8,1,8)),
        "faceplate_forehead_lock":("north",rect(10,8,4,2)),
        "torso_inner_spine":("north",rect(23,22,2,9))}
    assert set(mechanism).issubset(index)
    for bn,(side,src_uv) in mechanism.items():
        cover(cube(index[bn]),**{side:src_uv})
    modelpath.write_text(json.dumps(md,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

assert [stable(p) for p in protected]==prior,("B630_NOT_TEXTURE_ONLY_CODE_CHANGED")
assert all(stable(path)==sha for path,sha in animations),("B630_ANIMATION_CURVES_MODIFIED")
print(MARK+": 24/24 real worn humanoid+leggings PNGs; 28-bone exterior UVs, no second eye overlay; ZERO animation/recall/gameplay changes")
