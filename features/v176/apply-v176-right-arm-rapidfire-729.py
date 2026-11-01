#!/usr/bin/env python3
"""B729: player-requested one RIGHT arm weapon; smaller mechanical hatch/slide;
8 physical projectiles/sec (2x original) and all server/client origins on RIGHT.

Runs after B699/B717/B718. No changes to existing suit entry/exit/Recall rig.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def edit(rel,old,new):
 p=J/rel
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("V176_B729_DRIFT",rel,s.count(old),old[:110])
 p.write_text(s.replace(old,new,1),encoding="utf-8")

# 8 shots per 20 TPS second: at ticks mod 5 == 0 or 2.
# 2 tick minimum and 3 tick alternate prevent >8/s despite client packet spam.
edit("powerarmor/V176MicroMgRules.java",
 ''' public static final int COOLDOWN_TICKS=5; // Max 4 projectiles / second at 20 TPS''',
 ''' public static final int COOLDOWN_TICKS=2; // 2/3-tick beat => exactly max 8 shots/sec at 20 TPS''')
edit("powerarmor/V176MicroMgRules.java",
 '''  return lastShotTick<0 || (tick>=lastShotTick && tick-lastShotTick>=COOLDOWN_TICKS);''',
 '''  if(lastShotTick<0)return true; // First trigger responds instantly.
  return tick>=lastShotTick && tick-lastShotTick>=COOLDOWN_TICKS
      &&(tick%5L==0L||tick%5L==2L); // 0,2,5,7,... 8 shots per second''')

edit("powerarmor/V176MicroMgFire.java",
 '''  double side=((now/5L)&1L)==0L?0.27D:-0.27D;
  Vec3 origin=p.getEyePosition().add(dir.scale(0.55D))
             .add(right.scale(side)).add(0,-0.30D,0);''',
 '''  // Only the wearer's RIGHT wrist has a muzzle. Left arm remains unarmed.
  Vec3 origin=p.getEyePosition().add(dir.scale(0.50D))
             .add(right.scale(0.34D)).add(0,-0.35D,0);''')

# Client issues first click immediately, subsequently one command on each
# 2/3 server tick beat. Keep server as sole authority on FE and damage.
edit("client/V176MicroMgFireClient.java",
 ''' private static long next=-1L;''',
 ''' private static long next=-1L;
 private static boolean wasDown=false;''')
edit("client/V176MicroMgFireClient.java",
 '''  if(!ready()){next=-1L;return;}''',
 '''  if(!ready()){next=-1L;wasDown=false;return;}''')
edit("client/V176MicroMgFireClient.java",
 '''  if(!mc.mouseHandler.isMouseGrabbed())return; // ignore action wheel's released cursor
  if(GLFW.glfwGetMouseButton(mc.getWindow().handle(),GLFW.GLFW_MOUSE_BUTTON_LEFT)!=GLFW.GLFW_PRESS)
   return;
  long tick=mc.level.getGameTime();
  if(next>=0L && tick<next)return;
  next=tick+V176MicroMgFireClient.cooldown();''',
 '''  if(!mc.mouseHandler.isMouseGrabbed()){wasDown=false;return;} // no wheel click
  if(GLFW.glfwGetMouseButton(mc.getWindow().handle(),GLFW.GLFW_MOUSE_BUTTON_LEFT)!=GLFW.GLFW_PRESS){
   wasDown=false;next=-1L;return;
  }
  long tick=mc.level.getGameTime();
  boolean first=!wasDown;
  wasDown=true;
  if(!first&&tick%5L!=0L&&tick%5L!=2L)return; // doubled 2/3 tick beat
  if(next>=0L && tick<next)return;
  next=tick+2L;''')
edit("client/V176MicroMgFireClient.java",
 ''' private static int cooldown(){return 5;}''',
 ''' private static int cooldown(){return 2;}''')

# Turret is now checked every server tick, while owner-follow position changes
# retain their original 5-tick rate. A second mouse/AI gun does not exist.
edit("powerarmor/V176CompanionMode.java",
 '''  if(!(event.getEntity() instanceof ServerPlayer player)||player.tickCount%5!=0)return;''',
 '''  if(!(event.getEntity() instanceof ServerPlayer player))return;''')
edit("powerarmor/V176CompanionMode.java",
 '''  double dist=suit.distanceToSqr(player);
  if(dist>14D*14D){''',
 '''  if(player.tickCount%5==0){ // preserve original companion movement cadence
  double dist=suit.distanceToSqr(player);
  if(dist>14D*14D){''')
edit("powerarmor/V176CompanionMode.java",
 '''  if(!turret||!hasModule(suit))return;
  ItemStack chest=suit.getItemBySlot(EquipmentSlot.CHEST);''',
 '''  }
  if(!turret||!hasModule(suit))return;
  ItemStack chest=suit.getItemBySlot(EquipmentSlot.CHEST);''')
edit("powerarmor/V176CompanionMode.java",
 '''   double barrelSide=((now/5L)&1L)==0L?0.27D:-0.27D;
   Vec3 muzzle=start.add(right.scale(barrelSide)).add(0,-0.20D,0);''',
 '''   // One muzzle, under the RIGHT wrist of the armor.
   Vec3 muzzle=start.add(right.scale(0.34D)).add(0,-0.13D,0);''')

# Small dark-tech single right wrist barrel; visible rear forearm hatch opens
# ~19 degrees and barrel slides forward over 8 world ticks, not 8 render frames.
rel="client/V176MicroMgVisualClient.java"
edit(rel,
 ''' private static final ModelPart BARREL=createBarrel();
 private static final Map<Integer,Float> EXTENSION=new HashMap<>();''',
 ''' private static final ModelPart BARREL=createBarrel();
 private static final ModelPart HATCH=createHatch();
 private static final Map<Integer,Float> EXTENSION=new HashMap<>();
 private static final Map<Integer,Long> LAST_RENDER_TICK=new HashMap<>();''')

edit(rel,
 '''    CubeListBuilder.create()
      .texOffs(0,0).addBox(-1.0F,5.5F,-9.0F,2.0F,2.0F,7.0F)
      .texOffs(0,10).addBox(-1.25F,5.25F,-9.5F,2.5F,2.5F,1.5F)
      .texOffs(0,16).addBox(-1.5F,5.0F,-4.0F,3.0F,3.0F,3.0F),
    PartPose.ZERO);
  return LayerDefinition.create(mesh,32,32).bakeRoot().getChild("barrel");
 }''',
 '''    CubeListBuilder.create()
      // Miniature rifle housing INSIDE the forearm; arm local +Y is forward
      // after the right arm raises. Old 9px shoulder-overhanging barrel removed.
      .texOffs(0,0).addBox(-0.8F,6.0F,-1.6F,1.6F,5.5F,1.8F)
      .texOffs(0,9).addBox(-1.1F,10.5F,-1.9F,2.2F,1.3F,2.4F)
      .texOffs(0,15).addBox(-1.25F,6.0F,-1.9F,2.5F,2.8F,2.8F),
    PartPose.ZERO);
  return LayerDefinition.create(mesh,32,32).bakeRoot().getChild("barrel");
 }
 private static ModelPart createHatch(){
  MeshDefinition mesh=new MeshDefinition();
  mesh.getRoot().addOrReplaceChild("hatch",
    CubeListBuilder.create()
      .texOffs(12,0).addBox(-1.6F,6.0F,1.65F,3.2F,4.6F,0.65F),
    PartPose.ZERO);
  return LayerDefinition.create(mesh,32,32).bakeRoot().getChild("hatch");
 }''')

edit(rel,
 '''  float old=EXTENSION.getOrDefault(key,0.0F);
  float next=armed?Math.min(1.0F,old+0.12F):Math.max(0.0F,old-0.12F);
  if(next==0.0F)EXTENSION.remove(key);
  else EXTENSION.put(key,next);
  return next;''',
 '''  Minecraft mc=Minecraft.getInstance();
  long now=mc.level==null?0:mc.level.getGameTime();
  Long prior=LAST_RENDER_TICK.put(key,now);
  // Tick-driven, independent of monitor FPS; 8 ticks => ~0.4s animation.
  long elapsed=prior==null?1L:Math.max(0L,Math.min(8L,now-prior));
  float old=EXTENSION.getOrDefault(key,0.0F);
  float step=0.125F*elapsed;
  float next=armed?Math.min(1.0F,old+step):Math.max(0.0F,old-step);
  if(next==0.0F){EXTENSION.remove(key);if(!armed)LAST_RENDER_TICK.remove(key);}
  else EXTENSION.put(key,next);
  return next;''')

edit(rel,
 '''  // Sub-armor housing stays hidden until extended; smooth mechanical slide.
  pose.translate(0.0F,0.0F,(1.0F-extension)*0.40F);
  nodes.submitModelPart(BARREL,pose,RenderTypes.entitySolid(texture(tier)),
      light,OverlayTexture.NO_OVERLAY,null,false,false,0xFFFFFFFF,null,0);
  pose.popPose();
 }
 private static void drawPair(PoseStack pose,SubmitNodeCollector nodes,int light,
      HumanoidModel<?> model,int tier,float extension){
  drawArm(pose,nodes,light,model.leftArm,tier,extension);
  drawArm(pose,nodes,light,model.rightArm,tier,extension);
 }''',
 '''  // First the actual rear forearm shell hinges out by only 19 degrees.
  pose.pushPose();
  pose.translate(0.0F,7.0F/16.0F,2.1F/16.0F);
  pose.mulPose(com.mojang.math.Axis.XP.rotationDegrees(-19.0F*extension));
  pose.translate(0.0F,-7.0F/16.0F,-2.1F/16.0F);
  nodes.submitModelPart(HATCH,pose,RenderTypes.entitySolid(texture(tier)),
      light,OverlayTexture.NO_OVERLAY,null,false,false,0xFFFFFFFF,null,0);
  pose.popPose();
  // The short barrel physically slides out parallel to the right forearm.
  pose.translate(0.0F,-(1.0F-extension)*0.25F,0.0F);
  nodes.submitModelPart(BARREL,pose,RenderTypes.entitySolid(texture(tier)),
      light,OverlayTexture.NO_OVERLAY,null,false,false,0xFFFFFFFF,null,0);
  pose.popPose();
 }
 private static void drawRight(PoseStack pose,SubmitNodeCollector nodes,int light,
      HumanoidModel<?> model,int tier,float extension){
  if(extension<=0.001F)return;
  float original=model.rightArm.xRot;
  model.rightArm.xRot=original*(1F-extension)-1.40F*extension;
  drawArm(pose,nodes,light,model.rightArm,tier,extension);
  model.rightArm.xRot=original;
 }
 // Raise precisely the RIGHT player arm before the player model is rendered.
 // Keep the left arm's normal vanilla walking/action animation.
 @SubscribeEvent public static void aimRight(RenderPlayerEvent.Pre<?> event){
  Minecraft mc=Minecraft.getInstance();
  if(mc.level==null)return;
  Entity entity=mc.level.getEntity(event.getRenderState().id);
  if(!(entity instanceof Player player))return;
  int variant=tier(player);
  if(variant==0)return;
  ItemStack chest=player.getItemBySlot(EquipmentSlot.CHEST);
  float extend=extension(entity.getId(),
     has(chest,"micro_mg")&&has(chest,"micro_mg_on"));
  if(extend<=0F)return;
  var arm=event.getRenderer().getModel().rightArm;
  arm.xRot=arm.xRot*(1F-extend)-1.40F*extend;
  arm.yRot*=1F-extend;
  arm.zRot*=1F-extend;
 }''')

edit(rel,
 '''   drawPair(event.getPoseStack(),event.getSubmitNodeCollector(),
      event.getRenderState().lightCoords,event.getRenderer().getModel(),tier,amount);''',
 '''   drawRight(event.getPoseStack(),event.getSubmitNodeCollector(),
      event.getRenderState().lightCoords,event.getRenderer().getModel(),tier,amount);''')

edit(rel,
 '''  var player=event.getPlayer();
  int tier=tier(player);''',
 '''  if(event.getArm()!=net.minecraft.world.entity.HumanoidArm.RIGHT)return;
  var player=event.getPlayer();
  int tier=tier(player);''')
edit(rel,
 '''  pose.translate(0.0F,0.0F,-0.28F);
  event.getSubmitNodeCollector().submitModelPart(BARREL,pose,
    RenderTypes.entitySolid(texture(tier)),event.getPackedLight(),
    OverlayTexture.NO_OVERLAY,null,false,false,0xFFFFFFFF,null,0);
  pose.popPose();''',
 '''  // Only the right first-person forearm; compact arm-mounted muzzle.
  pose.translate(0.14F,0.12F,-0.10F);
  pose.pushPose();
  pose.mulPose(com.mojang.math.Axis.XP.rotationDegrees(-19.0F));
  event.getSubmitNodeCollector().submitModelPart(HATCH,pose,
    RenderTypes.entitySolid(texture(tier)),event.getPackedLight(),
    OverlayTexture.NO_OVERLAY,null,false,false,0xFFFFFFFF,null,0);
  pose.popPose();
  event.getSubmitNodeCollector().submitModelPart(BARREL,pose,
    RenderTypes.entitySolid(texture(tier)),event.getPackedLight(),
    OverlayTexture.NO_OVERLAY,null,false,false,0xFFFFFFFF,null,0);
  pose.popPose();''')

edit(rel,
 '''    drawPair(event.getPoseStack(),event.getSubmitNodeCollector(),
       state.lightCoords,model,tier,amount);''',
 '''    drawRight(event.getPoseStack(),event.getSubmitNodeCollector(),
       state.lightCoords,model,tier,amount);''')

client=(J/rel).read_text(encoding="utf-8")
fire=(J/"powerarmor/V176MicroMgFire.java").read_text(encoding="utf-8")
mode=(J/"powerarmor/V176CompanionMode.java").read_text(encoding="utf-8")
assert "drawPair(" not in client and "model.leftArm" not in client
assert 'event.getArm()!=net.minecraft.world.entity.HumanoidArm.RIGHT' in client
assert "createHatch()" in client and "0.125F*elapsed" in client
assert "right.scale(0.34D)" in fire and "right.scale(0.34D)" in mode
assert "barrelSide" not in mode
print("V176_B729_RIGHT_ARM_ONLY_HATCH_SLIDE_8_SHOTS_PER_SECOND_PASS")
