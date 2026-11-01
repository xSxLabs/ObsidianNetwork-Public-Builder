#!/usr/bin/env python3
"""Fail closed B647 generated-resource verification for all 24 authentic suits."""
import json,math,os
from pathlib import Path
from PIL import Image
A=Path(os.environ['V1_RESOURCE_ROOT'])/'assets/obsidiannetwork'
def getfirst(t):return next(iter(t.values()))['vector']
def getlast(t):return list(t.values())[-1]['vector']
for mk in range(1,25):
    name='power_armor_visual_mk'+str(mk)
    model=json.loads((A/'geckolib/models/entity'/(name+'.geo.json')).read_text())
    ani=json.loads((A/'geckolib/animations/entity'/(name+'.animation.json')).read_text())['animations']
    bones={b['name']:b for b in model['minecraft:geometry'][0]['bones']}
    assert len(bones)==38,mk
    head=bones['helmet']
    assert len(head['cubes'])==4,(mk,'helmet roof or walls missing')
    assert head['cubes'][2]['origin']==[-4.5,32.55,-4.5]
    assert head['cubes'][2]['size']==[9,.95,9]
    assert head['cubes'][2]['uv']['up']=={'uv':[8,0],'uv_size':[8,8]}
    assert head['cubes'][3]['uv']['down']=={'uv':[16,0],'uv_size':[8,8]}
    for side in ('left','right'):
        plate=bones['helmet_'+side]
        assert plate['parent']=='helmet' and len(plate['cubes'])==1,(mk,side,'whole helmet split')
        assert plate['cubes'][0]['origin'][2]==3.55,(mk,side,'not rear panel')
        assert plate['cubes'][0]['size'][2]==.95
        assert plate['cubes'][0]['uv']['south']['uv_size']==[4,8]
    mask=bones['faceplate']
    assert mask['pivot']==[0,29.25,-4.55]
    assert mask['cubes'][0]['uv']['north']=={'uv':[8,8],'uv_size':[8,8]}
    for action in ('equip','unequip'):
        clip=ani['animation.power_armor.'+action]
        assert clip['animation_length']==4.0,mk
        m=clip['bones']['faceplate']
        assert getfirst(m['position'])==getlast(m['position'])==[0,0,0]
        assert getfirst(m['rotation'])==getlast(m['rotation'])==[0,0,0]
        assert max(k['vector'][2] for k in m['position'].values())>=4.1,(mk,'not moved to rear')
        assert max(k['vector'][1] for k in m['position'].values())>=4.9,(mk,'not above head')
        assert max(k['vector'][0] for k in m['rotation'].values())>=89,(mk,'face not rotated upward')
        for side in ('left','right'):
            f=clip['bones']['helmet_'+side]['rotation']
            assert getfirst(f)==getlast(f)==[0,0,0]
            assert max(abs(v['vector'][1]) for v in f.values())>100
        assert all(v['vector']==[0,0,0] for side in ('left','right') for p in ('arm','leg') for v in clip['bones'][side+'_'+p]['rotation'].values()),(mk,'X pose')
    brake=ani['animation.power_armor.recall_brake']
    dock=ani['animation.power_armor.recall_dock']
    app=ani['animation.power_armor.recall_approach']
    assert brake['animation_length']==.6 and dock['animation_length']==2 and app['animation_length']==.55
    for c in ('rotation','position'):
        assert getlast(brake['bones']['faceplate'][c])==getfirst(dock['bones']['faceplate'][c])
    assert getlast(brake['bones']['faceplate']['position'])==[0.,5.,4.15],mk
    assert getlast(brake['bones']['faceplate']['rotation'])==[90.,0.,0.],mk
    for n,tr in app['bones'].items():
        if n=='root':continue
        for channel,fr in tr.items():
            assert getlast(fr)==getfirst(brake['bones'][n][channel]),(mk,n,channel,'phase reset')
            assert getlast(brake['bones'][n][channel])==getfirst(dock['bones'][n][channel]),(mk,n,channel,'phase reset')
    for mode in ('recall_brake','recall_dock'):
        clip=ani['animation.power_armor.'+mode]
        assert all(float(t)<=clip['animation_length']+.0001 for tracks in clip['bones'].values() for channel in tracks.values() for t in channel),(mk,mode)
    worn='power_armor' if mk==1 else 'power_armor_mk'+str(mk)
    with Image.open(A/'textures/entity'/(name+'.png')) as im:tex=im.convert('RGBA')
    with Image.open(A/'textures/entity/equipment/humanoid'/(worn+'.png')) as im:top=im.convert('RGBA')
    with Image.open(A/'textures/entity/equipment/humanoid_leggings'/(worn+'.png')) as im:legs=im.convert('RGBA')
    assert tex.crop((0,0,64,32)).tobytes()==top.tobytes()
    assert tex.crop((0,32,64,64)).tobytes()==legs.tobytes()
print('B647_ALL_24_REAR_PLATE_ONLY_CROWN_GLIDE_RECALL_VISUAL_CONTRACT_PASS')
