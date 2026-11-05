#!/usr/bin/env python3
"""B1181: Import original user-supplied Void_Reaver_HD_Halbe_Dicke.bbmodel mesh/PNG."""
import os,json,base64
from pathlib import Path
P=Path(__file__).resolve().parent/'b1181-assets'
R=Path(os.environ['V1_RESOURCE_ROOT'])/'assets/obsidiannetwork'
pieces=sorted(P.glob('void_model.part*'))
assert len(pieces)==8,('B1181_MISSING_BBMODEL_SEGMENT',len(pieces))
bb=json.loads('\n'.join(p.read_text(encoding='utf-8') for p in pieces))
assert bb['meta']['model_format']=='free'
assert len(bb['elements'])==132 and all(e['type']=='mesh' for e in bb['elements'])
assert bb['resolution']=={'width':128,'height':128}
assert all(e.get('rotation',[0,0,0])==[0,0,0] for e in bb['elements'])
models=R/'models/item';textures=R/'textures/item'
models.mkdir(parents=True,exist_ok=True);textures.mkdir(parents=True,exist_ok=True)
png=base64.b64decode(bb['textures'][0]['source'].split('base64,',1)[1],validate=True)
assert png[:8]==b'\x89PNG\r\n\x1a\n'
assert int.from_bytes(png[16:20],'big')==128 and int.from_bytes(png[20:24],'big')==128
(textures/'void_reaver_hd.png').write_bytes(png)
# B1185: Every triangle/quad in the supplied BBModel has coincident UVs.
# Wavefront OBJ cannot rasterize a zero-area UV face reliably. Keep the
# EXACT 128x128 texture bytes and 3D vertices, but give each face a tiny,
# nondegenerate footprint INSIDE its original solid-color palette swatch.
# Emit explicit outward+inward normals so the thin two-sided axe/pick is
# visible from first person, third person, GUI and on the ground.
import math
from PIL import Image
from io import BytesIO
atlas=Image.open(BytesIO(png)).convert('RGBA')
vertices=[];uvs=[];uvmap={};normals=[];mesh_faces=[];total=0;repaired=0
def uvnum(uv):
 k=tuple(float(x) for x in uv)
 if k not in uvmap:
  uvmap[k]=len(uvs)+1;uvs.append(k)
 return uvmap[k]
def normal(a,b,c):
 p=vertices[a-1];q=vertices[b-1];r=vertices[c-1]
 u=[q[k]-p[k] for k in range(3)]
 v=[r[k]-p[k] for k in range(3)]
 n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
 mag=math.sqrt(sum(c*c for c in n))
 assert mag>1e-9,'B1185_DEGENERATE_ORIGINAL_GEOMETRY'
 return tuple(c/mag for c in n)
for i,e in enumerate(bb['elements']):
 keys={}
 for name,pos in e['vertices'].items():
  keys[name]=len(vertices)+1
  x,y,z=[float(x) for x in pos]
  vertices.append(((x+8)/16,(y-4)/16,z/16))
 group=[]
 for f in e['faces'].values():
  ids=f['vertices'];assert len(ids) in (3,4)
  original_uv=[tuple(f['uv'][k]) for k in ids]
  if len(set(original_uv))==1:
   # These points are centers of colored swatches (x=8,24,..).
   # Moving by 2 texels never leaves the original 16x16 solid tile.
   u,v=original_uv[0]
   assert 2<=u<=125 and 2<=v<=125
   assert atlas.getpixel((int(u),int(v)))[3]==255,('B1185_TRANSPARENT_SWATCH',i,u,v)
   offsets=[(-2,-2),(2,-2),(2,2),(-2,2)]
   mapped_uv=[(u+dx,v+dy) for dx,dy in offsets[:len(ids)]]
   repaired+=1
  else:
   mapped_uv=original_uv
  face=[(keys[k],uvnum(mapped_uv[j])) for j,k in enumerate(ids)]
  outward=normal(face[0][0],face[1][0],face[2][0])
  normals.append(outward);n_out=len(normals)
  normals.append(tuple(-x for x in outward));n_in=len(normals)
  group.append((face,n_out,n_in));total+=1
 mesh_faces.append(group)
assert total==1760 and repaired==1760 and len(vertices)>=6000 and len(uvs)>=42,(total,repaired,len(vertices),len(uvs))
lines=['# User BBModel vertices and ORIGINAL texture unchanged; nondegenerate palette UVs',
       'mtllib void_reaver_hd.mtl','o Void_Reaver_HD_Halbe_Dicke']
lines += [f'v {x:.7f} {y:.7f} {z:.7f}' for x,y,z in vertices]
lines += [f'vt {(u+0.5)/128:.7f} {1-(v+0.5)/128:.7f}' for u,v in uvs]
lines += [f'vn {x:.7f} {y:.7f} {z:.7f}' for x,y,z in normals]
lines += ['usemtl void_reaver_material','s off']
for i,faces in enumerate(mesh_faces):
 lines.append(f'g mesh_{i:03d}')
 for face,n_out,n_in in faces:
  lines.append('f '+' '.join(f'{p}/{uv}/{n_out}' for p,uv in face))
  lines.append('f '+' '.join(f'{p}/{uv}/{n_in}' for p,uv in reversed(face)))
(models/'void_reaver_hd.obj').write_text('\n'.join(lines)+'\n',encoding='utf-8')
(models/'void_reaver_hd.mtl').write_text(
 'newmtl void_reaver_material\nKa 1 1 1\nKd 1 1 1\nKs 0 0 0\nillum 1\nmap_Kd #texture0\n',encoding='utf-8')
# User orientation: blade is at local -X, hook at +X. Y=-90 maps
# -X to -Z (FORWARD, away from player) and +X toward player's camera.
display=bb['display']
display['firstperson_righthand']['rotation']=[0,-90,10]
display['thirdperson_righthand']['rotation']=[0,-90,55]
display['firstperson_lefthand']['rotation']=[0,90,-10]
display['thirdperson_lefthand']['rotation']=[0,90,-55]
item={'loader':'neoforge:obj',
      'model':'obsidiannetwork:models/item/void_reaver_hd.obj',
      'textures':{'texture0':'obsidiannetwork:item/void_reaver_hd',
                  'particle':'obsidiannetwork:item/void_reaver_hd'},
      'automatic_culling':False,'shade_quads':False,'flip_v':False,
      'emissive_ambient':False,'gui_light':'front','display':display}
target=models/'multitool.json'
assert target.exists(),'B1181_PREVIOUS_ITEM_MODEL_MISSING'
target.write_text(json.dumps(item,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('B1185_EXACT_USER_BBMODEL_OPAQUE_NONDEGENERATE_DOUBLE_SIDED_OBJ_PASS',len(vertices),total,repaired,len(png))
