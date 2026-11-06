#!/usr/bin/env python3
"""B1188: Native Minecraft 3D item directly reconstructed from all 132 user BBModel meshes.
The OBJ loader from B1184/B1186/B1187 was invisible on real clients. Rasterize
EVERY source face at 1/8 Blockbench pixel into a textured true-volume native
Minecraft element (not a 2D sprite). Keep the original PNG byte-for-byte.
"""
import base64,hashlib,json,math,os
from collections import defaultdict
from io import BytesIO
from pathlib import Path
from PIL import Image

PARTS=Path(__file__).resolve().parent/'b1181-assets'
R=Path(os.environ['V1_RESOURCE_ROOT'])/'assets/obsidiannetwork'
MODEL=R/'models/item/multitool.json'
CLIENT=R/'items/multitool.json'
TEXTURE=R/'textures/item/void_reaver_hd.png'
assert MODEL.is_file() and CLIENT.is_file() and TEXTURE.is_file(),'B1188_RESOURCE_ROUTING_MISSING'
sources=sorted(PARTS.glob('void_model.part*'))
assert len(sources)==8,('B1188_ORIGINAL_BBMODEL_PARTS',len(sources))
bb=json.loads('\n'.join(p.read_text(encoding='utf-8') for p in sources))
assert len(bb['elements'])==132 and bb['resolution']=={'width':128,'height':128}
original=base64.b64decode(bb['textures'][0]['source'].split('base64,',1)[1],validate=True)
assert TEXTURE.read_bytes()==original,'B1188_USER_ORIGINAL_TEXTURE_CHANGED'
png=Image.open(BytesIO(original)).convert('RGBA')
assert png.size==(128,128)
S=8
X0=-9.0
Y0=0.0
XMAX=180
YMAX=260
def inside(x,y,poly):
 hit=False
 j=len(poly)-1
 for i in range(len(poly)):
  x1,y1=poly[i];x2,y2=poly[j]
  if ((y1>y)!=(y2>y)) and x<(x2-x1)*(y-y1)/(y2-y1)+x1:hit=not hit
  j=i
 return hit
def palette_uv(u,v):
 return [round(u/8-.1,5),round(v/8-.1,5),round(u/8+.1,5),round(v/8+.1,5)]
elements=[]
mesh_names=[]
colors=set()
for mesh in bb['elements']:
 name=mesh['name']
 vertices=mesh['vertices']
 zs=[float(v[2]) for v in vertices.values()]
 zmin,zmax=min(zs),max(zs)
 assert zmax-zmin>0.001 and -16<=zmin<zmax<=32,(name,zmin,zmax)
 grid={}
 for face in mesh['faces'].values():
  poly=[vertices[k][:2] for k in face['vertices']]
  area=abs(sum(poly[i][0]*poly[(i+1)%len(poly)][1]-poly[(i+1)%len(poly)][0]*poly[i][1] for i in range(len(poly)))/2)
  if area<1e-5:continue
  uv=next(iter(face['uv'].values()))
  u,v=float(uv[0]),float(uv[1])
  ix,iy=round(u),round(v)
  assert 0<=ix<128 and 0<=iy<128 and png.getpixel((ix,iy))[3]==255,('B1188_TRANSPARENT_PALETTE',name,uv)
  color=(u,v)
  minx=max(0,math.floor((min(p[0] for p in poly)-X0)*S-.5))
  maxx=min(XMAX,math.ceil((max(p[0] for p in poly)-X0)*S+.5))
  miny=max(0,math.floor((min(p[1] for p in poly)-Y0)*S-.5))
  maxy=min(YMAX,math.ceil((max(p[1] for p in poly)-Y0)*S+.5))
  for x in range(minx,maxx):
   px=X0+(x+.5)/S
   for y in range(miny,maxy):
    if inside(px,Y0+(y+.5)/S,poly):grid[x,y]=color
 if not grid:
  # Never omit tiny rivets: preserve one true 3D cell per original part.
  points=list(vertices.values())
  cx=sum(p[0] for p in points)/len(points)
  cy=sum(p[1] for p in points)/len(points)
  first=next((f for f in mesh['faces'].values() if f['uv']),None)
  assert first is not None,('B1188_MISSING_FACE',name)
  uv=next(iter(first['uv'].values()))
  grid[(int((cx-X0)*S),int((cy-Y0)*S))]=(float(uv[0]),float(uv[1]))
 mesh_names.append(name)
 colors.update(grid.values())
 rows=defaultdict(list)
 for (x,y),color in grid.items():rows[y].append((x,color))
 active={}
 rects=[]
 for y in range(min(rows),max(rows)+2):
  points=sorted(rows.get(y,[]));runs=[];i=0
  while i<len(points):
   x,color=points[i];end=x+1
   while i+1<len(points) and points[i+1]==(end,color):
    end+=1;i+=1
   runs.append((x,end,color));i+=1
  nxt={}
  for run in runs:nxt[run]=active.pop(run,y)
  for (ax,bx,color),top in active.items():rects.append((ax,top,bx,y,color))
  active=nxt
 for ax,top,bx,bot,color in rects:
  x1=round(X0+ax/S+8,5)
  x2=round(X0+bx/S+8,5)
  y1=round(Y0+top/S,5)
  y2=round(Y0+bot/S,5)
  assert x2-x1>0.001 and y2-y1>0.001 and zmax-zmin>0.001
  uv=palette_uv(*color)
  faces={direction:{'uv':uv,'texture':'#palette'} for direction in ('down','up','north','south','west','east')}
  box={'from':[x1,y1,round(zmin,5)],'to':[x2,y2,round(zmax,5)],'faces':faces}
  assert all(-16<=v<=32 for v in box['from']+box['to'])
  elements.append(box)
assert len(mesh_names)==132 and len(set(mesh_names))==132
assert len(elements)>=2000 and len(colors)>=20,('B1188_ORIGINAL_DETAILS_MISSING',len(elements),len(colors))
old=json.loads(MODEL.read_text(encoding='utf-8'))
assert old['loader']=='neoforge:obj' and old['model']=='obsidiannetwork:models/item/void_reaver_hd.obj'
assert old['display']['firstperson_righthand']['rotation'][1]==-90
native={
 'parent':'minecraft:block/block',
 'ambientocclusion':False,
 'gui_light':'front',
 'textures':{'palette':'obsidiannetwork:item/void_reaver_hd','particle':'obsidiannetwork:item/void_reaver_hd'},
 'display':old['display'],
 'elements':elements
}
MODEL.write_text(json.dumps(native,separators=(',',':'),ensure_ascii=False)+'\n',encoding='utf-8')
item=json.loads(CLIENT.read_text(encoding='utf-8'))
assert item['model']=={'type':'minecraft:model','model':'obsidiannetwork:item/multitool'}
assert TEXTURE.read_bytes()==original
print('B1188_NATIVE_3D_ALL_132_ORIGINAL_MESHES_ORIGINAL_PNG_PASS',len(elements),len(colors),hashlib.sha256(original).hexdigest())
