#!/usr/bin/env python3
"""B659 fail-closed collision-only recipe repair after EVERY recipe generator.
Only conflicting inputs with different outputs may change. Others remain bytes.
"""
import argparse,collections,copy,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument("resources",type=Path);p.add_argument("--apply",action="store_true")
a=p.parse_args()
root=a.resources
paths=sorted({*root.glob("data/*/recipe/**/*.json"),*root.glob("data/*/recipes/**/*.json")})
assert paths,"No recipe JSONs; refusing a false green build."
docs={p:json.loads(p.read_text(encoding="utf8")) for p in paths}
before={p:p.read_bytes() for p in paths}
changed=set()
def material(stem):
 return {
 "reactor_glass":["minecraft:tinted_glass","minecraft:amethyst_shard"],
 "reactor_fuel_assembly":["minecraft:blaze_rod","minecraft:netherite_ingot"],
 "reactor_controller":["minecraft:comparator","minecraft:observer"],
 "reactor_item_port":["minecraft:hopper","minecraft:chest"],
 "reactor_fluid_port":["minecraft:bucket","minecraft:prismarine_shard"],
 "reactor_power_port":["minecraft:copper_block","minecraft:redstone_block"],
 "powerbank_glass":["minecraft:light_blue_stained_glass","minecraft:amethyst_shard"],
 "powerbank_input_port":["minecraft:redstone_block","minecraft:hopper"],
 "powerbank_output_port":["minecraft:copper_block","minecraft:dropper"],
 "network_printer":["minecraft:observer","minecraft:piston"],
 "network_hologram_terminal":["minecraft:ender_eye","minecraft:amethyst_shard"],
 }.get(stem,[])+["minecraft:comparator","minecraft:observer","minecraft:amethyst_shard","minecraft:copper_block","minecraft:echo_shard","minecraft:prismarine_crystals","minecraft:repeater","minecraft:ender_eye","minecraft:diamond_block","minecraft:netherite_scrap","minecraft:hopper","minecraft:blue_ice","minecraft:sea_lantern"]
def result(doc):
 r=doc.get("result",None)
 return r.get("id",r.get("item")) if isinstance(r,dict) else r
def opts(v,depth=0):
 if depth>7:return set()
 if isinstance(v,str):
  if not v.startswith("#"):return {v}
  tag=v[1:];ns,_,sub=tag.partition(":")
  f=root/"data"/ns/"tags/item"/(sub+".json")
  if not f.exists():return {v}
  data=json.loads(f.read_text(encoding="utf8"))
  return set().union(*(opts(x,depth+1) for x in data.get("values",[])))
 if isinstance(v,dict):
  if "tag" in v:return opts("#"+v["tag"],depth+1)
  if "item" in v:return opts(v["item"],depth+1)
  if "items" in v:return set().union(*(opts(x,depth+1) for x in v["items"]))
  if "id" in v:return opts(v["id"],depth+1)
  return set()
 if isinstance(v,list):return set().union(*(opts(x,depth+1) for x in v))
 return set()
def grid(doc):
 rows=doc.get("pattern",[])
 if not isinstance(rows,list) or not rows:return None
 rows=list(rows)
 while rows and not rows[0].strip():rows.pop(0)
 while rows and not rows[-1].strip():rows.pop()
 if not rows:return None
 cols=[i for i in range(max(map(len,rows))) if any(i<len(row) and row[i]!=" " for row in rows)]
 if not cols:return None
 rows=[ "".join(row[i] if i<len(row) else " " for i in range(min(cols),max(cols)+1)) for row in rows]
 k=doc.get("key",{})
 return tuple(tuple(None if c==" " else opts(k.get(c,[])) for c in row) for row in rows)
def pack(doc):
 t=doc.get("type")
 if t=="minecraft:crafting_shaped":
  g=grid(doc);return ("shaped",g) if g else None
 if t=="minecraft:crafting_shapeless":
  return ("shapeless",tuple(opts(x) for x in doc.get("ingredients",[])))
 if t in ("minecraft:smelting","minecraft:blasting","minecraft:smoking","minecraft:campfire_cooking","minecraft:stonecutting"):
  return (t,(opts(doc.get("ingredient",[])),))
 return None
def matchsets(x,y):return bool(x and y and x.intersection(y))
def multiset(a,b):
 if len(a)!=len(b):return False
 used=[False]*len(b)
 def go(i):
  if i==len(a):return True
  for j in range(len(b)):
   if not used[j] and matchsets(a[i],b[j]):
    used[j]=True
    if go(i+1):return True
    used[j]=False
  return False
 return go(0)
def overlap(x,y):
 if not x or not y:return False
 tx,vx=x;ty,vy=y
 if tx=="shaped" and ty=="shaped":
  if len(vx)!=len(vy) or len(vx[0])!=len(vy[0]):return False
  return any(all((q is None and p is None) or (p is not None and q is not None and matchsets(p,q)) for r,s in zip(vx,vg) for p,q in zip(r,s)) for vg in (vy,tuple(tuple(reversed(r)) for r in vy)))
 if tx in ("shaped","shapeless") and ty in ("shaped","shapeless"):
  xx=tuple(v for row in vx for v in row if v is not None) if tx=="shaped" else vx
  yy=tuple(v for row in vy for v in row if v is not None) if ty=="shaped" else vy
  return multiset(xx,yy)
 return tx==ty and len(vx)==len(vy) and all(matchsets(p,q) for p,q in zip(vx,vy))
def collisions():
 indexed=[(p,pack(d)) for p,d in docs.items()]
 found=[]
 for i,(p,x) in enumerate(indexed):
  if not x:continue
  for q,y in indexed[i+1:]:
   if y and result(docs[p])!=result(docs[q]) and overlap(x,y):found.append((p,q))
 return found
def variants(d,stem):
 typ=d.get("type");out=[]
 if typ=="minecraft:crafting_shaped":
  rows=d.get("pattern",[]);keys=d.get("key",{})
  counts=collections.Counter("".join(rows))
  chars=[c for c in keys if counts[c]>0]
  # Prefer the middle, single-occurrence discriminator to preserve costs.
  chars.sort(key=lambda c:(counts[c]!=1, c!=rows[len(rows)//2][len(rows[len(rows)//2])//2],c))
  for c in chars:
   if isinstance(keys[c],str):
    for m in material(stem):
     if m==keys[c]:continue
     t=copy.deepcopy(d);t["key"][c]=m;out.append(t)
 if typ=="minecraft:crafting_shapeless":
  for i,x in enumerate(d.get("ingredients",[])):
   if isinstance(x,str):
    for m in material(stem):
     if m==x:continue
     t=copy.deepcopy(d);t["ingredients"][i]=m;out.append(t)
 return out
original=collisions()
print("B659_RECIPE_SCAN initial="+str(len(paths))+" conflicting_pairs="+str(len(original)))
if original and not a.apply:
 for x,y in original[:40]:print("COLLISION",x.relative_to(root),y.relative_to(root))
 raise SystemExit("B659 unresolved recipe collisions")
if a.apply:
 for attempt in range(len(paths)*3):
  found=collisions()
  if not found:break
  left,right=found[0];victim=right
  old=docs[victim];found_fix=False
  for candidate in variants(old,victim.stem):
   docs[victim]=candidate
   if not any(victim in pair for pair in collisions()):
    changed.add(victim);found_fix=True;break
  if not found_fix:
   docs[victim]=old
   raise SystemExit("B659 no safe automatic repair for "+str(left)+" vs "+str(right))
 else:raise SystemExit("B659 collision repair exceeded iteration bound")
 assert not collisions(),"B659 unrepaired collisions"
 for path in changed:
  assert result(docs[path])==result(json.loads(before[path])),path
  path.write_text(json.dumps(docs[path],ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
for path in paths:
 if path not in changed:assert path.read_bytes()==before[path],("B659 unique recipe modified",path)
print("B659_RECIPES_COLLISION_FREE PASS checked="+str(len(paths))+" changed="+str(len(changed)))
for path in sorted(changed):print("B659_RECIPE_REPAIRED",path.relative_to(root),result(docs[path]))
