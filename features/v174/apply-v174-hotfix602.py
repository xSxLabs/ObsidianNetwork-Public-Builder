#!/usr/bin/env python3
"""v1.7.4 B602: Cable Bundle content-only drops; ENERGY facade refresh;
distinct Ultra Solar Matrix and Ultra Energy Core hand-drawn technical sprites.
Runs only AFTER B598. Fail closed on source/texture API drift.
"""
import os,re,json
from pathlib import Path
from PIL import Image,ImageDraw
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
def write(p,s):p.write_text(s,encoding="utf-8")
def one(s,old,new,why):
 assert s.count(old)==1,("B602_ANCHOR",why,s.count(old),old[:140])
 return s.replace(old,new,1)
# GetDrops is the authoritative *single* pipeline. It already emits one
# underlying cable per installed layer, each actual upgrade and the facade.
# Remove ONLY the erroneous container-block loot, not any of these contents.
p=J/"block/ConduitBundleBlock.java";s=p.read_text(encoding="utf-8")
m=re.search(r"\bgetDrops\s*\([^;]*?\)\s*\{",s,re.S)
assert m,("B602_NO_BUNDLE_GET_DROPS",p)
start=m.end(); depth=1;end=None
for i in range(start,len(s)):
 if s[i]=="{":depth+=1
 elif s[i]=="}":
  depth-=1
  if depth==0:end=i;break
assert end is not None
body=s[start:end]
assert "super.getDrops" in body and "layerStack(" in body and "containedUpgradeDrops" in body and "facadeState()" in body,("B602_DROPS_EXISTING_CONTENTS_CHANGED",body[:1000])
assert body.count("return drops;")==1,("B602_BUNDLE_RETURN_CHANGED",body[-200:])
# Retain vanilla loot-rule evaluation, but strip the useless bundle item.
# Work with a modifiable copy; vanilla getDrops may be immutable.
old_match=re.search(r"(?P<var>\bjava\.util\.List<[^>]+>\s+drops|\bList<[^>]+>\s+drops)\s*=\s*super\.getDrops\s*\(\s*([^;]+?)\s*\)\s*;",body)
assert old_match,("B602_SUPER_DROPS_ASSIGNMENT_CHANGED",body[:500])
old=old_match.group(0)
new=old_match.group("var")+"=new java.util.ArrayList<>(super.getDrops("+old_match.group(2)+"));"
body=body.replace(old,new,1)
body=body.replace("return drops;",'''// B602_CONTENTS_ONLY_DROP: real installed cable layers, saved upgrades
 // and facades survive. Never also return the transient conduit container.
 drops.removeIf(stack -> stack.getItem()==this.asItem());
 return drops;''',1)
s=s[:start]+body+s[end:]
write(p,s)
# Energy-cable facade: installed FACADED blockstate hides the underlying
# baked model, so the client must receive the actual facade state AFTER the
# blockstate replacement. The first BE sync occurs before the block update
# and can be lost by a following state refresh.
p=J/"item/CableFacadeItem.java";s=p.read_text(encoding="utf-8")
# Match the final energy-cable update (not network cables or mixed bundles).
m=re.search(r"(?P<whole>(?P<owner>\w+)\.setBlockAndUpdate\s*\(\s*(?P<pos>\w+)\s*,\s*\(BlockState\)\s*(?P<state>\w+)\.setValue\s*\(\s*EnergyCableBlock\.FACADED\s*,\s*true\s*\)\s*\)\s*;)",s)
if not m:
 m=re.search(r"(?P<whole>(?P<owner>\w+)\.setBlockAndUpdate\s*\(\s*(?P<pos>\w+)\s*,\s*(?P<state>\w+)\.setValue\s*\(\s*EnergyCableBlock\.FACADED\s*,\s*true\s*\)\s*\)\s*;)",s)
assert m,("B602_ENERGY_FACADE_INSTALL_HOOK_MISSING",s[s.find("EnergyCableBlock.FACADED")-350:s.find("EnergyCableBlock.FACADED")+450])
owner,pos=m.group("owner"),m.group("pos")
post='''\n  // B602_ENERGY_FACADE_FINAL_SYNC: refresh AFTER FACADED blockstate mutation.
  // This sends the actual selected texture to the client-side facade BER.
  if({owner}.getBlockEntity({pos}) instanceof dev.obsidiannetwork.blockentity.EnergyCableBlockEntity xsxEnergyFacade){{
   xsxEnergyFacade.setFacadeState(xsxEnergyFacade.facadeState());
   xsxEnergyFacade.requestModelDataUpdate();
   {owner}.sendBlockUpdated({pos},{owner}.getBlockState({pos}),{owner}.getBlockState({pos}),3);
  }}'''.format(owner=owner,pos=pos)
s=s[:m.end()]+post+s[m.end():]
write(p,s)
# Defensive last-frame visual fallback: should facade BE arrive later than the
# FACADED blockstate, don't leave that energy cable entirely invisible.
# Use the real naked cable model for this transient mismatch; once facade NBT
# arrives the existing CableFacadeRenderer renders the actual disguised block.
p=J/"client/render/CableFacadeRenderer.java";s=p.read_text(encoding="utf-8")
assert "CableFacadeRenderState" in s and "blockResolver.update" in s
# No renderer mutation here: block renderer is shared by all facaded cable
# families; the forced post-placement packet above is the narrow safe fix.
# Validate existing class and native BE networking instead.
be=(J/"blockentity/EnergyCableBlockEntity.java").read_text(encoding="utf-8")
assert "getUpdateTag(" in be and "getUpdatePacket(" in be and "facadeState()" in be and "setFacadeState(" in be
client=(J/"client/ClientModEvents.java").read_text(encoding="utf-8")
assert "ModBlockEntities.ENERGY_CABLE.get(), dev.obsidiannetwork.client.render.CableFacadeRenderer::new" in client, "B602_ENERGY_FACADE_RENDERER_MISSING"
# Truly original items: not inherited vanilla Nether Star / Netherite sprites.
# Crisp, readable 32x32 hi-tech sprites; no noisy procedural phototexture.
P=Image
def icon(name):
 im=P.new("RGBA",(32,32),(0,0,0,0))
 d=ImageDraw.Draw(im)
 metal=(27,39,56,255);shadow=(12,20,32,255);edge=(113,131,156,255)
 bright=(97,238,248,255);deep=(19,108,161,255);gold=(248,201,94,255)
 if name=="ultra_energy_core":
  # Octagonal reactor housing with cyan-plasma center, bright perimeter.
  d.polygon([(10,1),(21,1),(30,10),(30,21),(21,30),(10,30),(1,21),(1,10)],fill=shadow,outline=edge)
  d.polygon([(11,4),(20,4),(27,11),(27,20),(20,27),(11,27),(4,20),(4,11)],fill=metal,outline=gold)
  for a in [6,24]:
   d.rectangle((a,13,a+2,18),fill=edge)
  d.rectangle((12,5,19,8),fill=(51,70,93,255))
  d.rectangle((12,23,19,26),fill=(51,70,93,255))
  d.ellipse((8,8,23,23),fill=deep,outline=bright,width=2)
  d.ellipse((11,11,20,20),fill=(20,179,216,255))
  d.ellipse((13,13,18,18),fill=(218,253,255,255))
  for a,b in ((15,3),(15,28),(3,15),(28,15)):
   d.point((a,b),fill=gold)
 else:
  # Framed ultra-dense photovoltaic circuit, 3x3 crisp blue cell array.
  d.rectangle((1,1,30,30),fill=shadow,outline=gold,width=1)
  d.rectangle((3,3,28,28),fill=metal,outline=edge)
  for row in range(3):
   for col in range(3):
    x=5+col*8;y=5+row*8
    d.rectangle((x,y,x+6,y+6),fill=(18,72,103,255),outline=bright,width=1)
    d.line((x+1,y+1,x+5,y+5),fill=(52,149,192,255),width=1)
    d.point((x+3,y+2),fill=(176,247,255,255))
  d.rectangle((0,12,3,19),fill=gold)
  d.rectangle((28,12,31,19),fill=gold)
  d.rectangle((12,0,19,3),fill=gold)
  d.rectangle((12,28,19,31),fill=gold)
 return im
for name in ("ultra_energy_core","ultra_solar_matrix"):
 png=A/"textures/item"/(name+".png")
 assert not png.exists(),("B602_ICON_ALREADY_PRESENT",png)
 png.parent.mkdir(parents=True,exist_ok=True)
 icon(name).save(png,optimize=True)
 model=A/"models/item"/(name+".json")
 doc=json.loads(model.read_text(encoding="utf-8"))
 assert doc.get("parent")=="minecraft:item/generated" and doc["textures"]["layer0"].startswith("minecraft:item/"),("B602_ICON_MODEL_CHANGED",name,doc)
 doc["textures"]["layer0"]="obsidiannetwork:item/"+name
 write(model,json.dumps(doc,indent=2)+"\n")
 with Image.open(png) as v:
  assert v.size==(32,32) and v.mode=="RGBA" and len(set(v.getdata()))>=8,("B602_BAD_SPRITE",name)
 assert json.loads((A/"items"/(name+".json")).read_text(encoding="utf-8"))["model"]["model"]=="obsidiannetwork:item/"+name
assert "B602_CONTENTS_ONLY_DROP" in (J/"block/ConduitBundleBlock.java").read_text(encoding="utf-8")
assert "B602_ENERGY_FACADE_FINAL_SYNC" in (J/"item/CableFacadeItem.java").read_text(encoding="utf-8")
print("B602_BUNDLE_CONTENT_ONLY_ENERGY_FACADE_FINAL_SYNC_ULTRA_CUSTOM_TEXTURES_PASS")
