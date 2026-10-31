#!/usr/bin/env python3
"""B622: rebuild visual detail of all 24 MK GeckoLib suits, with hinged
outer-edge rear doors, one real faceplate, head-first recall and safe overlay.
Retain physical item ownership and the Build617 energy/armor core unchanged.
"""
import json, os, math
from pathlib import Path
from PIL import Image

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
N=24
FINISH="V175_CINEMATIC_POLISH_B622"

def save(path, data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def uv(x,y,w,h):
    assert x>=0 and y>=0 and w>0 and h>0 and x+w<=128.01 and y+h<=128.01,(x,y,w,h)
    return {"uv":[round(x,3),round(y,3)],"uv_size":[round(w,3),round(h,3)]}

def six(width,height,depth,top=83,base=100):
    # All six faces explicitly mapped to the manufactured metal/inner plate
    # region; no default solid-color cube faces.
    return {
     "north":uv(0,top,width,height),
     "south":uv(25,top,width,height),
     "west":uv(50,top,depth,height),
     "east":uv(67,top,depth,height),
     "up":uv(0,base,width,depth),
     "down":uv(25,base,width,depth)}

def mesh(name,pivot,origin,size,face_uv,parent):
    return {"name":name,"parent":parent,"pivot":pivot,
     "cubes":[{"origin":origin,"size":size,"uv":face_uv,"inflate":0}]}

def surface(origin,size,north=None,south=None,east=None,west=None,upper=None,lower=None):
    w,h,d=size
    faces=six(w,h,d)
    for side,over in (("north",north),("south",south),("east",east),
                      ("west",west),("up",upper),("down",lower)):
        if over is not None:faces[side]=over
    return {"origin":origin,"size":size,"uv":faces,"inflate":0}

# Custom additional pixels live strictly in UNUSED bottom part of the
# original 128x128 atlas, leaving each tier's base armor/visor art unchanged.
for tier in range(1,N+1):
    name=f"power_armor_visual_mk{tier}"
    path=A/"geckolib/models/entity"/f"{name}.geo.json"
    animpath=A/"geckolib/animations/entity"/f"{name}.animation.json"
    tex=A/"textures/entity"/f"{name}.png"
    assert path.is_file() and animpath.is_file() and tex.is_file(),("V175_ASSET_MISSING",tier)
    doc=json.loads(path.read_text(encoding="utf-8"))
    bones=doc["minecraft:geometry"][0]["bones"]
    index={b["name"]:b for b in bones}
    assert len(bones)==len(index)==20,("V175_EXPECT_POST_B621_RIG",tier)
    assert index["visor"]["parent"]=="faceplate" and index["faceplate"]["parent"]=="helmet"
    assert index["helmet"]["cubes"][0]["size"]==[9,8.5,.95]

    # Rear doors hinge at OUTER LATERAL margins, opening a central doorway.
    # Keeping their closed geometry in-place avoids the old detached boxes.
    index["rear_left"]["pivot"]=[-4.4,20,3.4]
    index["rear_right"]["pivot"]=[4.4,20,3.4]
    left=index["rear_left"]["cubes"][0]
    right=index["rear_right"]["cubes"][0]
    left["uv"]=six(*left["size"])
    right["uv"]=six(*right["size"])
    # Recover continuous old outer rear panel texture, not reused patchwork UV.
    left["uv"]["south"]=uv(22.4,6.8,4.35,10)
    right["uv"]["south"]=uv(26.75,6.8,4.35,10)

    # One single articulated faceplate: reuse the actual OLD helmet front art.
    # The rest of the helmet is made of open-sided wall/top/back shell pieces.
    face=index["faceplate"]
    face["pivot"]=[0,33.45,-4.45]
    fc=face["cubes"][0]
    fc["uv"]=six(*fc["size"],top=83,base=100)
    fc["uv"]["north"]=uv(9,34,8.9,7.55)
    # Inverted inner mask shows detailed mechanism rather than a solid fill.
    fc["uv"]["south"]=uv(25,83,8.9,7.55)
    for cub in index["helmet"]["cubes"]:
        co=cub["origin"];size=cub["size"]
        mapped=six(*size)
        # Exteriors retain tier's own helmet art; inward normals use new panel texture.
        if co[2]>=3.5:mapped["south"]=uv(27,34,9,8.5)
        if size[1]<=1.01:mapped["up"]=uv(9,25,9,9)
        if co[0]<-4 and size[0]<1.01:mapped["west"]=uv(0,34,7.1,8.5)
        if co[0]>3 and size[0]<1.01:mapped["east"]=uv(18,34,7.1,8.5)
        cub["uv"]=mapped

    # Preserve original torso outer faces; visible inner mechanisms get
    # detailed dedicated UVs, independent of tier color palette.
    torso=index["spine"]["cubes"]
    assert len(torso)==4,("V175_TORSO_SPLIT_LOST",tier)
    for cub in torso:
        cub["uv"]=six(*cub["size"])
    torso[0]["uv"]["north"]=uv(6.8,6.8,8.8,10)
    torso[1]["uv"]["west"]=uv(0,6.8,4.4,10)
    torso[2]["uv"]["east"]=uv(15.6,6.8,4.4,10)

    # Restore consistent original arm / leg textures along articulated
    # extremities instead of sampling their top corner on EVERY cube face.
    for bn in ("left_forearm","right_forearm","left_boot","right_boot"):
        cube=index[bn]["cubes"][0]
        old=cube["uv"];src_u,src_v=old
        w,h,d=cube["size"]
        cube["uv"]=six(w,h,d)
        cube["uv"]["north"]=uv(src_u+d,src_v+d,w,h)
        cube["uv"]["south"]=uv(src_u+2*d+w,src_v+d,w,h)

    # Light, physical gaskets, plate catches and hinge rails parented to the
    # existing articulated panels. No independent floating placeholder boxes.
    extras=[
      mesh("rear_left_hinge",[-4.4,20,3.4],[-4.60,16.5,2.48],[.45,7,.9],six(.45,7,.9),"rear_left"),
      mesh("rear_right_hinge",[4.4,20,3.4],[4.15,16.5,2.48],[.45,7,.9],six(.45,7,.9),"rear_right"),
      mesh("rear_left_gasket",[-4.4,20,3.4],[-.46,15.8,2.39],[.50,8.3,.22],six(.5,8.3,.22),"rear_left"),
      mesh("rear_right_gasket",[4.4,20,3.4],[.04,15.8,2.39],[.50,8.3,.22],six(.5,8.3,.22),"rear_right"),
      mesh("faceplate_left_rail",[0,33.45,-4.45],[-4.47,26,-4.75],[.57,7.3,.29],six(.57,7.3,.29),"faceplate"),
      mesh("faceplate_right_rail",[0,33.45,-4.45],[3.9,26,-4.75],[.57,7.3,.29],six(.57,7.3,.29),"faceplate"),
      mesh("faceplate_forehead_lock",[0,33.45,-4.45],[-1.75,32.2,-4.78],[3.5,.67,.3],six(3.5,.67,.3),"faceplate"),
      mesh("torso_inner_spine",[0,17,0],[-1,16,2.47],[2,8,.27],six(2,8,.27),"spine"),
    ]
    bones.extend(extras)
    assert len(bones)==28 and len({b["name"] for b in bones})==28

    animations=json.loads(animpath.read_text(encoding="utf-8"))
    assert len(animations["animations"])==7
    for aname, data in animations["animations"].items():
        root=data["bones"]["root"]["rotation"]
        if aname.endswith("recall_flight") or aname.endswith("recall_brake"):
            # 26.1 render direction: original -90 pitched FEET first.
            # +90 points the helmet into the flight direction.
            for frame in root.values():
                frame["vector"][0]=-frame["vector"][0]
        # Keep rear doors hinged without detached side translations.
        for bn, sign in (("rear_left",-1),("rear_right",1)):
            for frame in data["bones"][bn]["position"].values():
                frame["vector"][0]=round(frame["vector"][0]*.12,4)
            for frame in data["bones"][bn]["rotation"].values():
                frame["vector"][1]=round(frame["vector"][1]*1.15,4)
        # Compress mask lift and keep its pivot on upper helmet rim.
        for frame in data["bones"]["faceplate"]["position"].values():
            frame["vector"][2]=round(frame["vector"][2]*.50,4)
    save(path,doc)
    save(animpath,animations)

    with Image.open(tex) as opened:
        im=opened.convert("RGBA")
    assert im.size==(128,128)
    pixels=im.load()
    immutable=bytes(im.crop((0,0,128,80)).tobytes())
    # Brushed metal, engraved seams, bolt holes, staggered coolant
    # channels and tier-toned panel highlights. No additional sprite file.
    seed=pixels[8,8]
    if seed[3]==0:seed=pixels[26,27]
    base=(max(22,seed[0]),max(22,seed[1]),max(22,seed[2]))
    for y in range(82,127):
        for x in range(128):
            xx=x%24;yy=(y-82)%21
            scan=((x*17+y*11+tier*7)%9)-4
            brushed=7 if y%5==0 else -4 if y%9==0 else 0
            outline=xx in (0,1,22,23) or yy in (0,1,19,20)
            bolt=xx in (4,19) and yy in (4,16)
            vent=6<=xx<=17 and yy in (7,8,9) and xx%3!=0
            trace=xx in (11,12) and 12<=yy<=17
            if outline:c=(15,20,25)
            elif bolt:c=(182,182,164)
            elif vent:c=(9,17,23)
            elif trace:c=(31,203,226) if tier%2 else (215,175,48)
            else:c=tuple(max(15,min(248,int(t*.66+30)+scan+brushed)) for t in base)
            pixels[x,y]=(*c,255)
    assert im.crop((0,0,128,80)).tobytes()==immutable
    im.save(tex,optimize=True)

# Prevent superimposed vanilla equipment from showing a duplicate faceplate.
# The original ArmorStand remains the sole owner of all items and is restored
# on every normal transition completion AND after chunk load/restart.
world=J/"powerarmor/PowerArmorSuitWorld.java"
s=world.read_text(encoding="utf-8")
legacy='''  stand.setInvisible(false);
  return new Animation(stand,20,entering,visual);'''
replacement='''  // V175_CINEMATIC_SINGLE_MESH: hide ONLY while the actual Geo visual exists.
  // Stacks remain with this real owned ArmorStand, never on the visual.
  stand.addTag("xsxlabs_v175_temporarily_hidden_world_suit");
  stand.setInvisible(true);
  return new Animation(stand,20,entering,visual);'''
assert s.count(legacy)==1,("V175_STAND_OVERLAY_SOURCE_DRIFT",s.count(legacy))
s=s.replace(legacy,replacement,1)
# Different release-line patches reformat the cleanup method. Modify its
# actual body, not an obsolete one-line spelling from the initial generator.
start=s.find("private static void cleanup(Animation transition)")
end=s.find("private static Animation startAnimation",start)
assert 0<=start<end,("V175_ANIMATION_CLEANUP_METHOD_DRIFT",start,end)
cleanup=s[start:end]
assert "ArmorStand stand=transition.stand();" in cleanup,("V175_CLEANUP_NO_REAL_OWNER",cleanup[:650])
assert cleanup.count("stand.setInvisible(false)")>=1,("V175_CLEANUP_NO_VISIBILITY_RESTORE",cleanup[:900])
cleanup=cleanup.replace("stand.setInvisible(false)",
 "stand.removeTag(\"xsxlabs_v175_temporarily_hidden_world_suit\");stand.setInvisible(false)",1)
s=s[:start]+cleanup+s[end:]
end=s.rfind("\n}")
assert end>0 and "@EventBusSubscriber" in s
s=s[:end]+'''
 // V175_RESTART_SAFE_OVERLAY: never persist an invisible real world suit.
 // Only runs when a tagged entity joins, not in the per-tick hot path.
 @net.neoforged.bus.api.SubscribeEvent
 public static void v175RestoreWorldSuitOnLoad(
       net.neoforged.neoforge.event.entity.EntityJoinLevelEvent e){
  if(e.getLevel().isClientSide())return;
  if(e.getEntity() instanceof ArmorStand stand
     &&stand.getTags().contains("xsxlabs_v175_temporarily_hidden_world_suit")){
   stand.removeTag("xsxlabs_v175_temporarily_hidden_world_suit");
   stand.setInvisible(false);
  }
 }
'''+s[end:]
world.write_text(s,encoding="utf-8")

# V172 recall is itemless and its transient render is already the sole visible
# suit. Head-first pose is authored in GeckoLib; direction-matched rear exhaust
# particles must come from the boot/tail end instead of the mannequin torso.
rec=J/"powerarmor/PowerArmorRecall.java"
s=rec.read_text(encoding="utf-8")
old='''   player.level().sendParticles(ParticleTypes.END_ROD,
     visual.getX(),visual.getY()+.15D,visual.getZ(),2,.16D,.13D,.16D,.015D);
   player.level().sendParticles(ParticleTypes.FLAME,
     visual.getX(),visual.getY()-.10D,visual.getZ(),2,.12D,.10D,.12D,.015D);'''
new='''   // V175_HEAD_FIRST_JETS: 2 rear boot nozzles, exhaust opposite travel.
   Vec3 dir=move.normalize();
   Vec3 right=new Vec3(-dir.z,0D,dir.x);
   Vec3 tail=visual.position().subtract(dir.scale(.72D));
   for(int nozzle=-1;nozzle<=1;nozzle+=2){
    Vec3 spark=tail.add(right.scale(nozzle*.22D));
    player.level().sendParticles(ParticleTypes.END_ROD,
      spark.x,spark.y,spark.z,1,.04D,.04D,.04D,.015D);
    player.level().sendParticles(ParticleTypes.FLAME,
      spark.x,spark.y,spark.z,1,.04D,.04D,.04D,.015D);
   }'''
assert s.count(old)==1,("V175_JET_SOURCE_DRIFT",s.count(old))
s=s.replace(old,new,1)
rec.write_text(s,encoding="utf-8")

# Replace missing translation keys displayed above cosmetic entities (Jade).
for locale in ("en_us","de_de"):
    lang=A/"lang"/f"{locale}.json"
    data=json.loads(lang.read_text(encoding="utf-8"))
    for tier in range(1,N+1):
        key=f"entity.obsidiannetwork.power_armor_visual_mk{tier}"
        data[key]=f"Power Armor MK{tier}" if locale=="en_us" else f"Power-Rüstung MK{tier}"
    save(lang,data)
print("V175_B622_CINEMATIC: 24 textured six-face articulated suits, no duplicate world overlay, head-first flight, 2 real boot jets, safe recovery")
