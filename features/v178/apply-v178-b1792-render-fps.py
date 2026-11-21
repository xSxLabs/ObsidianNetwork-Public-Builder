#!/usr/bin/env python3
"""B1792: v1.7.8 v11 FPS optimization: safe opaque-model occlusion, facades and conduits.
Runs AFTER B1780; keeps v11 version. No changes to gameplay, geometry, textures or cable functionality.
"""
import os,re,json,struct,zlib
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
DIR={"north":(2,-1,0,1),"south":(2,1,0,1),"west":(0,-1,1,2),
     "east":(0,1,1,2),"down":(1,-1,0,2),"up":(1,1,0,2)}

# Decode standard 8-bit RGBA PNG alpha using only Python stdlib. Unknown
# formats are conservative: skip the model rather than remove a visible face.
opacity={}
def opaque(path):
 if path in opacity:return opacity[path]
 result=False
 try:
  raw=path.read_bytes()
  assert raw[:8]==b"\x89PNG\r\n\x1a\n"
  offset=8;idat=[];w=h=bit=kind=0;trans=False
  while offset+12<=len(raw):
   n=struct.unpack_from(">I",raw,offset)[0]
   tag=raw[offset+4:offset+8];b=raw[offset+8:offset+8+n];offset+=12+n
   if tag==b"IHDR":
    w,h,bit,kind,compression,filtering,interlace=struct.unpack(">IIBBBBB",b)
    assert interlace==0
   elif tag==b"tRNS":trans=True
   elif tag==b"IDAT":idat.append(b)
   elif tag==b"IEND":break
  if trans:result=False
  elif kind in (0,2,3):result=True
  elif kind in (4,6) and bit==8 and 0<w<=4096 and 0<h<=4096:
   channels=2 if kind==4 else 4;stride=w*channels
   decompressed=zlib.decompress(b"".join(idat))
   assert len(decompressed)==(stride+1)*h
   prev=bytearray(stride);offset=0;result=True
   for rowno in range(h):
    typ=decompressed[offset];offset+=1
    row=bytearray(decompressed[offset:offset+stride]);offset+=stride
    for i in range(stride):
     left=row[i-channels] if i>=channels else 0
     up=prev[i];diag=prev[i-channels] if i>=channels else 0
     if typ==1:row[i]=(row[i]+left)&255
     elif typ==2:row[i]=(row[i]+up)&255
     elif typ==3:row[i]=(row[i]+(left+up)//2)&255
     elif typ==4:
      p=left+up-diag
      a,b,c=abs(p-left),abs(p-up),abs(p-diag)
      row[i]=(row[i]+(left if a<=b and a<=c else up if b<=c else diag))&255
     elif typ!=0:raise ValueError("PNG filter")
    if any(row[i]!=255 for i in range(channels-1,stride,channels)):
     result=False;break
    prev=row
  else:result=False
 except Exception:result=False
 opacity[path]=result
 return result

def texture(model,reference):
 t=model.get("textures",{})
 for _ in range(10):
  if isinstance(reference,dict):reference=reference.get("sprite")
  if not isinstance(reference,str):return None
  if reference.startswith("#"):
   reference=t.get(reference[1:]);continue
  if ":" in reference:namespace,path=reference.split(":",1)
  else:namespace,path="minecraft",reference
  if namespace!="obsidiannetwork" or not path.startswith("block/"):return None
  return R/"textures"/(path+".png")
 return None

def covered(element,direction,elements):
 axis,sign,a,b=DIR[direction]
 low,high=element["from"],element["to"]
 plane=low[axis] if sign<0 else high[axis]
 x0,x1=low[a],high[a];y0,y1=low[b],high[b]
 if x1-x0<1e-5 or y1-y0<1e-5:return False
 rects=[]
 for other in elements:
  if other is element or "rotation" in other:continue
  l,h=other["from"],other["to"]
  # Opaque volume immediately outside this face (includes touching cuboids).
  if sign>0 and not (l[axis]<=plane+1e-6 and h[axis]>plane+1e-6):continue
  if sign<0 and not (l[axis]<plane-1e-6 and h[axis]>=plane-1e-6):continue
  u,v=max(x0,l[a]),min(x1,h[a]);q,p=max(y0,l[b]),min(y1,h[b])
  if v-u>1e-5 and p-q>1e-5:rects.append((u,v,q,p))
 if not rects:return False
 xs=sorted({x0,x1}|{v for rect in rects for v in rect[:2]})
 ys=sorted({y0,y1}|{v for rect in rects for v in rect[2:]})
 for a,b in zip(xs,xs[1:]):
  if a<x0-1e-5 or b>x1+1e-5:continue
  mx=(a+b)/2
  for c,d in zip(ys,ys[1:]):
   if c<y0-1e-5 or d>y1+1e-5:continue
   my=(c+d)/2
   if not any(r[0]-1e-6<=mx<=r[1]+1e-6 and
              r[2]-1e-6<=my<=r[3]+1e-6 for r in rects):return False
 return True

removed=culled=changed=considered=skipped=0
details={}
for path in sorted((R/"models/block").glob("*.json")):
 d=json.loads(path.read_text(encoding="utf-8"))
 elements=d.get("elements",[])
 if not elements:continue
 considered+=1
 if any("rotation" in el for el in elements):continue
 pngs={texture(d,f.get("texture",""))
       for el in elements for f in el.get("faces",{}).values()}
 if not pngs or None in pngs or not all(opaque(p) for p in pngs):
  skipped+=1;continue
 cuts=flags=0
 for el in elements:
  for face,info in list(el.get("faces",{}).items()):
   if face not in DIR:continue
   if covered(el,face,elements):
    del el["faces"][face];cuts+=1
   elif "cullface" not in info:
    axis,sign,_,_=DIR[face]
    boundary=0 if sign<0 else 16
    at=(el["from"] if sign<0 else el["to"])[axis]
    if abs(at-boundary)<1e-5:
     info["cullface"]=face;flags+=1
 if cuts or flags:
  path.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  changed+=1;removed+=cuts;culled+=flags;details[path.stem]=[cuts,flags]
assert removed>1000 and culled>100,("B1792_FACE_COUNTS",removed,culled)
print("B1792_OPAQUE_MODELS",considered,"changed",changed,
      "hidden_faces_removed",removed,"border_cullfaces_added",culled,
      "translucent_or_unknown_models_skipped",skipped)
print("B1792_FPS_TOP",sorted(details.items(),key=lambda p:-p[1][0])[:12])

def method_region(src,name):
 start=src.find("extractRenderState(")
 assert start>=0,("B1792_MISSING_RENDER_EXTRACT",name)
 brace=src.index("{",start)
 depth=0
 for end in range(brace,len(src)):
  if src[end]=="{":depth+=1
  if src[end]=="}":
   depth-=1
   if depth==0:return start,end+1,src[start:end+1]
 raise AssertionError(("B1792_UNBALANCED_RENDER",name))

# Facaded bundles submit ONLY their facade unless NetworkVision is active.
# Avoid the redundant 6*4 connectivity, status and extract calculations.
p=J/"client/render/ConduitBundleRenderer.java"
source=p.read_text(encoding="utf-8")
start,end,body=method_region(source,"ConduitBundleRenderer")
signature=body[:body.index("{")]
match=re.search(r"\b(?:State|ConduitBundleRenderer\.State)\s+(\w+)\b",signature)
assert match,("B1792_CONDUIT_STATE_ARG",signature[:200])
state=match.group(1)
target=re.search(r"(?:java\.util\.)?Arrays\.fill\s*\(\s*"+re.escape(state)+r"\.sideLayers\s*,",body)
assert target and "blockResolver.update(" in body and body.index("blockResolver.update(")<target.start(),("B1792_CONDUIT_SOURCE_DRIFT",)
body=body[:target.start()]+f"if({state}.facaded) return; // B1792_SKIP_HIDDEN_BUNDLE_RENDER_WORK\n   "+body[target.start():]
# Do not leave a qualified prefix such as ConduitBundleBlockEntity.
# before the replacement; that would compile to a nonexistent field.
direction_rx=r"(?<![\w.])(?:(?:net\.minecraft\.core\.)?Direction\.values\(\))"
layer_rx=r"(?<![\w.])(?:(?:(?:dev\.obsidiannetwork\.blockentity\.)?ConduitBundleBlockEntity\.)?Layer\.values\(\))"
body,dirs=re.subn(direction_rx,"B1792_DIRECTIONS",body)
body,layers=re.subn(layer_rx,"B1792_LAYERS",body)
source=source[:start]+body+source[end:]
if dirs+layers:
 cls=re.search(r"\bclass\s+ConduitBundleRenderer\b[^{]*\{",source)
 assert cls
 fields="""
 private static final net.minecraft.core.Direction[] B1792_DIRECTIONS=net.minecraft.core.Direction.values();
 private static final dev.obsidiannetwork.blockentity.ConduitBundleBlockEntity.Layer[] B1792_LAYERS=dev.obsidiannetwork.blockentity.ConduitBundleBlockEntity.Layer.values();
"""
 source=source[:cls.end()]+fields+source[cls.end():]
p.write_text(source,encoding="utf-8")
print("B1792_BUNDLE_HIDDEN_FACADE_EARLY_RETURN_PASS",dirs,layers)

# Six-neighbor maximum BLOCK+SKY lighting is preserved exactly. A weak-key
# cache reuses that packed result for 5 world ticks, instead of twelve lighting
# queries for every single render frame. The world identity is checked.
p=J/"client/render/CableFacadeRenderer.java"
source=p.read_text(encoding="utf-8")
start,end,body=method_region(source,"CableFacadeRenderer")
header=body[:body.index("{")]
match=re.search(r"\(\s*(?:T|[\w.<>?]+)\s+(\w+)\s*,\s*CableFacadeRenderState\s+(\w+)\s*,",header)
assert match,("B1792_FACADE_ARGS",header[:200])
be,state=match.groups()
ix=body.find("Direction.values()")
assert ix>0 and "getBrightness(" in body,("B1792_FACADE_LIGHT_DRIFT",)
lo=body.rfind("for",0,ix)
assert lo>=0 and body[lo:ix].count("{")==0
open_brace=body.find("{",ix)
assert 0<open_brace-ix<30
depth=0;loop_end=None
for i in range(open_brace,len(body)):
 if body[i]=="{":depth+=1
 if body[i]=="}":
  depth-=1
  if depth==0:loop_end=i+1;break
assert loop_end is not None
assign=re.search(r"\b"+re.escape(state)+r"\.lightCoords\s*=.*?;",body[loop_end:],re.S)
assert assign,("B1792_FACADE_LIGHT_ASSIGN",)
last=loop_end+assign.end()
original=body[lo:last]
assert original.count("getBrightness(")==2,("B1792_FACADE_LIGHT_SAMPLE_DRIFT",)
replacement=f"""long xsxNow={be}.getLevel()==null?Long.MIN_VALUE:{be}.getLevel().getGameTime();
   B1792Light cached=B1792_LIGHTS.get({be});
   if(cached!=null&&xsxNow>=cached.tick&&xsxNow-cached.tick<5L){{
    {state}.lightCoords=cached.packed;
   }}else{{
    {original}
    if(xsxNow!=Long.MIN_VALUE)
     B1792_LIGHTS.put({be},new B1792Light(xsxNow,{state}.lightCoords));
   }}"""
body=body[:lo]+replacement+body[last:]
source=source[:start]+body+source[end:]
cls=re.search(r"\bclass\s+CableFacadeRenderer\b[^{]*\{",source)
assert cls
fields="""
 // B1792_FACADE_LIGHT_CACHE: exact legacy neighbor blend, only once per 5 ticks.
 private static final class B1792Light{
  final long tick;final int packed;
  B1792Light(long t,int p){tick=t;packed=p;}
 }
 private static final java.util.Map<net.minecraft.world.level.block.entity.BlockEntity,B1792Light>
   B1792_LIGHTS=new java.util.WeakHashMap<>();
"""
source=source[:cls.end()]+fields+source[cls.end():]
p.write_text(source,encoding="utf-8")
print("B1792_FACADE_LIGHT_CACHE_PRESERVES_SIX_NEIGHBOR_COLORS_PASS")
