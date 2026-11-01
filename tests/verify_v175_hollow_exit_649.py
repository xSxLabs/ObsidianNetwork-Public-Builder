#!/usr/bin/env python3
"""Fail closed after overlay: genuine arm/leg void and correct rear-hinge opening."""
import json,os
from pathlib import Path
from PIL import Image
A=Path(os.environ['V1_RESOURCE_ROOT'])/'assets/obsidiannetwork'
J=Path(os.environ['V1_SOURCE_ROOT'])/'dev/obsidiannetwork'
for mk in range(1,25):
 stem=f'power_armor_visual_mk{mk}'
 data=json.loads((A/'geckolib/models/entity'/(stem+'.geo.json')).read_text())
 animation=json.loads((A/'geckolib/animations/entity'/(stem+'.animation.json')).read_text())['animations']
 b={k['name']:k for k in data['minecraft:geometry'][0]['bones']}
 assert len(b)==40,mk
 for side,sgn in (('left',-1),('right',1)):
  u=side+'_entry_unit'
  assert b[u]['pivot']==[sgn*4.4,23,3.4],(mk,'wrong rear pivot')
  assert b[side+'_arm']['parent']==b['rear_'+side]['parent']==u,(mk,side,'rear not coupled')
  for seg in ('arm','forearm','leg','boot'):
   part=b[side+'_'+seg]
   assert len(part['cubes'])==5,(mk,side,seg,'solid core still exists')
   cube=part['cubes'];xs=[c['size'][0] for c in cube];zs=[c['size'][2] for c in cube]
   assert zs[0]<.24 and xs[1]<.24 and xs[2]<.24,(mk,'hollow shell failed')
   assert all(c['inflate']==0 for c in cube)
  for action in ('equip','unequip'):
   clip=animation['animation.power_armor.'+action]
   assert clip['animation_length']==4
   t=clip['bones']
   assert t[u]['rotation']['1.2']['vector']==[0,0,0]
   assert abs(t[u]['rotation']['2.12']['vector'][1])>95
   assert abs(t['rear_'+side]['rotation']['1.2']['vector'][1])>110
   assert t[side+'_arm_back_shell']['scale']['2.12']['vector']==[0,0,0]
   assert t[side+'_forearm_back_shell']['scale']['2.12']['vector']==[0,0,0]
   assert t[side+'_arm_back_shell']['scale']['4.0']['vector']==[1,1,1]
 for mode in ('recall_flight','recall_approach','recall_brake','recall_dock'):
  c=animation['animation.power_armor.'+mode]
  assert 'left_entry_unit' not in c['bones'] and 'right_entry_unit' not in c['bones']
  assert all(float(k)<=c['animation_length']+.0001 for v in c['bones'].values() for tr in v.values() for k in tr),(mk,mode)
 worn='power_armor' if mk==1 else f'power_armor_mk{mk}'
 with Image.open(A/'textures/entity'/(stem+'.png')) as im:atlas=im.convert('RGBA')
 with Image.open(A/'textures/entity/equipment/humanoid'/(worn+'.png')) as im:top=im.convert('RGBA')
 assert atlas.crop((0,0,64,32)).tobytes()==top.tobytes(),mk
assert 'PowerArmorExitReveal649.begin(player);' in (J/'powerarmor/PowerArmorSuitWorld.java').read_text()
s=(J/'powerarmor/PowerArmorExitReveal649.java').read_text()
assert 'p.tickCount+48' in s and 'p.setInvisible(false);' in s and 'PlayerLoggedOutEvent' in s
print('V175_B649_ALL_24_HOLLOW_ARM_LEG_REAR_WINGS_EXIT_REVEAL_PASS')
