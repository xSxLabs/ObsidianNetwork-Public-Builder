#!/usr/bin/env python3
"""B647: ONLY the two halves of the rear helmet plate swing open, not head sides/top.
Correct faceplate pivot and positive rearward slide onto the permanent helmet roof.
Runs directly after B646, for the same 24 unchanged authentic armor UV atlas PNGs.
No modifications of equipment items, gameplay, inventory, server lifetime or FE.
"""
import copy,hashlib,json,math,os
from pathlib import Path
A=Path(os.environ['V1_RESOURCE_ROOT'])/'assets/obsidiannetwork'
TAG='V175_B647_ONLY_REAR_PLATE_AND_REAL_CROWN_MASK'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ease(a,b,t):
    if t<=a:return 0.
    if t>=b:return 1.
    x=(t-a)/(b-a)
    return x*x*(3-2*x)
def frame(v):return {'vector':[round(float(x),4) for x in v],'easing':'easeInOutSine'}
def frames(duration,fn,n=80):
    return {str(round(i*duration/n,4)):frame(fn(i/n)) for i in range(n+1)}
def key0(track):return next(iter(track.values()))['vector']
def keylast(track):return list(track.values())[-1]['vector']
def mask(open_amount):
    """Bone pivot is geometric center of original 8px-high faceplate.

    Starts flush on the face, rises clear in front, rolls OUTWARD (the original
    NORTH/eyes surface ultimately faces UP), slides visibly 4.15px backwards,
    and lands centered 0.27px ABOVE the intact 33.5px-high crown.
    """
    p=max(0.,min(1.,open_amount))
    stops=(
      (0.,(0.,0.,0.),0.),
      (.24,(0.,2.35,-.65),14.),
      (.48,(0.,4.15,-.6),43.),
      (.70,(0.,4.90,1.25),73.),
      (.88,(0.,5.00,3.35),88.),
      (1.,(0.,5.00,4.15),90.),
    )
    for (a,v,r),(b,w,q) in zip(stops,stops[1:]):
        if p<=b:
            f=ease(a,b,p)
            return tuple(v[i]+(w[i]-v[i])*f for i in range(3)),r+(q-r)*f
    return stops[-1][1],stops[-1][2]
def apply_mask(clip,duration,openness):
    plate=clip['bones'].setdefault('faceplate',{})
    plate['position']=frames(duration,lambda t:mask(openness(t))[0])
    plate['rotation']=frames(duration,lambda t:(mask(openness(t))[1],0.,0.))
def same(a,b):return abs(a-b)<1e-6

def restore_full_plate(left,right,face):
    """Rejoin only the B646 split TOP or BOTTOM original cuboid and its UV."""
    assert left['origin'][0]==-4.5 and right['origin'][0]==0,(face,'x')
    assert left['size'][0]==right['size'][0]==4.5,(face,'width')
    assert left['origin'][1:]==right['origin'][1:],face
    assert left['size'][1:]==right['size'][1:],face
    cub=copy.deepcopy(left)
    cub['size'][0]=9
    for side in ('north','south','up','down'):
        l=left['uv'][side];r=right['uv'][side]
        assert same(r['uv'][0],l['uv'][0]+l['uv_size'][0]),(face,side,'UV seam')
        assert same(l['uv'][1],r['uv'][1]) and same(l['uv_size'][1],r['uv_size'][1]),face
        cub['uv'][side]['uv_size'][0]=round(l['uv_size'][0]+r['uv_size'][0],4)
    cub['uv']['east']=copy.deepcopy(right['uv']['east'])
    cub['uv']['west']=copy.deepcopy(left['uv']['west'])
    assert cub['uv']['up']==({'uv':[8,0],'uv_size':[8,8]} if face=='roof' else {'uv':[25,103],'uv_size':[9,9]}),(face,'top original artwork')
    assert cub['uv']['down']==({'uv':[42,103],'uv_size':[9,9]} if face=='roof' else {'uv':[16,0],'uv_size':[8,8]}),(face,'bottom original artwork')
    return cub

def geometry_mask_samples(pos,rotation):
    """Return 4 corners x/y/z of genuine faceplate at a centered pivot.
    Source pixels are 8 by 8 (north is outside) and thickness 0.96.
    """
    x0,y0,z0=0,29.25,-4.55
    theta=math.radians(rotation)
    return [(x0+dx+pos[0],y0+dy*math.cos(theta)-dz*math.sin(theta)+pos[1],
             z0+dy*math.sin(theta)+dz*math.cos(theta)+pos[2])
            for dx in (-4,4) for dy in (-4,4) for dz in (-.48,.48)]

def run():
    for mk in range(1,25):
        name=f'power_armor_visual_mk{mk}'
        model=A/'geckolib/models/entity'/(name+'.geo.json')
        animation=A/'geckolib/animations/entity'/(name+'.animation.json')
        texture=A/'textures/entity'/(name+'.png')
        worn='power_armor' if mk==1 else f'power_armor_mk{mk}'
        pngs=(texture,A/'textures/entity/equipment/humanoid'/(worn+'.png'),
              A/'textures/entity/equipment/humanoid_leggings'/(worn+'.png'))
        original_hashes=[sha(x) for x in pngs]
        m=json.loads(model.read_text(encoding='utf8'))
        a=json.loads(animation.read_text(encoding='utf8'))
        bones=m['minecraft:geometry'][0]['bones']
        bs={b['name']:b for b in bones}
        assert len(bones)==38 and bs['helmet']['parent']=='root',mk
        assert 'cubes' not in bs['helmet'],mk
        l,r=bs['helmet_left'],bs['helmet_right']
        assert l['parent']==r['parent']=='helmet' and len(l['cubes'])==len(r['cubes'])==4,mk
        assert l['cubes'][0]['uv']['south']=={'uv':[24,8],'uv_size':[4,8]},mk
        assert r['cubes'][0]['uv']['south']=={'uv':[28,8],'uv_size':[4,8]},mk
        # Return original static head walls and full top/bottom painted surfaces.
        # ONLY back panel halves remain as independently animated real parts.
        bs['helmet']['cubes']=[copy.deepcopy(l['cubes'][1]),copy.deepcopy(r['cubes'][1]),
           restore_full_plate(l['cubes'][2],r['cubes'][2],'roof'),
           restore_full_plate(l['cubes'][3],r['cubes'][3],'bottom')]
        l['cubes']=[l['cubes'][0]]
        r['cubes']=[r['cubes'][0]]
        assert len(bs['helmet']['cubes'])==4 and len(l['cubes'])==len(r['cubes'])==1,mk
        # Fix real center of the mask instead of rotating about eyebrow hinge.
        # With +90 degrees its genuine NORTH eye artwork points upwards.
        visor=bs['faceplate']
        assert visor['parent']=='helmet' and visor['pivot']==[0,33.45,-4.45],mk
        assert visor['cubes'][0]['origin']==[-4,25.25,-4.55],mk
        assert visor['cubes'][0]['size']==[8,8,.96],mk
        visor['pivot']=[0,29.25,-4.55]
        clips=a['animations']
        for action in ('equip','unequip'):
            clip=clips['animation.power_armor.'+action]
            assert clip['animation_length']==4.0,(mk,action)
            # Keep all normal body and rear plate hinge timings unchanged.
            if action=='equip':
                openness=lambda t:ease(.015,.27,t)*(1-ease(.82,.99,t))
            else:
                openness=lambda t:ease(.02,.23,t)*(1-ease(.87,.99,t))
            apply_mask(clip,4.,openness)
            assert keylast(clip['bones']['faceplate']['position'])==[0,0,0]
        brake=clips['animation.power_armor.recall_brake']
        dock=clips['animation.power_armor.recall_dock']
        assert brake['animation_length']==.6 and dock['animation_length']==2.,mk
        apply_mask(brake,.6,lambda t:ease(0,1,t))
        apply_mask(dock,2.,lambda t:1-ease(.84,1.,t))
        for ch in ('position','rotation'):
            assert keylast(brake['bones']['faceplate'][ch])==key0(dock['bones']['faceplate'][ch]),(mk,ch,'recall continuity')
        # Geometric truth gate: when open the mask lies flat horizontally,
        # original OUTSIDE eyes face up, entire faceplate is ABOVE the roof,
        # and its rear edge does NOT pass behind the 4.5px back of the head.
        pos,ang=mask(1.)
        assert ang==90 and pos[2]>=4.0,(mk,'not slid back')
        samples=geometry_mask_samples(pos,ang)
        assert min(p[1] for p in samples)>33.5,(mk,'mask buried in top helmet plate')
        assert min(p[2] for p in samples)>-4.5 and max(p[2] for p in samples)<4.5,(mk,'not on crown')
        # For the fixed 90-degree positive rotation, NORTH outside face points UP.
        assert -math.sin(math.radians(ang))<-.99,ang # see north normal transform: +Y
        model.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        animation.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        assert [sha(x) for x in pngs]==original_hashes,(mk,'changed armor pixels')
    print(TAG+': MK1--MK24 rear-only hinged plates; stationary full head/roof; true center-pivot 4.15px crown slide; outside up; recall continuity; all PNGs unchanged')
if __name__=='__main__':run()
