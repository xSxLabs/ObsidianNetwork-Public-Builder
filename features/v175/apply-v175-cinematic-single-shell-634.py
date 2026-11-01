#!/usr/bin/env python3
"""B634: film-readable normal rear-entry/exit using ONE textured outer shell.
B632 base geometry, B633 owner-facing exit placement. Recall unchanged.
"""
import hashlib, json, os, math
from pathlib import Path

A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
MARK="V175_B634_SINGLE_SHELL_CINEMATIC"
TICKS=48
SECONDS=TICKS/20.0
def sha(path):
 return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,obj):
 path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def smooth(a,b,t):
 s=max(0.0,min(1.0,(t-a)/(b-a)))
 return s*s*(3-2*s)
def opened(t,start,fully,closing,closed):
 return smooth(start,fully,t)*(1-smooth(closing,closed,t))
# GeckoLib times are SECONDS, not fractions of animation_length.
TIMES=(0,.05,.06,.061,.10,.14,.18,.24,.30,.38,.45,.57,.68,.72,.78,.84,.88,.881,.94,.98,1.0)
def track(fn):
 return {str(round(t*SECONDS,3)):{
    "vector":[round(float(v),4) for v in fn(t)],
    "easing":"easeInOutSine"} for t in TIMES}
def normal(action):
 # Faceplate lifts FIRST, then two back halves swing OUTWARD on fixed outer
 # hinges. Clear, extended walk-in/exit hold. Doors return, mask seals last.
 # Both animations finish at a geometrically closed (zero) pose.
 enter=action=="equip"
 def mask(t):
  return opened(t,.05 if enter else .02,.18 if enter else .14,.73,.94)
 def doors(t):
  return opened(t,.13 if enter else .11,.34 if enter else .32,.67,.90)
 def arms(t):
  return opened(t,.17,.39,.67,.89)
 bones={
  "root":{"rotation":track(lambda t:(0,0,0))},
  "rear_left":{"rotation":track(lambda t:(0,-114*doors(t),0)),
               "position":track(lambda t:(0,0,0))},
  "rear_right":{"rotation":track(lambda t:(0,114*doors(t),0)),
                "position":track(lambda t:(0,0,0))},
  "faceplate":{"rotation":track(lambda t:(-115*mask(t),0,0)),
               "position":track(lambda t:(0,.75*mask(t),.35*mask(t)))},
  "left_arm":{"rotation":track(lambda t:(0,0,-8*arms(t)))},
  "right_arm":{"rotation":track(lambda t:(0,0,8*arms(t)))},
  # While standing, chest, forearms, boots and legs do not disassemble.
  # Those independent movements belong exclusively to RECALL.
  "torso_inner_spine":{"scale":{
    "0.0":{"vector":[1,1,1],"easing":"easeInOutSine"},
    str(round(.06*SECONDS,3)):{"vector":[1,1,1],"easing":"easeInOutSine"},
    str(round(.061*SECONDS,3)):{"vector":[0,0,0],"easing":"easeInOutSine"},
    str(round(.88*SECONDS,3)):{"vector":[0,0,0],"easing":"easeInOutSine"},
    str(round(.881*SECONDS,3)):{"vector":[1,1,1],"easing":"easeInOutSine"},
    str(SECONDS):{"vector":[1,1,1],"easing":"easeInOutSine"}
  }}
 }
 for part in ("chest_left","chest_right","left_leg","right_leg",
              "left_forearm","right_forearm","left_boot","right_boot"):
  bones[part]={"rotation":track(lambda t:(0,0,0)),
               "position":track(lambda t:(0,0,0))}
 assert abs(bones["rear_left"]["rotation"][str(SECONDS)]["vector"][1])<1e-5
 assert bones["faceplate"]["rotation"][str(SECONDS)]["vector"]==[0,0,0]
 return {"animation_length":SECONDS,"loop":"hold_on_last_frame","bones":bones}

protect=[J/"powerarmor/PowerArmorRecall.java",
         J/"conduit/EnergyConduitTicker.java"]
before_protected={str(p):sha(p) for p in protect}
for mk in range(1,25):
 stem="power_armor_visual_mk"+str(mk)
 modelpath=A/"geckolib/models/entity"/(stem+".geo.json")
 animpath=A/"geckolib/animations/entity"/(stem+".animation.json")
 texpath=A/"textures/entity"/(stem+".png")
 assert all(p.is_file() for p in (modelpath,animpath,texpath)),("MISSING",mk)
 before_tex=sha(texpath)
 model=json.loads(modelpath.read_text(encoding="utf-8"))
 animations=json.loads(animpath.read_text(encoding="utf-8"))
 clips=animations["animations"]
 old_recall={n:json.dumps(clips["animation.power_armor."+n],sort_keys=True)
             for n in ("recall_flight","recall_brake","recall_dock")}
 bones=model["minecraft:geometry"][0]["bones"]
 idx={b["name"]:b for b in bones}
 assert len(bones)==len(idx)==28,(mk,"B632 rig drift")
 assert len(idx["spine"]["cubes"])==1
 assert idx["spine"]["cubes"][0]["origin"]==[-4.4,13,-3.4]
 assert idx["chest_left"]["cubes"][0]["uv"]["north"]=={"uv":[20,20],"uv_size":[4,12]}
 assert idx["chest_right"]["cubes"][0]["uv"]["north"]=={"uv":[24,20],"uv_size":[4,12]}
 assert idx["rear_left"]["cubes"][0]["uv"]["south"]=={"uv":[32,20],"uv_size":[4,12]}
 assert idx["rear_right"]["cubes"][0]["uv"]["south"]=={"uv":[36,20],"uv_size":[4,12]}
 assert idx["faceplate"]["cubes"][0]["uv"]["north"]=={"uv":[8,8],"uv_size":[8,8]}
 # B632 accidentally stacked a full painted front torso directly BEHIND
 # the two matching painted half-chest panels. Remove that redundant CUBE,
 # not the spine bone: reactor and inner shell remain its children.
 idx["spine"]["cubes"]=[]
 assert idx["reactor"]["parent"]=="spine"
 # The actual front is now ONLY the two contiguous, real worn-UV chest plates.
 # No second solid synthetic colored box in the animated normal suit.
 assert len(idx["chest_left"]["cubes"])==len(idx["chest_right"]["cubes"])==1
 # Shoulder decorative plates were exactly coplanar with top/side arm faces,
 # creating flash and mismatched patterns. Make them slightly external so
 # they are legitimate armoured caps, not z-fighting duplicate surfaces.
 for part,origin in (("left_shoulder",[-9.72,21.96,-2.73]),
                     ("right_shoulder",[4.27,21.96,-2.73])):
  cap=idx[part]["cubes"][0]
  cap["origin"]=origin
  cap["size"]=[5.45,3.2,5.45]
 # Delete seven detached accessory MICRO-CUBES. Their bones persist so
 # hierarchy/recall keyframes remain valid, but floating gaskets and rails
 # can never occlude the genuine rear doors and single hinged faceplate.
 remove=("rear_left_hinge","rear_right_hinge","rear_left_gasket",
         "rear_right_gasket","faceplate_left_rail",
         "faceplate_right_rail","faceplate_forehead_lock")
 for part in remove:
  assert len(idx[part]["cubes"])==1,(mk,part)
  idx[part].pop("cubes")
 # No duplicate visor plate; the real single hinged mask stays.
 assert "cubes" not in idx["visor"]
 for action in ("equip","unequip"):
  assert clips["animation.power_armor."+action]["animation_length"]==1.0
  clips["animation.power_armor."+action]=normal(action)
 for n,blob in old_recall.items():
  assert json.dumps(clips["animation.power_armor."+n],sort_keys=True)==blob,(mk,n,"RECALL DRIFT")
 write(modelpath,model)
 write(animpath,animations)
 assert sha(texpath)==before_tex,(mk,"WEARER TEXTURE MODIFIED")

# Authoritative 48-tick lifetime and visual 2.4-second clip must agree.
# Inventory ownership and failure recovery are unchanged.
world=J/"powerarmor/PowerArmorSuitWorld.java"
s=world.read_text(encoding="utf-8")
assert s.count("new Animation(stand,20,entering,")==3,("B634_WORLD_DURATION",s.count("new Animation(stand,20,entering,"))
assert s.count("int t=21-animation.ticks();")==1,"B634_PROGRESS_ANCHOR"
assert s.count("progress/20F")==1,"B634_VANILLA_FALLBACK_PROGRESS"
assert "V175_B633_EXIT_BACK_TO_PLAYER" in s
assert "BlockPos p=player.blockPosition().relative(player.getDirection());" in s
assert "PowerArmorRuntime.SLOTS" in s and "stand.discard();" in s
s=s.replace("new Animation(stand,20,entering,","new Animation(stand,48,entering,")
s=s.replace("int t=21-animation.ticks();","int t=49-animation.ticks();")
s=s.replace("progress/20F","progress/48F")
# The vanilla stand is always a persistent inventory owner; the temporary
# GeckoLib suit is the ONLY rendered mesh while a real visual is alive.
world.write_text(s,encoding="utf-8")

visual=J/"powerarmor/PowerArmorVisualEntity.java"
s=visual.read_text(encoding="utf-8")
assert s.count("tickCount>23")==1,"B634_NORMAL_VISUAL_LIFETIME"
assert "PowerArmorRecall.isVisualActive(getUUID())" in s
assert "V175_PHASE" in s
s=s.replace("tickCount>23","tickCount>51",1)
assert '\"animation.power_armor.equip\":\"animation.power_armor.unequip\"' in s
visual.write_text(s,encoding="utf-8")

# Client rendering safeguard: vanilla invisible armor stands may STILL draw
# their equipped armor. Suppress ONLY complete invisible power-armor stands
# in the 26.1 entity render-state pipeline; when the visual fails to spawn,
# the stand remains visible, so the player never loses the real item mesh.
render=J/"client/PowerArmorTransitionRenderGuard.java"
assert not render.exists(),"B634_RENDER_GUARD_ALREADY_EXISTS"
render.write_text(r'''package dev.obsidiannetwork.client;

import net.minecraft.resources.Identifier;
import net.minecraft.util.context.ContextKey;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.renderstate.RegisterRenderStateModifiersEvent;
import net.neoforged.neoforge.client.event.RenderLivingEvent;
import net.minecraft.client.renderer.entity.ArmorStandRenderer;

/** B634: never draw the real four-stack vanilla owner on top of its
 * GeckoLib animation. No equipment is moved, cleared or duplicated.
 * A missing cinematic visual leaves the vanilla owner fully visible.
 */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class PowerArmorTransitionRenderGuard {
 private PowerArmorTransitionRenderGuard(){}
 private static final ContextKey<Boolean> HIDE_OWNER=new ContextKey<>(
   Identifier.fromNamespaceAndPath("obsidiannetwork","v175_hide_armor_owner"));
 @SubscribeEvent public static void register(RegisterRenderStateModifiersEvent event){
  event.registerEntityModifier(ArmorStandRenderer.class,(stand,state)->{
   boolean hidden=stand.isInvisible()
      &&dev.obsidiannetwork.powerarmor.PowerArmorSuitWorld.full(stand);
   state.setRenderData(HIDE_OWNER,hidden);
  });
 }
 @SubscribeEvent public static void render(RenderLivingEvent.Pre<?,?,?> event){
  if(event.getRenderState().getRenderDataOrDefault(HIDE_OWNER,false))
   event.setCanceled(true);
 }
}
''',encoding="utf-8")
assert {str(p):sha(p) for p in protect}==before_protected,"B634_POWER_OR_RECALL_DRIFT"
print(MARK+": 24 single textured shells; 114-degree rear split; single 115-degree mask; synchronized 48-tick runtime; client owner-layer suppression; recall untouched")
