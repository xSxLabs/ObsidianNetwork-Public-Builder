#!/usr/bin/env python3
"""B917: fix first-person right-arm/barrel axis, OFF sequencing, black hatch,
and invisible Backpack inventory hit targets. Runs AFTER B915.
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
 "  if(hatchOpen>0.001F){",
 "  if(hatchOpen>0.001F&&hatchOpen<0.999F){")

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

# The ChestMenu carries 36 real player slots even when the backpack only
# displays storage search/list and four modules. Move all 36 client targets
# away from the GUI and make them unclickable; server rejects their IDs too.
screen="client/V176BackpackScreen.java"
modify(screen,
 "   searchBox=new net.minecraft.client.gui.components.EditBox(",
 """   for(int i=54;i<this.menu.slots.size();i++){
    var original=this.menu.getSlot(i);
    this.menu.slots.set(i,new net.minecraft.world.inventory.Slot(
        original.container,original.getContainerSlot(),-10000,-10000){
     @Override public boolean mayPlace(net.minecraft.world.item.ItemStack stack){return false;}
     @Override public boolean mayPickup(net.minecraft.world.entity.player.Player player){return false;}
     @Override public boolean isActive(){return false;}
    });
   }
   searchBox=new net.minecraft.client.gui.components.EditBox(""")

menu="backpack/V176BackpackMenu.java"
modify(menu,
 " @Override public void clicked(int slotId,int button,ContainerInput type,Player player){",
 """ @Override public void clicked(int slotId,int button,ContainerInput type,Player player){
  // The 36 inherited ChestMenu player slots are NOT part of the Backpack UI.
  // Block regular clicks, shift-click, swap, throw and clone authoritatively.
  if(slotId>=54&&slotId<this.slots.size())return;""")
modify(menu,
 " @Override public ItemStack quickMoveStack(Player p,int index){",
 """ @Override public ItemStack quickMoveStack(Player p,int index){
  if(index>=54)return ItemStack.EMPTY;""")

# Fail closed: a later edit may never silently restore ghost inventory slots
# or alter the working third-person active arm pose.
v=(J/gun).read_text(encoding="utf-8")
c=(J/pose).read_text(encoding="utf-8")
m=(J/menu).read_text(encoding="utf-8")
scr=(J/screen).read_text(encoding="utf-8")
assert "pose.translate(-5.0F/16.0F,2.0F/16.0F,0.0F)" in v
assert "if(hatchOpen>0.001F&&hatchOpen<0.999F)" in v
assert "baseline*(1.0F-raised)-1.5707964F*raised" in c
assert "if(slotId>=54&&slotId<this.slots.size())return;" in m
assert "if(index>=54)return ItemStack.EMPTY;" in m
assert "original.getContainerSlot(),-10000,-10000" in scr
assert "V176MicroMgLayer" not in c
print("B917_FIRSTPERSON_SHARED_ARM_GUN_AXIS_OFF_SEQUENCE_NO_BLACK_PANEL_NO_GHOST_INVENTORY_PASS")
