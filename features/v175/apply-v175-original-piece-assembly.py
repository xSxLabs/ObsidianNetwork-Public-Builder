#!/usr/bin/env python3
"""B626: original piece-by-piece assembly choreography for all 24 xSxLabs suits.

Independent design: use staggered moving components and a late faceplate lock.
Do NOT copy or import third-party code, models, animations, textures or sounds.
Requires the successful B625 28-bone GeckoLib rigs. Never mutate item ownership,
energy transfer, persisted equipment or world topology.
"""
import json, math, os, re
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
TAG="V175_B626_ORIGINAL_PIECE_ASSEMBLY"
STEPS=[round(i/24,6) for i in range(25)]
# 1) Trunk/hinge plates, 2) legs/boots, 3) arms/cuffs, 4) helmet, 5) mask.
# A unique path and lock window per moving part: all paths return to their
# authentic tier-specific manufactured texture at the ORIGINAL closed position.
# x/y/z are GeckoLib model pixels relative to the unchanged bone pivots.
PIECES={
 "spine":        ([0, 7, 16],[19, 0, 0],.02,.32),
 "reactor":      ([0, 7,-20],[-18,0,0],.11,.36),
 "chest_left":   ([-16, 6,-13],[-12,-64,-18],.10,.43),
 "chest_right":  ([ 16, 6,-13],[-12, 64, 18],.14,.47),
 "rear_left":    ([-14, 8, 17],[8,-94,0],.09,.44),
 "rear_right":   ([ 14, 8, 17],[8, 94,0],.12,.46),
 "left_leg":     ([-12,-10,14],[12,0,-23],.22,.58),
 "right_leg":    ([ 12,-10,14],[12,0,23],.25,.61),
 "left_boot":    ([-17,-12,-8],[-27,0,-17],.33,.69),
 "right_boot":   ([ 17,-12,-8],[-27,0,17],.35,.71),
 "left_arm":     ([-20, 5,12],[3,0,-57],.32,.71),
 "right_arm":    ([ 20, 5,12],[3,0,57],.35,.74),
 "left_forearm": ([-23,-3,-12],[-27,0,-23],.40,.79),
 "right_forearm":([ 23,-3,-12],[-27,0,23],.42,.80),
 "left_shoulder":([-18,12,5],[0,-18,-23],.46,.82),
 "right_shoulder":([18,12,5],[0,18,23],.48,.83),
 "helmet":       ([0,20,18],[-45,0,0],.59,.91),
}
assert len(PIECES)==17
FACES="animation.power_armor."
DURATION_NORMAL=2.6  # matching 52 authoritative 20Hz ticks
DURATION_BRAKE=.60
DURATION_DOCK=2.0
def smooth(a,b,t):
    if t<=a:return 0.
    if t>=b:return 1.
    s=(t-a)/(b-a)
    return s*s*s*(s*(s*6-15)+10)

def stepvalue(t,a,b):
    # A separate gentle punch at the final latch gives 3D motion rather than
    # a linear box slide. No jitter at either endpoint.
    s=smooth(a,b,t)
    extra=.045*math.sin(s*math.pi)**4
    return 1.-s+extra

def keyframes(fn):
    out={}
    for t in STEPS:
        value=fn(t)
        assert len(value)==3 and all(math.isfinite(x) for x in value)
        out[str(round(t,6))]={"vector":[round(v,4) for v in value],
                              "easing":"easeInOutSine"}
    return out

def pose(name,t,action):
    pos,rot,start,end=PIECES[name]
    if action=="equip":
        strength=stepvalue(t,start,end)
    elif action=="unequip":
        strength=stepvalue(1-t,start,end)
    elif action=="recall_brake":
        strength=.62*smooth(.12,1,t)
    elif action=="recall_dock":
        strength=.62*stepvalue(t,max(0,start-.15),min(.98,end+.08))
    else:raise AssertionError(action)
    return [round(v*strength,4) for v in pos],[round(v*strength,4) for v in rot]

def mask(t,action):
    # Only ONE actual faceplate exists. It is a child of the flying helmet.
    # When the head unit is traveling, the mask folds up; after head dock,
    # it locks shut. The visor and trim are children of that very same bone.
    if action=="equip":
        lift=1.-smooth(.80,.99,t)
    elif action=="unequip":
        lift=smooth(.02,.20,t)
    elif action=="recall_brake":
        lift=smooth(.25,1,t)
    elif action=="recall_dock":
        lift=1.-smooth(.75,.99,t)
    else:raise AssertionError(action)
    return [-117*lift,0,0],[0,1.0*lift,-.35*lift]

def make_clip(action):
    clip={"animation_length":{"equip":DURATION_NORMAL,"unequip":DURATION_NORMAL,
          "recall_brake":DURATION_BRAKE,"recall_dock":DURATION_DOCK}[action],
          "loop":"hold_on_last_frame","bones":{}}
    bones=clip["bones"]
    for name in PIECES:
        bones[name]={
            "position":keyframes(lambda t,n=name:pose(n,t,action)[0]),
            "rotation":keyframes(lambda t,n=name:pose(n,t,action)[1])
        }
    bones["faceplate"]={
      "rotation":keyframes(lambda t:mask(t,action)[0]),
      "position":keyframes(lambda t:mask(t,action)[1])
    }
    bones["root"]={"rotation":keyframes(
      lambda t:[90*(1-smooth(.06,.97,t)),0,0] if action=="recall_brake"
      else [0,0,0])}
    return clip

for mk in range(1,25):
    stem="power_armor_visual_mk"+str(mk)
    modelpath=A/"geckolib/models/entity"/(stem+".geo.json")
    animpath=A/"geckolib/animations/entity"/(stem+".animation.json")
    model=json.loads(modelpath.read_text(encoding="utf-8"))
    src=json.loads(animpath.read_text(encoding="utf-8"))
    bs=model["minecraft:geometry"][0]["bones"]
    index={b["name"]:b for b in bs}
    assert len(bs)==len(index)==28 and set(PIECES).issubset(index),("B626_TIER_ORIGINAL_RIG_DRIFT",mk)
    assert index["visor"]["parent"]=="faceplate" and index["faceplate"]["parent"]=="helmet"
    # All independent pieces need world/root-space pivots. Closed poses remain
    # visually identical because no pivot, cube origin or UV is changed.
    for b in ("left_forearm","right_forearm","left_boot","right_boot",
              "left_shoulder","right_shoulder","reactor"):
        index[b]["parent"]="root"
    for i in ("rear_left","rear_right"):
        assert abs(index[i]["pivot"][0])==4.4
    an=src["animations"]
    assert len(an)==7 and all(FACES+x in an for x in
        ("equip","unequip","recall_flight","recall_brake","recall_dock"))
    for action in ("equip","unequip","recall_brake","recall_dock"):
        an[FACES+action]=make_clip(action)
    # The already-correct B625 head-first horizontal flight is unchanged.
    assert all(k["vector"][0]==90 for k in an[FACES+"recall_flight"]["bones"]["root"]["rotation"].values())
    # UV and texture art are left exactly untouched. No assets from the ZIP.
    modelpath.write_text(json.dumps(model,indent=2)+"\n",encoding="utf-8")
    animpath.write_text(json.dumps(src,indent=2)+"\n",encoding="utf-8")

def replace(s,old,new,label):
    n=s.count(old)
    assert n==1,("B626_JAVA_SOURCE_DRIFT",label,n)
    return s.replace(old,new,1)

# NORMAL equip and unequip must run for the entire assembly. Physical owner
# stays on the invisible real ArmorStand until the final authoritative step.
world=J/"powerarmor/PowerArmorSuitWorld.java"
s=world.read_text(encoding="utf-8")
start=s.find(" private static Animation startAnimation(")
end=s.find(" @SubscribeEvent public static void transitionTick(",start)
assert 0<=start<end,("B626_NORMAL_VISUAL_LIFECYCLE_DRIFT",start,end)
region=s[start:end]
assert region.count("new Animation(stand,20,entering,")==2,("B626_NORMAL_DURATION_SOURCE_DRIFT",region.count("new Animation(stand,20,entering,"))
region=region.replace("new Animation(stand,20,entering,","new Animation(stand,52,entering,")
s=s[:start]+region+s[end:]
s=replace(s,"int t=21-animation.ticks();","int t=53-animation.ticks();","normal-tick-count")
# Safe fallback if a client cannot render GeckoLib; preserve the previous
# 20-frame armor-stand pose trajectory, stretched to the full 52 ticks.
original="pose(stand,t,animation.entering());"
if s.count(original)==1:
    s=s.replace(original,"pose(stand,Math.min(20,(int)Math.round(t*20.0D/52.0D)),animation.entering());",1)
assert 'stand.addTag("xsxlabs_v175_temporarily_hidden_world_suit")' in s
assert "v175RestoreWorldSuitOnLoad" in s
assert "stand.removeTag" in s and "stand.entityTags()" in s
world.write_text(s,encoding="utf-8")

visual=J/"powerarmor/PowerArmorVisualEntity.java"
s=visual.read_text(encoding="utf-8")
# Longer server safety window; recall visuals are still protected by
# PowerArmorRecall.isVisualActive() and are explicitly discarded on release.
s=replace(s,"tickCount>23","tickCount>55","visual-expiry-52ticks")
assert "PowerArmorRecall.isVisualActive(getUUID())" in s
assert "V175_RECALL_VISUAL_LIFETIME" in s
visual.write_text(s,encoding="utf-8")

recall=J/"powerarmor/PowerArmorRecall.java"
s=recall.read_text(encoding="utf-8")
s=replace(s,"visual.beginPhase(progress<8?3:4);",
 "visual.beginPhase(progress<12?3:4);","brake-vs-dock-split")
s=replace(s,"if(progress<28){","if(progress<52){","full-recall-montage")
# Once at the docking position, the 160-tick flight timeout must no longer
# cancel the inventory transaction while the deterministic assembly runs.
s=replace(s,"if(f.ticks()>MAX_FLIGHT){abort(",
 "if(f.ticks()>MAX_FLIGHT&&!DOCKING.containsKey(player.getUUID())){abort(",
 "flight-timeout-excludes-dock")
assert "PowerArmorSuitWorld.recallEquip(stand,player)" in s
assert "DOCKING.remove(player.getUUID())" in s
assert "visual.beginPhase(2)" in s
recall.write_text(s,encoding="utf-8")
print(TAG+": 24 original tier-textured suits, 17 independently arriving parts, 52-tick montage, single faceplate, rollback-safe timed recall")
