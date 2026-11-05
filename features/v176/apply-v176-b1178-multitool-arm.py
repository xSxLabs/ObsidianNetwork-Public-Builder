#!/usr/bin/env python3
"""B1178: screenshot-based render fixes.

1. When attack mode owns the first-person weapon arm, cancel the legacy
   vanilla RIGHT-arm draw; leave off-mode and other arms unaffected.
2. Worn third-person barrel stays on actual rightArm's pivot (not a world
   element). Seat it slightly lower; leave turret and 1P barrel unchanged.
3. Replace the item cuboid soup with ONE coherent forged axe/pick silhouette,
   dark metallic shading and embedded violet trim, in all item display poses.
No changes to recipes, FE, attack logic, inventory, suits or network code.
"""
import json, os
from pathlib import Path
from PIL import Image, ImageDraw

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"

# The actual user screenshot shows an extra vanilla arm next to the custom
# 1P forearm. B973 intentionally no-opped RenderArmEvent. That is incorrect
# when Minecraft also calls the arm event with an empty main-hand.
gun=J/"client/V176MicroMgVisualClient.java"
s=gun.read_text(encoding="utf-8")
old=""" @SubscribeEvent public static void xsxlabs$aimVisibleFirstPersonArm(RenderArmEvent event){
  // Legacy hook intentionally disabled: B973 submits upper arm, hinged
  // forearm and gun in one RenderHandEvent pass for empty or held hands.
  // Do not cancel or touch the vanilla pose here (also used in UI previews).
 }"""
new=""" @SubscribeEvent public static void xsxlabs$aimVisibleFirstPersonArm(RenderArmEvent event){
  // B1178: firstPerson(RenderHandEvent) owns the right arm AND its barrel
  // while Attack Mode is on. The separate vanilla arm must NOT draw too.
  // Never cancel the left arm, or either arm when Attack Mode is OFF.
  if(event.getArm()!=net.minecraft.world.entity.HumanoidArm.RIGHT)return;
  var player=event.getPlayer();
  if(player==null
      ||player.getMainArm()!=net.minecraft.world.entity.HumanoidArm.RIGHT)return;
  int armorTier=tier(player);
  if(armorTier<1||armorTier>24||!armedForAttack(player))return;
  event.setCanceled(true); // B1178_CANCEL_ONLY_REDUNDANT_VANILLA_RIGHT_ARM
 }"""
assert s.count(old)==1,("B1178_ARM_HANDLER_DRIFT",s.count(old))
s=s.replace(old,new,1)
# Single player-specific correction after *real* pivot; turret uses false
# overload and never executes this. The prior tiny +0.020 did not seat it.
oldoffset="if(worn)pose.translate(0.0F,-0.012F,0.020F); // B1176_WORN_ONLY_LOWER"
newoffset="if(worn)pose.translate(0.0F,-0.012F,0.052F); // B1178_WORN_ONLY_FOREARM"
assert s.count(oldoffset)==1,("B1178_WORN_OFFSET_DRIFT",s.count(oldoffset))
assert "V176ThirdPersonArmSnapshot.apply(" in s
assert "drawArm(pose,nodes,light,parent,tier,extension,false);" in s
s=s.replace(oldoffset,newoffset,1)
gun.write_text(s,encoding="utf-8")

# Compact, connected and asymmetrical Netherite axe/pick. The photographed
# reference is a broad C-shaped axe on the LEFT and a slender curved
# pick/claw on the RIGHT, with an inset illuminated hexagonal hub.
model=R/"models/item/multitool.json"
atlas=R/"textures/item/multitool_3d.png"
assert model.exists() and atlas.exists(),"B1178_RESOURCE_NOT_GENERATED"
data=json.loads(model.read_text(encoding="utf-8"))
assert len(data["elements"])>70,"B1178_EXPECT_B1176_BASE"
pal=[
 (12,11,18), (23,21,31), (34,31,45), (47,41,59),
 (61,53,73), (79,68,93), (112,97,128), (150,130,165),
 (47,16,71), (93,26,134), (173,41,228), (236,94,255),
 (26,19,40), (52,30,83), (126,55,188), (248,180,255)
]
img=Image.new("RGBA",(64,64),(0,0,0,255))
draw=ImageDraw.Draw(img)
for tile,rgb in enumerate(pal):
 x=(tile%4)*16;y=(tile//4)*16
 for dy in range(16):
  for dx in range(16):
   grain=((dx*7+dy*5+tile*3)%7)-3
   bevel=7 if dx==0 or dy==0 else (-9 if dx==15 or dy==15 else 0)
   img.putpixel((x+dx,y+dy),
       tuple(max(0,min(255,c+grain+bevel)) for c in rgb)+(255,))
# Swatch 15: a readable purple illuminated hexagonal ring, not a cube icon.
hx=(15%4)*16;hy=(15//4)*16
draw.rectangle((hx,hy,hx+15,hy+15),fill=(20,15,29,255))
outer=[(hx+8,hy+1),(hx+13,hy+4),(hx+13,hy+11),
       (hx+8,hy+14),(hx+3,hy+11),(hx+3,hy+4)]
inner=[(hx+8,hy+4),(hx+10,hy+5),(hx+10,hy+10),
       (hx+8,hy+11),(hx+6,hy+10),(hx+6,hy+5)]
draw.polygon(outer,fill=(226,96,255,255))
draw.polygon(inner,fill=(38,16,58,255))
draw.line(outer+[outer[0]],fill=(255,186,255,255),width=1)
img.save(atlas)

parts=[]
def cub(x1,y1,z1,x2,y2,z2,t,trim=None):
 assert 0<=x1<x2<=16 and 0<=y1<y2<=16 and 0<=z1<z2<=16,("B1178_BAD_BOX",(x1,y1,z1,x2,y2,z2))
 def uv(n):
  u=(n%4)*4;v=(n//4)*4
  return [u,v,u+4,v+4]
 faces={}
 for face in ("north","south","east","west","up","down"):
  material=trim if trim is not None and face in ("east","up") else t
  faces[face]={"texture":"#metal","uv":uv(material)}
 parts.append({"from":[x1,y1,z1],"to":[x2,y2,z2],"faces":faces})

# Straight, slightly tapered long handle; all neon is flush/inset, no
# isolated free-floating plates. Blade-to-handle axis remains local +Y.
cub(7.10,.25,6.60,8.90,11.35,9.40,1,3)
cub(7.35,.3,6.36,8.65,10.8,6.64,2,4)
cub(7.35,.3,9.37,8.65,10.8,9.65,2,4)
cub(6.80,.35,7.05,7.14,10.75,8.95,0,2)
cub(8.86,.35,7.05,9.20,10.75,8.95,0,3)
# Continuous purple vein INSIDE the front grip housing.
cub(7.77,1.05,6.20,8.23,9.32,6.38,10,11)
cub(7.77,1.05,9.62,8.23,9.32,9.80,10,11)
for y in (1.0,3.65,6.30,8.95):
 cub(6.85,y,6.40,9.15,y+.38,9.60,2,4)
 cub(7.48,y+.05,6.19,8.52,y+.30,6.40,9,11)
cub(6.75,0,6.4,9.25,.82,9.6,2,5)
cub(7.45,.05,6.17,8.55,.56,6.40,10,11)

# Central dark housing is ONE connected mass and tapers into the grip.
cub(5.35,10.65,5.65,10.85,14.2,10.35,1,4)
cub(6.2,10.02,6.10,9.8,11.5,9.9,0,3)
cub(6.15,13.85,6.05,9.95,14.55,9.95,2,5)
cub(5.75,11.10,5.37,10.45,13.65,5.66,2,5)
cub(5.75,11.10,10.34,10.45,13.65,10.63,2,5)

# Heavy AXE blade on LEFT. A curved crescent silhouette is described by
# overlapping/connected row spans. Thin bright rim is IN CONTACT with the
# dark body and extends to its OUTER edge; no separate floating UV strips.
axe=[
 (7.75,8.25,.45,2.25),
 (8.25,8.75,.50,3.05),
 (8.75,9.25,.65,3.65),
 (9.25,9.75,.83,4.12),
 (9.75,10.25,1.15,4.68),
 (10.25,10.75,1.50,5.12),
 (10.75,11.25,1.80,5.65),
 (11.25,11.75,1.98,5.8),
 (11.75,12.25,1.78,5.85),
 (12.25,12.75,1.30,5.92),
 (12.75,13.25,.92,5.95),
 (13.25,13.75,.62,6.05),
 (13.75,14.25,.37,6.0),
 (14.25,14.75,.25,5.85),
 (14.75,15.25,.33,5.45),
 (15.25,15.75,.65,4.6),
 (15.75,15.98,1.10,3.25)]
for i,(ya,yb,left,right) in enumerate(axe):
 # Two-depth layered forging; the dark base is continuous with head.
 cub(left+.27,ya,5.93,right+.11,yb,10.07,2 if i%3 else 3,5)
 # A single bold electric-purple cutting edge, continuous across rows.
 cub(left,ya,5.80,left+.32,yb,10.20,10 if 2<i<15 else 11,15)
 # Dark front/rear beveled facets connect to the metal body.
 if 2<=i<=14 and i%2==0:
  cub(left+.32,ya+.08,5.74,min(right,left+1.55),yb-.06,5.94,3,5)
  cub(left+.32,ya+.08,10.06,min(right,left+1.55),yb-.06,10.26,3,5)
# Recessed glowing slots are anchored INSIDE the broad blade, not detached.
for xa,ya,xb,yb in ((2.4,9.15,3.3,9.41),(3.25,9.85,4.48,10.13),
                    (2.30,13.86,3.20,14.13),(3.23,13.02,4.90,13.31)):
 cub(xa,ya,5.69,xb,yb,5.94,10,11)
 cub(xa,ya,10.06,xb,yb,10.31,10,11)

# Right PICK/CLAW: one tapering continuous arc. Lower end bends downward
# like the reference, NOT two straight perpendicular hammer faces.
hook=[
 (14.80,15.42,10.48,12.58),
 (14.34,14.80,10.34,13.55),
 (13.88,14.34,10.75,14.38),
 (13.42,13.88,11.56,15.05),
 (12.96,13.42,12.55,15.48),
 (12.50,12.96,13.78,15.78),
 (12.04,12.50,14.47,15.90),
 (11.58,12.04,14.75,15.96),
 (11.12,11.58,15.06,15.98),
 (10.66,11.12,15.27,15.98),
 (10.20,10.66,15.45,15.99)]
for i,(ya,yb,left,right) in enumerate(hook):
 cub(left,ya,6.60,right,yb,9.40,2 if i%3 else 3,5)
 # Bright ridge embedded at the OUTER UPWARD contour of curved hook.
 if i<7:
  cub(left+.09,yb-.20,6.56,right-.08,yb,9.44,10,11)
 else:
  cub(right-.24,ya,7.13,right,yb,8.87,10,11)
# shoulder blends cleanly into the hub without any disconnected fragments.
cub(9.85,12.6,6.03,11.80,14.6,9.97,1,4)
cub(10.65,13.5,6.35,12.4,14.8,9.65,2,5)

# Prominent inset six-sided magenta gem on both sides of the forged head.
# The ring is painted in a tile, rather than six detached glowing cuboids.
cub(6.80,11.58,5.34,9.25,13.88,5.62,0,4)
cub(6.80,11.58,10.38,9.25,13.88,10.66,0,4)
cub(7.08,11.78,5.20,8.97,13.62,5.36,15)
cub(7.08,11.78,10.64,8.97,13.62,10.80,15)
# Two connected violet flutes around the metal hub.
cub(5.45,12.20,5.48,6.55,12.46,5.76,9,11)
cub(9.55,12.20,5.48,10.35,12.46,5.76,9,11)
cub(5.45,12.20,10.24,6.55,12.46,10.52,9,11)
cub(9.55,12.20,10.24,10.35,12.46,10.52,9,11)

# Refuse detached sections, huge scale in camera, duplicate model parents,
# and invalid UV. All faces use 16x16 legal resource coordinates.
assert 70<len(parts)<220,("B1178_UNEXPECTED_POLY_COUNT",len(parts))
assert all(0<=u<=16 for part in parts for face in part["faces"].values() for u in face["uv"])
data["textures"]={"metal":"obsidiannetwork:item/multitool_3d",
                  "particle":"obsidiannetwork:item/multitool_3d"}
data["gui_light"]="front"
data["elements"]=parts
# Broad axe face always turns toward viewer. Neutral Z keeps the long grip
# upright rather than lying sideways over the whole first-person screen.
data["display"]={
 "gui":{"rotation":[0,10,0],"translation":[0,0,0],"scale":[.89,.89,.89]},
 "firstperson_righthand":{"rotation":[0,-12,10],"translation":[0,1.0,0],"scale":[.43,.43,.43]},
 "firstperson_lefthand":{"rotation":[0,12,-10],"translation":[0,1.0,0],"scale":[.43,.43,.43]},
 "thirdperson_righthand":{"rotation":[0,-12,8],"translation":[0,1.5,0],"scale":[.68,.68,.68]},
 "thirdperson_lefthand":{"rotation":[0,12,-8],"translation":[0,1.5,0],"scale":[.68,.68,.68]},
 "ground":{"translation":[0,2,0],"scale":[.55,.55,.55]},
 "fixed":{"rotation":[0,180,0],"scale":[.85,.85,.85]}}
model.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("B1178_SINGLE_FIRST_PERSON_ARM_WORN_LOCAL_PIVOT_REFERENCE_FORGED_3D_MULTITOOL_PASS",
      "elements=",len(parts))
