#!/usr/bin/env python3
"""B1041: Make THIRD-PERSON & TURRET gun submit through actual Post events,
not only custom RenderLayers that may not execute in users' renderer setup.

B1030 Post path failed because turret tried 'model instanceof HumanoidModel'
while ArmorStandRenderer uses ArmorStandModel, NOT HumanoidModel.
B1032 disabled the real event handlers and relied on optional layers.
Use an independent parented pivot for stand and real PlayerModel.rightArm for
worn player. World barrel B1039 now sits outside the outer-armor mesh.

Only ONE gun owner: native player/stand weapon layers do not submit geometry;
existing Post event subscriber V176MicroMgVisualClient is already registered
for 1st-person and other client events (verified in B1039 bytecode).
"""
import os
from pathlib import Path
R=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def read(x):return (R/x).read_text(encoding="utf-8")
def write(x,s):(R/x).write_text(s,encoding="utf-8")
def method(s,anchor):
 start=s.index(anchor)
 brace=s.index("{",start)
 depth=0
 for i in range(brace,len(s)):
  if s[i]=="{":depth+=1
  if s[i]=="}":
   depth-=1
   if depth==0:return start,i+1,s[start:i+1]
 raise RuntimeError(("B1041_UNBALANCED",anchor))
def swap_method(path,anchor,java):
 s=read(path);a,b,old=method(s,anchor)
 assert "Intentional no-op" in old or "XSXLABS_B1037_" in old,(path,anchor,old[:120])
 write(path,s[:a]+java+s[b:])
# The first-person gun path isn't touched. This class's real @EventBusSubscriber
# ensures Post events are on the NeoForge client GAME bus.
visual="client/V176MicroMgVisualClient.java"
swap_method(visual,
 " @SubscribeEvent public static void wornFallback(",
''' private static final java.util.Set<Integer> XSX_B1041_LOGGED_PLAYER=
    java.util.concurrent.ConcurrentHashMap.newKeySet();
 @SubscribeEvent public static void wornFallback(RenderPlayerEvent.Post<?> event){
  Minecraft mc=Minecraft.getInstance();
  if(mc.level==null)return;
  var state=event.getRenderState();
  Entity entity=mc.level.getEntity(state.id);
  if(!(entity instanceof Player player))return;
  int variant=tier(player);
  if(variant<1||variant>24||!armedForAttack(player))return;
  var renderedArm=event.getRenderer().getModel().rightArm;
  PoseStack pose=event.getPoseStack();
  // Post receives the player's current BODY-YAW/world pose. Enter the
  // same inverted-Y 24px humanoid frame as vanilla PlayerModel exactly once.
  pose.pushPose();
  try{
   pose.translate(0.0F,1.5F,0.0F);
   pose.scale(-1.0F,-1.0F,1.0F);
   float ox=renderedArm.xRot,oy=renderedArm.yRot,oz=renderedArm.zRot;
   try{
    renderedArm.xRot=-1.535F;renderedArm.yRot=0.0F;renderedArm.zRot=0.0F;
    drawArm(pose,event.getSubmitNodeCollector(),state.lightCoords,renderedArm,variant,1.0F);
    if(XSX_B1041_LOGGED_PLAYER.add(state.id))
     System.out.println("XSXLABS_B1041_3PERSON_GUN_POST_SUBMITTED id="+state.id+
         " tier="+variant+" bodyYawInPose=true");
   }finally{
    renderedArm.xRot=ox;renderedArm.yRot=oy;renderedArm.zRot=oz;
   }
  }finally{pose.popPose();}
 }
''')
swap_method(visual,
 " @SubscribeEvent public static void worldSuit(",
''' @SubscribeEvent public static void worldSuit(RenderLivingEvent.Post<?,?,?> event){
  var state=event.getRenderState();
  if(state.entityType!=EntityType.ARMOR_STAND
      ||!(state instanceof net.minecraft.client.renderer.entity.state.ArmorStandRenderState standState))
   return;
  V176MicroMgStandLayer.submitFromPost(event.getPoseStack(),
       event.getSubmitNodeCollector(),state.lightCoords,standState);
 }
''')
# Only one owner of player barrel; a silent native layer no longer claims
# submission. This is a fallback because the in-game B1039 gun was invisible.
player="client/V176MicroMgLayer.java"
p=read(player)
a,b,old=method(p," @Override public void submit(")
assert "XSXLABS_B1037_PLAYER_MG_SUBMIT" in old
p=p[:a]+''' @Override public void submit(PoseStack pose,SubmitNodeCollector nodes,int light,
       AvatarRenderState state,float yaw,float pitch){
  // Post renderer owns the visible player gun; never submit two overlapped
  // opaque barrels from both native layer and Post in the same frame.
 }
'''+p[b:]
write(player,p)
# Turret's existing equipment/tier checks are retained. The only new
# mechanism is a STATIC Post entrypoint using the true ArmorStand render state
# and a model-independent pivot. No HumanoidModel instanceof check.
stand="client/V176MicroMgStandLayer.java"
s=read(stand)
a,b,old=method(s," @Override public void submit(")
assert "XSXLABS_B1037_STAND_MG_SUBMIT" in old
new=''' private static final java.util.Set<Integer> XSX_B1041_LOGGED_STAND=
    java.util.concurrent.ConcurrentHashMap.newKeySet();
 @Override public void submit(PoseStack pose,SubmitNodeCollector nodes,int light,
       ArmorStandRenderState state,float yaw,float pitch){
  // The Post fallback (V176MicroMgVisualClient.worldSuit) owns world rendering.
 }
 public static void submitFromPost(PoseStack post,SubmitNodeCollector nodes,
                                  int light,ArmorStandRenderState state){
  int variant=tier(state);
  if(variant<1||variant>24)return;
  boolean installed=has(state.chestEquipment,"micro_mg")
       ||has(state.headEquipment,"micro_mg")
       ||has(state.legsEquipment,"micro_mg")
       ||has(state.feetEquipment,"micro_mg");
  boolean active=Boolean.TRUE.equals(state.getRenderData(TURRET_ACTIVE))
       ||state.rightArmPose.x()<-35.0F
       ||has(state.chestEquipment,"micro_mg_turret_on");
  if(!installed||!active)return;
  RIGHT_ARM_PIVOT.xRot=(float)Math.toRadians(state.rightArmPose.x());
  RIGHT_ARM_PIVOT.yRot=(float)Math.toRadians(state.rightArmPose.y());
  RIGHT_ARM_PIVOT.zRot=(float)Math.toRadians(state.rightArmPose.z());
  post.pushPose();
  try{
   // Post is in ArmorStand root-world pose; gun pivot is in 24px model space.
   post.translate(0.0F,1.5F,0.0F);
   post.scale(-1.0F,-1.0F,1.0F);
   V176MicroMgVisualClient.drawArm(post,nodes,light,
       RIGHT_ARM_PIVOT,variant,1.0F);
   Integer id=state.getRenderData(TURRET_STAND_ID);
   if(id!=null&&XSX_B1041_LOGGED_STAND.add(id))
    System.out.println("XSXLABS_B1041_TURRET_GUN_POST_SUBMITTED id="+id+
       " tier="+variant+" arm="+state.rightArmPose.x());
  }finally{post.popPose();}
 }
'''
s=s[:a]+new+s[b:]
write(stand,s)
assert "drawArm(pose,event.getSubmitNodeCollector()" in read(visual)
assert "submitFromPost(event.getPoseStack()" in read(visual)
assert "RIGHT_ARM_PIVOT,variant,1.0F" in read(stand)
assert "HumanoidModel" not in read(stand)
assert "nodes.submitModelPart(BARREL,pose" in read(visual)
print("B1041_SINGLE_REGISTERED_3PERSON_POST_AND_ARMORSTAND_POST_WEAPON_SUBMISSIONS_PASS")
