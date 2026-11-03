#!/usr/bin/env python3
"""B1014: player-approved Build 1013 in-game repairs.

- Cell Terminal: real eight-slot direct-to-drive insertion interface, immediate
  server readback/refresh, integrated front instead of floating overlay, proper
  first/third-person item display.
- Micro MG: compact barrel-only third-person forearm mount with front-down /
  rear-up pitch correction; turret ArmorStand world rendering activation from
  reliable synchronized armor data + arm pose; first-person renderer UNCHANGED.
- Dedicated metallic pointed projectile mesh instead of Iron Nugget sprite.

Apply AFTER B982 only, never modify other versions. Fail closed on drift.
"""
import json
import os
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"

def edit(rel,old,new):
 p=J/rel
 s=p.read_text(encoding="utf-8")
 n=s.count(old)
 assert n==1,("B1014_SOURCE_DRIFT",rel,n,old[:120])
 p.write_text(s.replace(old,new,1),encoding="utf-8")

def addjson(rel,data):
 p=A/rel
 assert not p.exists(),("B1014_ASSET_ALREADY_EXISTS",rel)
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")

# 1: INTEGRATE the B982 front into the existing Crafting-Terminal screen.
# The previous front element z=-0.16 floated ahead of the chassis and old
# screen. Reuse existing north screen FACE at z=.58, preserving ALL geometry.
model=A/"models/block/cell_terminal.json"
obj=json.loads(model.read_text(encoding="utf-8"))
screens=[e for e in obj["elements"] if e.get("faces",{}).get("north",{}).get("texture")=="#ns_screen_crafting"]
panels=[e for e in obj["elements"] if e.get("faces",{}).get("north",{}).get("texture")=="#xsx_cell_front"]
assert len(screens)==1 and len(panels)==1,("B1014_SCREEN_GEOMETRY_DRIFT",len(screens),len(panels))
assert panels[0]["from"]==[2.0,2.0,-0.16],("B1014_FLOATING_PANEL_CHANGED",panels[0]["from"])
assert screens[0]["from"][2]>0.0 and screens[0]["to"][2]>0.0
prior=len(obj["elements"])
screens[0]["faces"]["north"]["texture"]="#xsx_cell_front"
obj["elements"].remove(panels[0])
assert len(obj["elements"])==prior-1
assert all(e["from"][2]>=0.0 for e in obj["elements"])
model.write_text(json.dumps(obj,indent=2)+"\n",encoding="utf-8")

# Same 3D model, but explicit hand/GUI display transforms and a clear view
# of the unique Cell Terminal front, not the black rear of an unposed cube.
addjson("models/item/cell_terminal.json",{
 "parent":"obsidiannetwork:block/cell_terminal",
 "display":{
  "gui":{"rotation":[30,225,0],"translation":[0,0,0],"scale":[0.78,0.78,0.78]},
  "thirdperson_righthand":{"rotation":[65,45,0],"translation":[0,2.5,0],"scale":[0.43,0.43,0.43]},
  "thirdperson_lefthand":{"rotation":[65,225,0],"translation":[0,2.5,0],"scale":[0.43,0.43,0.43]},
  "firstperson_righthand":{"rotation":[0,135,0],"translation":[0,1,0],"scale":[0.6,0.6,0.6]},
  "firstperson_lefthand":{"rotation":[0,225,0],"translation":[0,1,0],"scale":[0.6,0.6,0.6]},
  "ground":{"translation":[0,3,0],"scale":[0.35,0.35,0.35]},
  "fixed":{"rotation":[0,180,0],"scale":[0.8,0.8,0.8]}
 }
})
item=A/"items/cell_terminal.json"
descriptor=json.loads(item.read_text(encoding="utf-8"))
assert descriptor["model"]["model"]=="obsidiannetwork:block/cell_terminal","B1014_ITEM_REF_DRIFT"
descriptor["model"]["model"]="obsidiannetwork:item/cell_terminal"
item.write_text(json.dumps(descriptor,indent=2)+"\n",encoding="utf-8")

# 2: Eight cursor-input slots, ALL real-drive forwarding actions, no hidden
# storage on the terminal itself. The server uses real DriveMenu backing.
menu="cellterminal/V176CellTerminalMenu.java"
p=J/menu;s=p.read_text(encoding="utf-8")
a=s.index("  Slot oldDrop=slots.get(0);")
b=s.index("\n }\n @Override public boolean stillValid(Player player){",a)
assert "slots.set(0,new Slot(" in s[a:b]
s=s[:a]+'''  // Eight live insertion pads. They never hold a cell locally.
  for(int pad=0;pad<8;pad++){
   Slot backing=slots.get(pad);
   slots.set(pad,new Slot(backing.container,backing.getContainerSlot(),
       39+(pad%4)*24,81+(pad/4)*24){
    @Override public boolean isActive(){return true;}
    @Override public boolean mayPlace(ItemStack item){
     return item.getItem() instanceof StorageCellItem;
    }
    @Override public boolean mayPickup(Player player){return false;}
   });
  }'''+s[b:]
a=s.index("  // The first visible slot is an INPUT ACTION, never an inventory.")
assert "if(slotId==0){" in s[a:a+140]
s=s.replace("  // The first visible slot is an INPUT ACTION, never an inventory.\n  if(slotId==0){",
'''  // Eight virtual INPUT ACTIONS: only backed by actual network drives.
  if(slotId>=0&&slotId<8){''',1)
assert "if(slotId>0&&slotId<54)return;" in s
s=s.replace("  // All other 53 virtual preview slots remain disabled.\n  if(slotId>0&&slotId<54)return;",
'''  // All other 46 virtual preview slots remain disabled.
  if(slotId>=8&&slotId<54)return;''',1)
assert "    carried.shrink(1); // after the real drive confirms the exact cell" in s
s=s.replace("    broadcastChanges();\n    return;\n   }\n   return;\n  }",
'''    terminal.xsxRefresh(world); // live client counters, no two-second delay
    broadcastChanges();
    return;
   }
   return;
  }''',1)
assert "  broadcastChanges();\n  return original;" in s
s=s.replace("  broadcastChanges();\n  return original;",
'''  terminal.xsxRefresh(world);
  broadcastChanges();
  return original;''',1)
p.write_text(s,encoding="utf-8")

# Client ChestMenu reconstructs its own 54 slots: enable the same eight pads.
screen="client/V176CellTerminalScreen.java"
p=J/screen;s=p.read_text(encoding="utf-8")
a=s.index("  Slot oldDrop=this.menu.slots.get(0);")
b=s.index("\n }\n private V176CellTerminalBlockEntity live(){",a)
assert "this.menu.slots.set(0" in s[a:b]
s=s[:a]+'''  for(int pad=0;pad<8;pad++){
   Slot backing=this.menu.slots.get(pad);
   this.menu.slots.set(pad,new Slot(backing.container,backing.getContainerSlot(),
       39+(pad%4)*24,81+(pad/4)*24){
    @Override public boolean isActive(){return true;}
    @Override public boolean mayPlace(ItemStack item){
     return item.getItem() instanceof dev.obsidiannetwork.item.StorageCellItem;
    }
    @Override public boolean mayPickup(net.minecraft.world.entity.player.Player player){return false;}
   });
  }'''+s[b:]
assert 'g.text(font,"Drop Cell above or SHIFT-CLICK inventory",8,111,0xffb899ff);' in s
s=s.replace('  g.text(font,"Drop Cell above or SHIFT-CLICK inventory",8,111,0xffb899ff);',
'''  g.text(font,"8 LIVE CELL INPUTS",8,120,0xffb899ff);''')
# Remove the old extra explanatory line behind the new slots.
s=s.replace('  g.text(font,"Storage Cells stay in your inventory if full",8,122,0xffaabec9);',
'''  // No false preview grid; failed transfers leave the carried cells untouched.''')
s=s.replace('  g.text(font,"8 LIVE CELL INPUTS",8,120,0xffb899ff);',
'''  g.text(font,"8 LIVE CELL INPUTS",8,18,0xffb899ff);''')
# Draw each of the eight action slots exactly at the ChestMenu coordinates.
old='''  g.fill(x+78,y+54,x+98,y+74,0xff7e56b9);
  g.fill(x+79,y+55,x+97,y+73,0xff271438);'''
assert s.count(old)==1,"B1014_OLD_DROP_BG_DRIFT"
s=s.replace(old,'''  for(int pad=0;pad<8;pad++){
   int sx=x+39+(pad%4)*24,sy=y+81+(pad/4)*24;
   g.fill(sx-2,sy-2,sx+19,sy+19,0xff8c65c7);
   g.fill(sx-1,sy-1,sx+18,sy+18,0xff302147);
   g.fill(sx,sy,sx+17,sy+17,0xff1e152f);
  }''',1)
p.write_text(s,encoding="utf-8")

# Immediate authoritative terminal counts after real DriveMenu mutations.
be="cellterminal/V176CellTerminalBlockEntity.java"
p=J/be;s=p.read_text(encoding="utf-8")
old='''  if(!(world instanceof ServerLevel server)||server.getGameTime()%40L!=0L)return;
  var scan=V176CellTerminalTopology.scan(server,pos);'''
assert s.count(old)==1,("B1014_CELL_TICK_DRIFT",s.count(old))
s=s.replace(old,'''  if(!(world instanceof ServerLevel server)||server.getGameTime()%40L!=0L)return;
  be.xsxRefresh(server);
 }
 public void xsxRefresh(ServerLevel server){
  BlockPos pos=getBlockPos();
  BlockState state=getBlockState();
  var be=this;
  var scan=V176CellTerminalTopology.scan(server,pos);''',1)
# Existing old method's closing bracket still closes new instance method.
p.write_text(s,encoding="utf-8")

# 3: Compact single WORLD barrel on the right FOREARM, behind the wrist.
# Third-person pivots only; the first-person BARREL and hand callback unchanged.
visual="client/V176MicroMgVisualClient.java"
p=J/visual;s=p.read_text(encoding="utf-8")
old=".addBox(-0.52F,3.8F,-2.95F,1.04F,9.5F,1.05F)"
assert s.count(old)==1,("B1014_WORLD_BARREL_SHAPE_DRIFT",s.count(old))
s=s.replace(old,".addBox(-0.45F,6.1F,-2.85F,0.90F,6.6F,0.83F)",1)
# Rotate only the world gun around its forearm center. Front of barrel
# (higher model-Y) lowers; rear lifts slightly to sit flush end-to-end.
old="  pose.translate(0.0F,0.0F,0.04F);"
assert s.count(old)==1,("B1014_WORLD_BARREL_POSE_DRIFT",s.count(old))
s=s.replace(old,'''  pose.translate(0.0F,8.3F/16.0F,0.0F);
  pose.mulPose(com.mojang.math.Axis.XP.rotationDegrees(4.0F));
  pose.translate(0.0F,-8.3F/16.0F,-0.025F);''',1)
# The only world geometry is the thin barrel. Its armor atlas was drawing a
# flat black patch in the third-person weapon; use a dedicated metal material.
arm_start=s.index(" public static void drawArm(")
arm_end=s.index("\n }",arm_start)+3
world_arm=s[arm_start:arm_end]
anchor="nodes.submitModelPart(XSX_WORLD_BARREL,pose,RenderTypes.entitySolid(texture(tier))"
assert world_arm.count(anchor)==1,("B1014_WORLD_TEXTURE_ANCHOR_DRIFT",world_arm.count(anchor))
world_arm=world_arm.replace(anchor,'''nodes.submitModelPart(XSX_WORLD_BARREL,pose,RenderTypes.entitySolid(
       Identifier.fromNamespaceAndPath("obsidiannetwork",
       "textures/entity/micro_mg_world_barrel.png"))''',1)
assert "nodes.submitModelPart(BARREL,pose" not in world_arm
assert "nodes.submitModelPart(HATCH,pose" not in world_arm
s=s[:arm_start]+world_arm+s[arm_end:]
# Deployed stands do not always receive live scoreboard tags on CLIENT;
# the server also syncs the turret module token in equipment and arm pose.
world_start=s.index(" @SubscribeEvent public static void worldSuit(")
world_end=s.index("\n }",world_start)+3
world=s[world_start:world_end]
old='''boolean armed=has(chest,"micro_mg")&&
      (stand.entityTags().contains("xsxlabs_v176_turret")||stand.getRightArmPose().x()<-45F);'''
if old not in world:
 # The exact B957 generated variant may include a different indentation.
 marker='stand.entityTags().contains("xsxlabs_v176_turret")'
 assert marker in world and "stand.getRightArmPose().x()<-45F" in world,("B1014_STAND_ACTIVATION_DRIFT",world[-1800:])
 a=world.rfind("boolean armed=",0,world.index(marker))
 b=world.index(";",world.index(marker))+1
 assert a>=0 and b>a
 world=world[:a]+'''boolean armed=has(chest,"micro_mg_turret_on")
      ||stand.entityTags().contains("xsxlabs_v176_turret")
      ||stand.getRightArmPose().x()<-35F;'''+world[b:]
else:
 world=world.replace(old,'''boolean armed=has(chest,"micro_mg_turret_on")
      ||stand.entityTags().contains("xsxlabs_v176_turret")
      ||stand.getRightArmPose().x()<-35F;''',1)
assert "drawRight(xsxTurretPose" in world
s=s[:world_start]+world+s[world_end:]
p.write_text(s,encoding="utf-8")
# Opaque metallic gun atlas (not the armor's occasional black square pixel).
from PIL import Image,ImageDraw
im=Image.new("RGBA",(32,32),(93,110,127,255))
draw=ImageDraw.Draw(im)
draw.rectangle((0,0,31,4),fill=(170,187,201,255))
draw.rectangle((0,7,31,13),fill=(73,87,104,255))
draw.rectangle((0,15,31,20),fill=(121,141,157,255))
draw.rectangle((0,23,31,28),fill=(44,61,77,255))
draw.line((0,30,31,30),fill=(59,209,226,255),width=1)
out=A/"textures/entity/micro_mg_world_barrel.png"
assert not out.exists()
out.parent.mkdir(parents=True,exist_ok=True)
im.save(out)

# 4: Dedicated pointed 3D bullet. Never render Iron Nuggets as projectiles.
edit("ObsidianNetwork.java",
'''   public static final DeferredItem<net.minecraft.world.item.Item> COMPRESSED_OBSIDIAN_1X =''',
'''   public static final DeferredItem<net.minecraft.world.item.Item> MICRO_MG_ROUND =
      ITEMS.registerSimpleItem("micro_mg_round",() -> new net.minecraft.world.item.Item.Properties().stacksTo(1));
   public static final DeferredItem<net.minecraft.world.item.Item> COMPRESSED_OBSIDIAN_1X =''')
edit("powerarmor/V176MicroMgProjectile.java",
'''@Override protected Item getDefaultItem(){return Items.IRON_NUGGET;}''',
'''@Override protected Item getDefaultItem(){return ObsidianNetwork.MICRO_MG_ROUND.get();}''')
edit("client/V176MicroMgBulletRenderer.java",
'''ctx->new net.minecraft.client.renderer.entity.ThrownItemRenderer<>(ctx,0.35F,true));''',
'''ctx->new net.minecraft.client.renderer.entity.ThrownItemRenderer<>(ctx,0.28F,true));''')
def cuboid(fr,to,texture):
 return {"from":fr,"to":to,"faces":{
  face:{"texture":"#"+texture} for face in
  ("down","up","north","south","west","east")
 }}
addjson("models/item/micro_mg_round.json",{
 "textures":{"metal":"obsidiannetwork:block/ns_chassis2",
             "tip":"minecraft:block/iron_block",
             "rim":"minecraft:block/gold_block",
             "particle":"minecraft:block/iron_block"},
 "elements":[
  cuboid([6.1,6.1,3.5],[9.9,9.9,8],"rim"),
  cuboid([6.3,6.3,8],[9.7,9.7,12.4],"metal"),
  cuboid([7,7,12.4],[9,9,14.3],"tip"),
  cuboid([7.6,7.6,14.3],[8.4,8.4,15],"tip")
 ],
 "display":{
  "gui":{"rotation":[20,40,0],"scale":[0.8,0.8,0.8]},
  "ground":{"scale":[0.4,0.4,0.4]}
 }
})
addjson("items/micro_mg_round.json",{"model":{"type":"minecraft:model","model":"obsidiannetwork:item/micro_mg_round"}})
assert "Items.IRON_NUGGET" not in (J/"powerarmor/V176MicroMgProjectile.java").read_text()
assert "XSX_WORLD_BARREL" in (J/visual).read_text()
assert "nodes.submitModelPart(BARREL,pose" in (J/visual).read_text(), "B1014_FIRST_PERSON_GUN_LOST"
assert "8 LIVE CELL INPUTS" in (J/screen).read_text()
assert "if(slotId>=0&&slotId<8)" in (J/menu).read_text()
assert "xsxRefresh(world)" in (J/menu).read_text()
assert "xsxRefresh(ServerLevel server)" in (J/be).read_text()
assert 'obsidiannetwork:item/cell_terminal' in item.read_text()
print("B1014_EIGHT_LIVE_CELLS_INTEGRATED_FRONT_HAND_ITEM_WORLD_FOREARM_TURRET_POINTED_PROJECTILES_PASS")
