#!/usr/bin/env python3
"""B910: correct real player-arm pipeline, module hit testing, monitor front.

Apply AFTER B907, on reconstructed NeoForge 26.1 v1.7.6 source.
No earlier stable versions, cell contents, or game combat logic are changed.
"""
import os, json
from pathlib import Path
from PIL import Image, ImageDraw

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"

def change(path,old,new):
 p=J/path
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("B910_DRIFT",path,s.count(old),old[:110])
 p.write_text(s.replace(old,new,1),encoding="utf-8")

# B907 rotated the outer RenderHandEvent pose *without restoring it*, moving
# the actual vanilla first-person arm out of the camera. The barrel must only
# change its own pushed transform. The arm must remain vanilla-visible.
gun="client/V176MicroMgVisualClient.java"
change(gun,
"""  PoseStack pose=event.getPoseStack();
  // RenderHandEvent precedes the vanilla main-hand draw. Rotate its shared
  // camera-space arm pose so the visible right arm aims forward as one rigid
  // piece. Keep the already aligned barrel on its original view axis by
  // undoing this parent rotation only inside the barrel's submission scope.
  // Deliberately do NOT pop the outer rotation: vanilla arm must receive it.
  pose.translate(0.0F,0.075F,-0.045F);
  pose.mulPose(com.mojang.math.Axis.XP.rotationDegrees(-36.0F));
  pose.pushPose();
  pose.mulPose(com.mojang.math.Axis.XP.rotationDegrees(36.0F));
  // Camera-relative right upper arm. Positive model Y must point forwards.""",
"""  // Never alter the caller's hand matrix. A transformed parent frame hid
  // the real hand in B909 while the separate barrel stayed visible.
  PoseStack pose=event.getPoseStack();
  pose.pushPose();
  // Camera-relative RIGHT upper arm only; vanilla right hand remains shown.""")
# Hook the actual vanilla arm pass, not RenderHandEvent's parent pose.
# Keep the displacement small enough that hand and sleeve remain on screen.
change(gun,
"import net.neoforged.neoforge.client.event.RenderHandEvent;",
"import net.neoforged.neoforge.client.event.RenderHandEvent;\nimport net.neoforged.neoforge.client.event.RenderArmEvent;")
change(gun,
" @SubscribeEvent public static void worldSuit(",
""" @SubscribeEvent public static void xsxlabs$aimVisibleFirstPersonArm(RenderArmEvent event){
  if(event.getArm()!=net.minecraft.world.entity.HumanoidArm.RIGHT
      ||!armedForAttack(event.getPlayer()))return;
  // NeoForge's actual visible arm pass; do not cancel or change the other hand.
  event.getPoseStack().translate(0.0F,0.035F,-0.075F);
  event.getPoseStack().mulPose(com.mojang.math.Axis.XP.rotationDegrees(-11.0F));
 }
 @SubscribeEvent public static void worldSuit(""")

# A shoulder-mounted orphan gun came from this whole-player post-render
# fallback. It uses a different coordinate frame than the armor/player's arm.
# Render the weapon ONLY through the registered rightArm-attached layer.
p=J/gun
s=p.read_text(encoding="utf-8")
start=" @SubscribeEvent public static void wornFallback("
end=" public static void drawArm("
assert s.count(start)==1 and s.count(end)==1 and s.index(start)<s.index(end),"B910_POST_RENDER_DRIFT"
s=s[:s.index(start)]+""" // No Post event weapon: it ignores the true arm's submitted pose.
""" + s[s.index(end):]
p.write_text(s,encoding="utf-8")

# Guarantee that the *actual player model* and the armor render context
# both get the right-arm pose, independently of the gun's draw operation.
# B878's Pre event provides this context before rendering attached armor.
context="client/V176AttackPoseContext.java"
change(context,
"  PLAYER_RENDER_ARMED.set(armed);",
"""  PLAYER_RENDER_ARMED.set(armed);
  if(armed){
   // Use the model the renderer will actually submit. Apply again in the
   // PlayerModel setupAnim TAIL mixin, because other mods may animate it.
   var model=event.getRenderer().getModel();
   model.rightArm.xRot=-1.5707964F;
   model.rightArm.yRot=0.0F;
   model.rightArm.zRot=0.0F;
   model.rightArm.visible=true;
   model.rightSleeve.xRot=model.rightArm.xRot;
   model.rightSleeve.yRot=0.0F;
   model.rightSleeve.zRot=0.0F;
   model.rightSleeve.visible=true;
  }""")
# The final animation hook must keep both actual arm geometry and sleeve
# visible. Do NOT create a second false arm or affect the left arm.
change("mixin/V176AttackPlayerModelMixin.java",
"  this.rightArm.xRot=-1.5707964F;",
"  this.rightArm.xRot=-1.5707964F;\n  this.rightArm.visible=true;")
change("mixin/V176AttackPlayerModelMixin.java",
"  sleeve.xRot=this.rightArm.xRot;",
"  sleeve.visible=true;\n  sleeve.xRot=this.rightArm.xRot;")
change("mixin/V176AttackRightArmMixin.java",
"  rightArm.xRot=-1.5707964F;",
"  rightArm.xRot=-1.5707964F;\n  rightArm.visible=true;")
layer="client/V176MicroMgLayer.java"
change(layer,
"  arm.xRot=-1.5707964F;arm.yRot=0F;arm.zRot=0F;",
"  arm.xRot=-1.5707964F;arm.yRot=0F;arm.zRot=0F;\n  arm.visible=true;")
assert "getParentModel().rightArm" in (J/layer).read_text()
assert "wornFallback(RenderPlayerEvent.Post" not in (J/gun).read_text()
assert "pose.mulPose(com.mojang.math.Axis.XP.rotationDegrees(-36.0F));" not in (J/gun).read_text()

# Client ChestMenu virtual slots are not the server-owned backpack menu.
# Route any click ON a real module slot explicitly to that slot's exact ID.
# Swallow empty background clicks so clicking labels can never pick up slot 0.
screen="client/V176BackpackScreen.java"
change(screen,
"  boolean onSearch=searchBox!=null&&searchBox.isMouseOver(mx,my);",
"""  int moduleX=(int)mx-getLeftPos(),moduleY=(int)my-getTopPos();
  if((button==0||button==1)&&moduleX>=190&&moduleX<218
       &&moduleY>=16&&moduleY<115){
   int selected=(moduleY-20+2)/24;
   if(selected>=0&&selected<4&&moduleY>=20+selected*24-2
        &&moduleY<20+selected*24+18&&moduleX>=193&&moduleX<214){
    var game=net.minecraft.client.Minecraft.getInstance();
    if(game.player!=null&&game.gameMode!=null)
     game.gameMode.handleContainerInput(menu.containerId,selected,button,
         event.hasShiftDown()?net.minecraft.world.inventory.ContainerInput.QUICK_MOVE:
         net.minecraft.world.inventory.ContainerInput.PICKUP,game.player);
   }
   return true;
  }
  if((button==0||button==1)&&moduleX>=183&&moduleX<275
       &&moduleY>=8&&moduleY<124)return true;
  boolean onSearch=searchBox!=null&&searchBox.isMouseOver(mx,my);""")
# Important: the client module slots and server slots must remain indexed
# 0=magnet, 1..3=cells. The filter buttons below 124 retain normal clicks.
assert "handleContainerInput(menu.containerId,selected,button" in (J/screen).read_text()

# Dedicated COMPUTER / POWER MONITOR front: no inherited controller symbol.
# A textured dark bezel, vivid screen, readout panels, graph and status LEDs.
base=A/"textures/block"
base.mkdir(parents=True,exist_ok=True)
img=Image.new("RGBA",(32,32),(45,53,62,255))
d=ImageDraw.Draw(img)
d.rectangle((0,0,31,31),outline=(135,151,166),width=2)
d.rectangle((3,3,28,28),fill=(12,22,33),outline=(74,105,121),width=2)
d.rectangle((5,5,26,22),fill=(2,17,27),outline=(30,168,185),width=1)
d.rectangle((7,7,24,9),fill=(33,153,197))
for x in range(7,25,2):d.point((x,7),fill=(118,237,242))
d.rectangle((7,11,15,19),fill=(6,45,60))
d.rectangle((17,11,24,19),fill=(6,45,60))
for y,ln in [(12,6),(15,4),(18,7)]:
 d.line((8,y,8+ln,y),fill=(69,222,233),width=1)
d.line([(18,17),(20,15),(21,16),(23,12)],fill=(103,244,161),width=2)
d.rectangle((6,24,25,27),fill=(34,55,69),outline=(83,112,128),width=1)
for x in range(8,24,3):d.line((x,26,x+1,26),fill=(127,195,208))
d.rectangle((3,28,7,29),fill=(74,229,157))
d.rectangle((9,28,13,29),fill=(75,178,232))
dest=base/"power_terminal_computer_front.png"
img.save(dest,optimize=True)
model=A/"models/block/power_terminal.json"
assert model.is_file(),("B910_NO_MONITOR_MODEL",model)
# All horizontal faces use the high-contrast display since the terminal
# block currently has no horizontal FACING property.
model.write_text(json.dumps({
 "parent":"minecraft:block/cube",
 "textures":{
  "particle":"obsidiannetwork:block/power_terminal_computer_front",
  "north":"obsidiannetwork:block/power_terminal_computer_front",
  "south":"obsidiannetwork:block/power_terminal_computer_front",
  "east":"obsidiannetwork:block/power_terminal_computer_front",
  "west":"obsidiannetwork:block/power_terminal_computer_front",
  "up":"obsidiannetwork:block/power_terminal_computer_front",
  "down":"obsidiannetwork:block/power_terminal_computer_front"
 }},indent=2)+"\n",encoding="utf-8")
with Image.open(dest) as chk:assert chk.size==(32,32)
print("B910_RIGHT_ARM_VISIBLE_THIRDPERSON_TRUE_ARM_ONLY_EXACT_MODULE_SLOTS_COMPUTER_FRONT_PASS")
