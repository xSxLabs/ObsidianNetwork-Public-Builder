#!/usr/bin/env python3
"""B649 after B648: hollow real exterior arm/leg shells; proper REAR shoulder
opening of joined arm+back; show exiting player only after full hatch opening.
Keeps transfer-safe existing exit() and all 24 real armor textures unmodified.
"""
import copy, hashlib, json, os, re
from pathlib import Path
A=Path(os.environ['V1_RESOURCE_ROOT'])/'assets/obsidiannetwork'
J=Path(os.environ['V1_SOURCE_ROOT'])/'dev/obsidiannetwork'

def hashfile(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def smooth(a,b,t):
 if t<=a:return 0.
 if t>=b:return 1.
 x=(t-a)/(b-a);return x*x*(3-2*x)
def pose(x):return {'vector':[round(float(i),4) for i in x],'easing':'easeInOutSine'}
def keys(fn):return {str(round(i*.04,4)):pose(fn(i/100)) for i in range(101)}
def wing(t):return smooth(.31,.53,t)*(1-smooth(.70,.87,t))
def fold(t):return smooth(.08,.29,t)*(1-smooth(.86,.975,t))
def shell_on(t):return 1-smooth(.18,.285,t)*(1-smooth(.855,.945,t))
def hull(c):
 """Replace a closed solid cube (plus any inner solid) with 5 genuine thin
  shell panels. The sixth/back face is an OPEN cavity, covered only by the
  existing separately modeled exterior rear armor panel. No filled core.
  Every outside face retains the original per-MK worn-armor UV exactly.
 """
 x,y,z=c['origin'];w,h,d=c['size'];old=c['uv'];a=.22
 assert w>4 and h>=4 and d>=4,(w,h,d)
 def panel(p,s,outward,inside):
  u=copy.deepcopy(old)
  opposite={'north':'south','south':'north','east':'west','west':'east','up':'down','down':'up'}[outward]
  u[opposite]=copy.deepcopy(old[inside])
  return {'origin':[round(float(q),4) for q in p],
          'size':[round(float(q),4) for q in s],'uv':u,'inflate':0}
 return [
  panel((x,y,z),(w,h,a),'north','north'),
  panel((x,y,z+a),(a,h,d-a),'west','west'),
  panel((x+w-a,y,z+a),(a,h,d-a),'east','east'),
  panel((x+a,y+h-a,z+a),(w-2*a,a,d-a),'up','up'),
  panel((x+a,y,z+a),(w-2*a,a,d-a),'down','down')]

for mk in range(1,25):
 stem=f'power_armor_visual_mk{mk}'
 model=A/'geckolib/models/entity'/(stem+'.geo.json')
 animation=A/'geckolib/animations/entity'/(stem+'.animation.json')
 sk='power_armor' if mk==1 else f'power_armor_mk{mk}'
 pngs=[A/'textures/entity'/(stem+'.png'),A/'textures/entity/equipment/humanoid'/(sk+'.png'),A/'textures/entity/equipment/humanoid_leggings'/(sk+'.png')]
 original_png_hashes=[hashfile(p) for p in pngs]
 m=json.loads(model.read_text(encoding='utf-8'))
 a=json.loads(animation.read_text(encoding='utf-8'))
 bones=m['minecraft:geometry'][0]['bones'];idx={b['name']:b for b in bones}
 assert len(bones)==len(idx)==40,(mk,'B648 source expected')
 for side,sgn in (('left',-1),('right',1)):
  unit=idx[side+'_entry_unit'];arm=idx[side+'_arm'];rear=idx['rear_'+side]
  assert unit['parent']=='root' and arm['parent']==rear['parent']==unit['name']
  assert unit['pivot']==[sgn*6.3,23,0],(mk,side,'B648 shoulder pivot')
  unit['pivot']=[sgn*4.4,23,3.4]
  for part in (side+'_arm',side+'_forearm',side+'_leg',side+'_boot'):
   b=idx[part]
   assert len(b['cubes']) in (1,2),(mk,part)
   old=b['cubes'][0]
   assert old['size'][2]==5,(mk,part,'solid source dimensions')
   b['cubes']=hull(old)
   assert len(b['cubes'])==5
  for mode in ('equip','unequip'):
   clip=a['animations']['animation.power_armor.'+mode]
   assert clip['animation_length']==4.,mk
   t=clip['bones']
   t[side+'_entry_unit']['rotation']=keys(lambda p,s=sgn:(0,-s*96*wing(p),0))
   t['rear_'+side]['rotation']=keys(lambda p,s=sgn:(0,-s*112*fold(p),0))
   for bname in (side+'_arm_back_shell',side+'_forearm_back_shell'):
    assert bname in t and t[bname]['rotation']['0.0']['vector']==[0,0,0],(mk,bname)
    t[bname]['rotation']=keys(lambda p:(0,0,0))
    t[bname]['scale']=keys(lambda p:(shell_on(p),)*3)
   assert t[side+'_entry_unit']['rotation']['1.2']['vector']==[0,0,0]
   assert abs(t[side+'_entry_unit']['rotation']['2.12']['vector'][1])>95
   assert abs(t['rear_'+side]['rotation']['1.2']['vector'][1])>110
 assert a['animations']['animation.power_armor.recall_approach']['animation_length']==.55
 face=idx['faceplate']['cubes'][0]['uv']
 assert face['north']==face['south']=={'uv':[8,8],'uv_size':[8,8]},mk
 model.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 animation.write_text(json.dumps(a,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 assert [hashfile(p) for p in pngs]==original_png_hashes,(mk,'original armor PNG modified')

world=J/'powerarmor/PowerArmorSuitWorld.java'
s=world.read_text(encoding='utf-8')
needle='PowerArmorRecall.rememberLastWorn(player,stand);'
assert s.count(needle)==1,('B649_WORLD_SUCCESS_ONLY_ANCHOR',s.count(needle))
s=s.replace(needle,needle+'\n  PowerArmorExitReveal649.begin(player); // after successful transfer, show player only when hatch opens',1)
assert s.count('PowerArmorExitReveal649.begin(player);')==1
world.write_text(s,encoding='utf-8')

helper=J/'powerarmor/PowerArmorExitReveal649.java'
assert not helper.exists(),('B649 helper duplicated')
helper.write_text('''package dev.obsidiannetwork.powerarmor;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;

/** B649: purely visual exit staging; never owns/duplicates inventory items.
 * Vanishes only while the detached suit is opening. Entry is unchanged.
 * Player is always restored on tick threshold and logout.
 */
@EventBusSubscriber(modid="obsidiannetwork")
public final class PowerArmorExitReveal649 {
 private static final Map<UUID, Integer> HIDDEN_UNTIL=new HashMap<>();
 private PowerArmorExitReveal649(){}
 public static void begin(ServerPlayer p){
  if(p.isInvisible())return; // respect any existing vanilla invisibility
  p.setInvisible(true);
  // Normal B649 shared rear hatches finish opening by 42 ticks; stay
  // concealed for 48 ticks, still well before they begin to close.
  HIDDEN_UNTIL.put(p.getUUID(),p.tickCount+48);
 }
 @SubscribeEvent public static void tick(PlayerTickEvent.Post e){
  if(!(e.getEntity() instanceof ServerPlayer p))return;
  Integer end=HIDDEN_UNTIL.get(p.getUUID());
  if(end==null)return;
  if(p.tickCount>=end){
   HIDDEN_UNTIL.remove(p.getUUID());
   p.setInvisible(false);
  }else p.setInvisible(true);
 }
 @SubscribeEvent public static void logout(PlayerEvent.PlayerLoggedOutEvent e){
  if(e.getEntity() instanceof ServerPlayer p && HIDDEN_UNTIL.remove(p.getUUID())!=null)
   p.setInvisible(false);
 }
 @SubscribeEvent public static void clone(PlayerEvent.Clone e){
  HIDDEN_UNTIL.remove(e.getOriginal().getUUID());
 }
}
''',encoding='utf-8')
print('V175_B649: 24 real hollow arms+legs; 2 rear-pivot wings; mask/Recall unchanged; exit reveal at 48 ticks after verified transfer')
