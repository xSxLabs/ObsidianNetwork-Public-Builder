#!/usr/bin/env python3
"""B917: fix first-person right-arm/barrel axis, OFF sequencing, black hatch,
and Power Monitor ghost inventory removal. Runs AFTER B915.
The active third-person pose and left-arm code are deliberately untouched.
"""
import os
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def modify(rel, old, new):
    path=J/rel
    value=path.read_text(encoding="utf-8")
    assert value.count(old)==1, ("B917_SOURCE_DRIFT",rel,value.count(old),old[:90])
    path.write_text(value.replace(old,new,1),encoding="utf-8")

def bounded(rel, first, following, replacement):
    path=J/rel
    value=path.read_text(encoding="utf-8")
    assert value.count(first)==1 and value.count(following)==1
    a=value.index(first)
    b=value.index(following,a)
    assert a<b,("B917_METHOD_DRIFT",rel)
    path.write_text(value[:a]+replacement+value[b:],encoding="utf-8")

gun="client/V176MicroMgVisualClient.java"
modify(gun,
 " private static final Map<Integer,Float> EXTENSION=new HashMap<>();",
 """ private static final Map<Integer,Float> EXTENSION=new HashMap<>();
 /** Read-only deployment phase. Never advance animation from a render-pose hook. */
 public static float deploymentProgress(int entityId){
  return EXTENSION.getOrDefault(entityId,0.0F);
 }""")

# The separate RenderHandEvent barrel did not share the renderer's actual
# first-person arm frame. Render it from the SAME RenderArmEvent frame as the
# visible right arm when the main hand is empty (the attack-mode view).
# For players holding an item, retain the existing RenderHandEvent fallback.
bounded(gun,
 " @SubscribeEvent public static void firstPerson(RenderHandEvent event){",
 " @SubscribeEvent public static void xsxlabs$aimVisibleFirstPersonArm(RenderArmEvent event){",
 """ @SubscribeEvent public static void firstPerson(RenderHandEvent event){
  if(event.getHand()!=InteractionHand.MAIN_HAND)return;
  Minecraft mc=Minecraft.getInstance();
  if(mc.player==null)return;
  int equippedTier=tier(mc.player);
  if(equippedTier<1||equippedTier>24)return;
  boolean armed=armedForAttack(mc.player);
  // RenderHandEvent is also the animation heartbeat during RETRACTION.
  float progress=extension(mc.player.getId(),armed);
  if(progress<=0.001F||event.getItemStack().isEmpty())return;
  // Only the held-item fallback uses the independent camera-space path.
  float gunOut=phase(progress,7.0F/12.0F,1.0F);
  if(gunOut<=0.001F)return;
  PoseStack pose=event.getPoseStack();
  pose.pushPose();
  pose.translate(0.58F,-0.30F,-0.53F);
  pose.mulPose(com.mojang.math.Axis.XP.rotationDegrees(-96.0F));
  pose.translate(0.0F,-(1.0F-gunOut)*0.32F,0.0F);
  event.getSubmitNodeCollector().submitModelPart(BARREL,pose,
    RenderTypes.entitySolid(texture(equippedTier)),event.getPackedLight(),
    OverlayTexture.NO_OVERLAY,null,false,false,0xFFFFFFFF,null,0);
  pose.popPose();
 }
""")
bounded(gun,
 " @SubscribeEvent public static void xsxlabs$aimVisibleFirstPersonArm(RenderArmEvent event){",
 " @SubscribeEvent public static void worldSuit(",
 """ @SubscribeEvent public static void xsxlabs$aimVisibleFirstPersonArm(RenderArmEvent event){
  if(event.getArm()!=net.minecraft.world.entity.HumanoidArm.RIGHT)return;
  var player=event.getPlayer();
  int equippedTier=tier(player);
  if(equippedTier<1||equippedTier>24)return;
  float progress=deploymentProgress(player.getId());
  if(!armedForAttack(player)&&progress<=0.001F)return;
  // This transform belongs ONLY to the genuine right arm, not the world suit.
  // The gun below is submitted within THIS exact arm coordinate frame.
  PoseStack pose=event.getPoseStack();
  pose.translate(-0.05F,0.10F,-0.18F);
  pose.mulPose(com.mojang.math.Axis.XP.rotationDegrees(-50.0F));
  float gunOut=phase(progress,7.0F/12.0F,1.0F);
  if(gunOut<=0.001F)return;
  pose.pushPose();
  // Humanoid right arm shoulder pivot: x=-5, y=2 model pixels.
  // The barrel itself extends along local +Y, exactly like the right arm.
  pose.translate(-5.0F/16.0F,2.0F/16.0F,0.0F);
  pose.translate(0.0F,-(1.0F-gunOut)*0.32F,0.0F);
  event.getSubmitNodeCollector().submitModelPart(BARREL,pose,
    RenderTypes.entitySolid(texture(equippedTier)),event.getPackedLight(),
    OverlayTexture.NO_OVERLAY,null,false,false,0xFFFFFFFF,null,0);
  pose.popPose();
 }
""")

# The hatch's detached black rectangle was visible while fully deployed.
# Keep the short opening/closing phase, but never draw it as a free-standing
# black panel in steady Attack Mode. The original barrel stays unchanged.
modify(gun,
 "      .texOffs(12,0).addBox(-0.70F,3.30F,-2.95F,1.40F,1.55F,0.28F)",
 "      .texOffs(12,0).addBox(-0.10F,3.50F,-2.75F,0.20F,0.25F,0.05F)")

# B915 already produces the correct fully-active third-person arm. Preserve
# EXACTLY the pose, but keep it raised as the gun retracts and hatch closes.
# Once the gun is stowed, lower smoothly over the last 4/12 of extension.
context="client/V176AttackPoseContext.java"
modify(context,
 " private static Boolean lastLocalAim=null;",
 """ private static Boolean lastLocalAim=null;
 private static final ThreadLocal<Integer> RENDERED_PLAYER_ID=
     ThreadLocal.withInitial(()->-1);
 public static int renderingPlayerId(){return RENDERED_PLAYER_ID.get();}""")
modify(context,
 "  PLAYER_RENDER_ARMED.set(armed);",
 "  PLAYER_RENDER_ARMED.set(armed);\n  RENDERED_PLAYER_ID.set(state.id);")
modify(context,
 "  PLAYER_RENDER_ARMED.remove();",
 "  PLAYER_RENDER_ARMED.remove();\n  RENDERED_PLAYER_ID.remove();")

pose="client/V176FinalArmPose.java"
bounded(pose,
 " private static final Map<Model<?>,Boolean> ACTIVE=new WeakHashMap<>();",
 "\n}\n",
 """ private static final Map<Model<?>,Float> RAISE=new WeakHashMap<>();
 private static final Map<Model<?>,Float> BASE_X=new WeakHashMap<>();
 public static void track(Model<?> model,HumanoidRenderState state){
  boolean active=V176AttackPoseContext.aim(state);
  int id=state instanceof net.minecraft.client.renderer.entity.state.AvatarRenderState avatar
      ?avatar.id:V176AttackPoseContext.renderingPlayerId();
  float progress=id<0?0.0F:V176MicroMgVisualClient.deploymentProgress(id);
  // Only lower AFTER barrel retracts (1 -> 7/12) and hatch closes
  // (7/12 -> 4/12). Active pose remains bit-for-bit -PI/2.
  float raised=active?1.0F:Math.min(1.0F,progress/(4.0F/12.0F));
  RAISE.put(model,raised);
  if(model instanceof HumanoidModel<?> h)BASE_X.put(model,h.rightArm.xRot);
 }
 public static void apply(Model<?> model){
  Float raised=RAISE.get(model);
  if(raised==null||raised<=0.0F||!(model instanceof HumanoidModel<?> h))return;
  float baseline=BASE_X.getOrDefault(model,h.rightArm.xRot);
  h.rightArm.xRot=baseline*(1.0F-raised)-1.5707964F*raised;
  h.rightArm.yRot=0F;h.rightArm.zRot=0F;
  h.rightArm.visible=true;
  if(model instanceof PlayerModel p){
   p.rightSleeve.xRot=h.rightArm.xRot;
   p.rightSleeve.yRot=0F;p.rightSleeve.zRot=0F;
   p.rightSleeve.visible=true;
  }
 }""")

# The reported invisible slots are in the POWER MONITOR, NOT the Backpack.
# Preserve every Backpack menu/screen action and shift-click path unchanged.
# ChestMenu contributes 54 placeholder slots plus 36 real player slots.
# Both sets must be inert and invisible, in the CLIENT and on the SERVER.
terminal="power/V176PowerTerminalMenu.java"
modify(terminal,
 "  for(int slot=0;slot<54;slot++){",
 "  for(int slot=0;slot<slots.size();slot++){")
modify(terminal,
 "   slots.set(slot,new Slot(slots.get(slot).container,index,-100,-100){",
 "   slots.set(slot,new Slot(slots.get(slot).container,slots.get(slot).getContainerSlot(),-10000,-10000){")
modify(terminal,
 "    @Override public boolean mayPickup(Player player){return false;}",
 """    @Override public boolean mayPickup(Player player){return false;}
    @Override public boolean isActive(){return false;}""")
modify(terminal,
 " @Override public ItemStack quickMoveStack(Player player,int slot){",
 """ @Override public void clicked(int slotId,int button,
        net.minecraft.world.inventory.ContainerInput input,Player player){
  // Monitor contains no inventory: block PICKUP, QUICK_MOVE, SWAP, THROW,
  // CLONE, PICKUP_ALL and drag actions. Never mutate the carried item.
  return;
 }
 @Override public ItemStack quickMoveStack(Player player,int slot){""")

screen="client/V176PowerMonitorScreen.java"
# ContainerScreen.imageHeight is final in Minecraft / NeoForge 26.1.
# Do not assign to it. Draw a compact monitor-only panel via local h instead.
modify(screen,
 "  int x=getLeftPos(),y=getTopPos(),h=getImageHeight();",
 "  int x=getLeftPos(),y=getTopPos(),h=124;")
modify(screen,
 """  // Real vanilla inventory slots retain the same positions as 9x6 ChestMenu.
  for(int i=0;i<36;i++){
   int sx=x+8+(i%9)*18;
   int sy=y+(i<27?139+(i/9)*18:197);
   g.fill(sx-1,sy-1,sx+18,sy+18,0xff345869);
   g.fill(sx,sy,sx+17,sy+17,0xff203746);
  }""",
 """  // No player-inventory raster. All 90 slots are inert and invisible.""")

# Fail closed: a later edit may never silently restore ghost inventory slots
# or alter the working third-person active arm pose.
v=(J/gun).read_text(encoding="utf-8")
c=(J/pose).read_text(encoding="utf-8")
assert "pose.translate(-5.0F/16.0F,2.0F/16.0F,0.0F)" in v
assert ".texOffs(12,0).addBox(-0.10F,3.50F,-2.75F,0.20F,0.25F,0.05F)" in v
assert "baseline*(1.0F-raised)-1.5707964F*raised" in c
monitor_menu=(J/terminal).read_text(encoding="utf-8")
monitor_screen=(J/screen).read_text(encoding="utf-8")
assert "for(int slot=0;slot<slots.size();slot++)" in monitor_menu
assert "isActive(){return false;}" in monitor_menu
assert "void clicked(int slotId,int button" in monitor_menu
assert "int x=getLeftPos(),y=getTopPos(),h=124;" in monitor_screen
assert "this.imageHeight=124;" not in monitor_screen
assert "Real vanilla inventory slots retain" not in monitor_screen
assert "V176BackpackMenu" not in monitor_menu
assert "V176MicroMgLayer" not in c
print("B917_FIRSTPERSON_OFF_SEQUENCE_HATCH_AND_POWER_MONITOR_NO_GHOST_SLOTS_PASS")
