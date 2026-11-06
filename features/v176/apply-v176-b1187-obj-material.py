#!/usr/bin/env python3
"""B1187: Make the exact user Void Reaver OBJ readable in NeoForge.

The old exporter emitted 132 g groups but only ONE usemtl directive
before those groups. Some OBJ loaders reset the material on entering
a group, creating untextured/invisible geometry. Explicitly bind the
existing original PNG material for EACH group, triangulate quads and
verify the Minecraft client item -> model reference. Do not modify
geometry positions, UV coordinates, the MTL's texture target or PNG bytes.
"""
import json,os,hashlib
from pathlib import Path
root=Path(os.environ['V1_RESOURCE_ROOT'])/'assets/obsidiannetwork'
p=root/'models/item/void_reaver_hd.obj'
m=root/'models/item/multitool.json'
mtl=root/'models/item/void_reaver_hd.mtl'
item=root/'items/multitool.json'
tex=root/'textures/item/void_reaver_hd.png'
assert all(x.is_file() for x in (p,m,mtl,item,tex)),('B1187_RESOURCE_MISSING')
texture_hash=hashlib.sha256(tex.read_bytes()).hexdigest()
assert len(tex.read_bytes())==449,'B1187_ORIGINAL_TEXTURE_BYTES_DRIFT'
assert 'map_Kd #texture0' in mtl.read_text(encoding='utf-8')
obj=p.read_text(encoding='utf-8').splitlines()
group_count=sum(x.startswith('g mesh_') for x in obj)
original_faces=[x for x in obj if x.startswith('f ')]
quads=sum(len(x.split())==5 for x in original_faces)
assert group_count==132 and len(original_faces)==3520 and quads==1528,('B1187_SOURCE_MESH_DRIFT',group_count,len(original_faces),quads)
out=[]
for line in obj:
 if line.startswith('g mesh_'):
  out.append(line)
  out.append('usemtl void_reaver_material')  # explicit per-group binding
 elif line.startswith('f '):
  corners=line.split()[1:]
  assert len(corners) in (3,4)
  if len(corners)==4:
   out.append('f '+' '.join(corners[i] for i in (0,1,2)))
   out.append('f '+' '.join(corners[i] for i in (0,2,3)))
  else:
   out.append(line)
 else:
  out.append(line)
assert sum(x.startswith('f ') for x in out)==5048,'B1187_TRIANGULATION'
assert all(len(x.split())==4 for x in out if x.startswith('f '))
assert sum(x.startswith('usemtl void_reaver_material') for x in out)==133,'B1187_GROUP_MATERIAL'
assert sum(x.startswith('v ') for x in out)==6044,'B1187_VERTICES_UNCHANGED'
assert sum(x.startswith('vn ') for x in out)==3520,'B1187_NORMALS_UNCHANGED'
p.write_text('\n'.join(out)+'\n',encoding='utf-8')
j=json.loads(m.read_text(encoding='utf-8'))
assert j['loader']=='neoforge:obj'
assert j['model']=='obsidiannetwork:models/item/void_reaver_hd.obj'
assert j['textures']['texture0']=='obsidiannetwork:item/void_reaver_hd'
assert j['display']['firstperson_righthand']['rotation'][1]==-90
j['mtl_override']='obsidiannetwork:models/item/void_reaver_hd.mtl'
m.write_text(json.dumps(j,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
client=json.loads(item.read_text(encoding='utf-8'))
assert client['model']=={'type':'minecraft:model','model':'obsidiannetwork:item/multitool'},'B1187_ITEM_ROUTING'
assert hashlib.sha256(tex.read_bytes()).hexdigest()==texture_hash,'B1187_PNG_WAS_CHANGED'
print('B1187_ORIGINAL_TEXTURE_HASH_UNCHANGED_OBJ_PER_GROUP_MATERIAL_ALL_TRIANGLES_PASS',group_count,quads,5048,texture_hash)
