#!/usr/bin/env python3
"""B1176: user screenshot corrections. Worn gun lower, single backpack count,
and a front-facing black/purple forged 3D multitool. No gameplay changes."""
import json, os
from pathlib import Path
from PIL import Image

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"

# 1) Worn third-person ONLY: correction is after the actual right-arm pivot.
# +Z lowers the elevated B1175 barrel in the model's inverted-Y player frame.
gun=J/"client/V176MicroMgVisualClient.java"
s=gun.read_text(encoding="utf-8")
old="if(worn)pose.translate(0.0F,-0.015F,-0.09F);"
new="if(worn)pose.translate(0.0F,-0.012F,0.020F); // B1176_WORN_ONLY_LOWER"
assert s.count(old)==1,("B1176_WORN_LOCAL_MOUNT_DRIFT",s.count(old))
assert "drawArm(pose,nodes,light,parent,tier,extension,false);" in s
assert "V176ThirdPersonArmSnapshot.apply(" in s
s=s.replace(old,new,1)
gun.write_text(s,encoding="utf-8")

# 2) Backpack: only ONE amount label, right-aligned and 58% or smaller.
screen=J/"client/V176BackpackScreen.java"
s=screen.read_text(encoding="utf-8")
assert s.count('super.renderSlotContents(g,stack,slot,"");')==1
# Preview icons always render at count 1, not the actual virtual total.
s=s.replace('super.renderSlotContents(g,stack,slot,"");',
            'super.renderSlotContents(g,stack.copyWithCount(1),slot,""); // B1176_NO_VANILLA_COUNT',1)
old="""    g.pose().translate(slot.x+16.0F-font.width(label)*0.78F,slot.y+10.0F);
    g.pose().scale(0.78F,0.78F);"""
new="""    // A single small count fits even when abbreviated amounts are long.
    float xsxCountScale=Math.min(0.58F,15.5F/Math.max(1,font.width(label)));
    g.pose().translate(slot.x+16.0F-font.width(label)*xsxCountScale,
        slot.y+17.0F-9.0F*xsxCountScale);
    g.pose().scale(xsxCountScale,xsxCountScale);"""
assert s.count(old)==1,("B1176_CUSTOM_COUNT_LABEL_DRIFT",s.count(old))
s=s.replace(old,new,1)
# B816 inserted an earlier identical count label in extractLabels. The old
# B891 removal was not fail-closed and could leave this duplicate behind.
anchor=" @Override protected void extractLabels("
assert s.count(anchor)==1,("B1176_LABEL_METHOD_NOT_FOUND",s.count(anchor))
a=s.index(anchor)
b=s.find(" @Override",a+len(anchor))
if b<0:b=len(s)
labels=s[a:b]
target="for(int index=0;index<45;index++){"
if target in labels:
 p=labels.index(target); opening=labels.index("{",p); depth=0; end=None
 for k in range(opening,len(labels)):
  if labels[k]=="{":depth+=1
  elif labels[k]=="}":
   depth-=1
   if depth==0:
    end=k+1;break
 assert end is not None
 legacy=labels[p:end]
 assert "xsx_v176_preview_total" in legacy,("B1176_UNEXPECTED_LIST_LOOP",legacy[:160])
 labels=labels[:p]+"// B1176: old duplicate count loop removed.\n  "+labels[end:]
 s=s[:a]+labels+s[b:]
assert s.count('g.text(font,label,0,0,0xffeffaff);')==1,("B1176_NOT_SINGLE_STORED_LABEL",s.count('g.text(font,label,0,0,0xffeffaff);'))
# Any residual original count line is a hard failure, not an ignored warning.
assert 'g.text(font,label,8+(index%9)' not in s
screen.write_text(s,encoding="utf-8")

# 3) New Minecraft JSON geometry. In B1175 the broad axe was shown largely
# edge-on by the -90 degree Y hand transform. This tool shows its actual face.
# Sculpt two separate silhouettes around a thick central mechanical core:
# the left CRESCENT AXE and the opposite long, curved PICK/HOOK.
model=A/"models/item/multitool.json"
png=A/"textures/item/multitool_3d.png"
assert model.is_file() and png.is_file()
base=json.loads(model.read_text(encoding="utf-8"))
assert "elements" in base and len(base["elements"])>=45
# 16 16x16 metallic swatches: dark Netherite, smoked-steel bevels, violet
# inlays and pink-purple cutting edges. No washed-out grey main body.
palette=[
 (10,9,16),(22,20,30),(34,30,44),(50,44,63),
 (65,54,77),(87,73,102),(111,96,126),(152,130,166),
 (36,13,59),(76,19,119),(157,30,221),(221,70,255),
 (23,16,37),(48,28,76),(116,44,172),(247,156,255)
]
im=Image.new("RGBA",(64,64),(0,0,0,255))
for tile,rgb in enumerate(palette):
 tx=(tile%4)*16;ty=(tile//4)*16
 for yy in range(16):
  for xx in range(16):
   noise=((xx*3+yy*7+tile*11)%7)-3
   bevel=(7 if xx<=1 or yy<=1 else (-9 if xx>=14 or yy>=14 else 0))
   im.putpixel((tx+xx,ty+yy),
      tuple(max(0,min(255,k+noise+bevel)) for k in rgb)+(255,))
im.save(png)
parts=[]
def cub(lo,hi,t,bevel=None):
 assert len(lo)==len(hi)==3
 assert all(0<=x<y<=16 for x,y in zip(lo,hi)),(lo,hi)
 def uv(i):
  u=(i%4)*4;v=(i//4)*4
  return [u,v,u+4,v+4]
 faces={}
 for face in ("north","south","east","west","up","down"):
  idx=(bevel if bevel is not None and face in ("up","east") else t)
  faces[face]={"uv":uv(idx),"texture":"#metal"}
 parts.append({"from":lo,"to":hi,"faces":faces})
def plate(x1,y1,x2,y2,t,depth=.22):
 # two decorative face plates on BOTH broad faces, not a single side only
 cub([x1,y1,5.25-depth],[x2,y2,5.25],t)
 cub([x1,y1,10.75],[x2,y2,10.75+depth],t)
# Dark slender grip with visible continuous purple neon channel.
cub([7.05,.28,6.95],[8.95,11.30,9.05],1,3)
cub([7.34,.30,6.62],[8.65,10.80,6.96],2,4)
cub([7.34,.30,9.04],[8.65,10.80,9.38],0,2)
cub([6.68,.35,7.28],[7.07,10.85,8.72],0,2)
cub([8.94,.35,7.28],[9.32,10.85,8.72],2,4)
plate(7.70,1.00,8.25,9.20,10,.24)
for yy in (1.05,3.45,5.85,8.25,10.05):
 cub([6.70,yy,6.65],[9.3,yy+.32,9.35],2,4)
 plate(7.2,yy+.08,8.75,yy+.24,9,.26)
cub([6.62,.05,6.46],[9.38,.88,9.54],1,5)
plate(7.35,.15,8.65,.65,11)
# The weighted black head MUST be visibly wider than the shaft.
cub([5.35,10.45,5.70],[10.85,13.9,10.30],1,4)
cub([5.85,11.2,5.48],[10.25,13.65,5.73],2,5)
cub([5.85,11.2,10.27],[10.25,13.65,10.52],0,3)
cub([6.55,13.65,6.2],[9.45,14.40,9.8],2,4)
# Central dark gem housing with violet ring: frontal and rear.
for z1,z2 in ((5.05,5.28),(10.72,10.95)):
 cub([7.05,11.65,z1],[8.95,13.42,z2],8,10)
 cub([7.35,11.91,z1-.05],[8.65,13.20,z2-.03],0,13)
 cub([7.70,12.16,z1-.08],[8.30,12.97,z2-.06],11,15)
# Axe body on LEFT: massive upper and lower wings with an OPEN concave
# recess between them, not a rectangular flat hammer.
cub([3.90,12.15,5.8],[5.50,15.30,10.2],1,4)
cub([2.95,13.40,6.0],[4.07,15.70,10.0],2,5)
cub([1.92,14.24,6.25],[3.11,15.86,9.75],2,5)
cub([1.05,14.8,6.60],[2.05,15.98,9.40],3,6)
cub([.28,15.27,7.00],[1.22,15.99,9.0],4,7)
cub([3.5,9.82,5.85],[5.55,12.4,10.15],1,4)
cub([2.55,8.93,6.1],[3.80,11.15,9.90],2,5)
cub([1.65,8.20,6.37],[2.78,9.94,9.63],3,5)
cub([.80,7.62,6.70],[1.86,8.89,9.30],4,6)
cub([.20,7.30,7.20],[.94,8.0,8.80],5,7)
# Sharply chamfered violet crest on the two crescent tips, shallow
# panel insets instead of uniformly bright magenta body.
for yy,x1,x2 in ((15.52,.15,1.2),(15.0,1.03,2.10),
                 (14.46,1.94,2.96),(8.45,.42,1.6),(9.05,1.35,2.5)):
 plate(x1,yy,x2,yy+.18,11,.30)
for a,b,c,d in ((2.6,13.25,3.4,13.56),(3.4,12.55,4.9,12.89),
                 (2.3,10.15,3.2,10.47),(3.5,11.08,5.08,11.38)):
 plate(a,b,c,d,10,.27)
# Angular forged surface plates layered ABOVE the shadow undercut.
for x1,y1,x2,y2 in ((3.4,13.82,4.55,14.3),
                     (4.40,11.92,5.13,12.55),
                     (3.05,9.40,3.76,10.10)):
 plate(x1,y1,x2,y2,2,.16)
# Pick on RIGHT: long upper span then descending, narrowing hooked point.
cub([10.42,12.25,5.90],[12.0,14.6,10.1],1,4)
cub([11.85,13.40,6.04],[13.3,15.10,9.96],2,5)
cub([13.12,13.82,6.29],[14.42,15.16,9.71],2,5)
cub([14.28,13.5,6.66],[15.13,14.7,9.34],3,6)
cub([14.94,12.6,7.0],[15.55,13.84,9.0],2,5)
cub([15.13,11.56,7.32],[15.78,12.8,8.68],3,6)
cub([15.40,10.55,7.65],[15.95,11.7,8.35],4,6)
cub([15.65,9.70,7.8],[15.99,10.7,8.20],5,7)
# Electric purple edge wraps the curved upper spine.
for x1,y1,x2,y2 in ((10.8,14.30,12.0,14.55),
                     (12.0,14.78,13.35,15.00),
                     (13.33,14.82,14.38,15.06),
                     (14.48,14.13,15.10,14.36),
                     (15.15,12.5,15.5,13.40),
                     (15.37,11.24,15.7,12.20)):
 plate(x1,y1,x2,y2,10,.27)
plate(15.65,9.72,15.9,10.45,11,.32)
# Decorative near-black top armor and light-purple horizontal cuts.
plate(5.70,12.28,7.2,12.56,9,.20)
plate(8.7,12.28,10.05,12.56,9,.20)
plate(9.2,10.62,10.25,10.84,14,.23)
# Final legal block-model UV (0..16) and hand poses showing broad faces.
base["elements"]=parts
base["textures"]={"metal":"obsidiannetwork:item/multitool_3d",
                  "particle":"obsidiannetwork:item/multitool_3d"}
base["gui_light"]="front"
base["display"]={
 "gui":{"rotation":[16,12,12],"translation":[0,0,0],
        "scale":[.88,.88,.88]},
 "firstperson_righthand":{"rotation":[0,-15,40],"translation":[0,1.2,0],
        "scale":[.63,.63,.63]},
 "firstperson_lefthand":{"rotation":[0,15,-40],"translation":[0,1.2,0],
        "scale":[.63,.63,.63]},
 "thirdperson_righthand":{"rotation":[0,-20,45],"translation":[0,2,0],
        "scale":[.74,.74,.74]},
 "thirdperson_lefthand":{"rotation":[0,20,-45],"translation":[0,2,0],
        "scale":[.74,.74,.74]},
 "ground":{"translation":[0,2,0],"scale":[.55,.55,.55]},
 "fixed":{"rotation":[0,180,0],"scale":[.85,.85,.85]}}
assert len(parts)>=70,("B1176_GEOMETRY_TOO_SIMPLE",len(parts))
assert all(0<=v<=16 for e in parts for f in e["faces"].values() for v in f["uv"])
model.write_text(json.dumps(base,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("B1176_WORN_GUN_LOWER_SINGLE_BACKPACK_LABEL_58PCT_FORGED_TOOL_3D_PASS",len(parts))
