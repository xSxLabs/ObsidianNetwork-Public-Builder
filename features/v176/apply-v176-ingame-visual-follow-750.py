#!/usr/bin/env python3
"""B750: ingame feedback: right weapon invisible, arm not raised, Follow sliding.

After B745. Explicit third-person arm submission is a fallback for player
renderers that reset model pose after RenderPlayerEvent.Pre. World ArmorStand
leg/arm rotations are server-authoritative and replicate to other players.
No changes to FE, bullet combat, loot or exit/recall lifecycle.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def edit(file,old,new):
 p=J/file
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("V176_B750_ANCHOR_DRIFT",file,s.count(old),old[:160])
 p.write_text(s.replace(old,new,1),encoding="utf-8")

# Make mutated item component observable to the equipment slot synchronization
# rather than relying on Java's in-place ItemStack component mutation.
edit("powerarmor/V176AttackModeServer.java",
"""  chest.set(ModDataComponents.POWER_ARMOR_UPGRADES.get(),String.join(",",list));
  message(p,active);""",
"""  chest.set(ModDataComponents.POWER_ARMOR_UPGRADES.get(),String.join(",",list));
  // Fresh slot object triggers equipment/component sync to all tracking clients.
  p.setItemSlot(EquipmentSlot.CHEST,chest.copy());
  message(p,active);""")
edit("powerarmor/V176AttackModeServer.java",
"""    clearFromChest(chest);
    message(p,false);""",
"""    clearFromChest(chest);
    p.setItemSlot(EquipmentSlot.CHEST,chest.copy());
    message(p,false);""")

# Server tick already runs every game tick; movement is applied each fifth tick.
# Drive intermediate animation frames every tick and leave the suit idle at rest.
edit("powerarmor/V176CompanionMode.java",
""" private static boolean hasModule(ArmorStand suit){""",
""" private static void walkingPose(ArmorStand suit,boolean walking,boolean turret,long time){
  float swing=walking?(float)Math.sin(time*0.72D)*24.0F:0.0F;
  // Vanilla ArmorStand limb rotations are data-watched, so multiplayer sees them.
  // Aim right arm only for active armed Turret; FOLLOW always swings both arms.
  suit.setShowArms(true);
  suit.setLeftLegPose(new net.minecraft.core.Rotations(swing,0F,0F));
  suit.setRightLegPose(new net.minecraft.core.Rotations(-swing,0F,0F));
  suit.setLeftArmPose(new net.minecraft.core.Rotations(-swing*0.75F,0F,0F));
  suit.setRightArmPose(new net.minecraft.core.Rotations(turret?-80F:swing*0.75F,0F,0F));
 }
 private static boolean hasModule(ArmorStand suit){""")
edit("powerarmor/V176CompanionMode.java",
"""  if(!was)suit.addTag(requested);
  ItemStack chest=suit.getItemBySlot(EquipmentSlot.CHEST);""",
"""  if(!was)suit.addTag(requested);
  // Stop walking/aiming as soon as a mode is switched off.
  if(was)walkingPose(suit,false,false,player.level().getGameTime());
  ItemStack chest=suit.getItemBySlot(EquipmentSlot.CHEST);""")
edit("powerarmor/V176CompanionMode.java",
"""  if(turret&&!hasModule(suit)){
   suit.removeTag(TURRET);""",
"""  // Keep limb movement separate from the five-tick position update.
  double near=suit.distanceToSqr(player);
  boolean walking=near>3.5D*3.5D && near<14D*14D;
  walkingPose(suit,walking,turret&&hasModule(suit),world.getGameTime());
  if(turret&&!hasModule(suit)){
   suit.removeTag(TURRET);""")

# This renderer's original Pre pose is not guaranteed to survive the
# renderer's own setupAnim. Submit an explicit raised RIGHT arm in Post.
# Use the actual power-armor equipment atlas rather than the gun texture
# to give the raised arm a visible armored silhouette.
edit("client/V176MicroMgVisualClient.java",
""" private static Identifier texture(int tier){""",
""" private static Identifier wornArmorTexture(int tier){
  String name=tier==1?"power_armor":"power_armor_mk"+tier;
  return Identifier.fromNamespaceAndPath("obsidiannetwork",
    "textures/entity/equipment/humanoid/"+name+".png");
 }
 private static Identifier texture(int tier){""")
edit("client/V176MicroMgVisualClient.java",
"""  if(amount>0.0F)
   drawRight(event.getPoseStack(),event.getSubmitNodeCollector(),
      event.getRenderState().lightCoords,event.getRenderer().getModel(),tier,amount,false);""",
"""  if(amount>0.0F){
   var model=event.getRenderer().getModel();
   float raised=phase(amount,0.0F,4.0F/12.0F);
   float rx=model.rightArm.xRot,ry=model.rightArm.yRot,rz=model.rightArm.zRot;
   // A renderer may reset its Pre-event arm pose. Draw the aimed arm after
   // normal rendering so visible aiming never depends on setupAnim ordering.
   model.rightArm.xRot=rx*(1F-raised)-1.40F*raised;
   model.rightArm.yRot=ry*(1F-raised);
   model.rightArm.zRot=rz*(1F-raised);
   if(raised>0.01F)
    event.getSubmitNodeCollector().submitModelPart(model.rightArm,
       event.getPoseStack(),RenderTypes.entitySolid(wornArmorTexture(tier)),
       event.getRenderState().lightCoords,OverlayTexture.NO_OVERLAY,
       null,false,false,0xFFFFFFFF,null,0);
   drawArm(event.getPoseStack(),event.getSubmitNodeCollector(),
      event.getRenderState().lightCoords,model.rightArm,tier,amount);
   model.rightArm.xRot=rx;model.rightArm.yRot=ry;model.rightArm.zRot=rz;
  }""")

# RenderHandEvent runs for HELD ITEMS too. RenderArmEvent does not.
# Keep RenderArmEvent for an empty hand to avoid duplicate gun drawings.
edit("client/V176MicroMgVisualClient.java",
"""import net.neoforged.neoforge.client.event.RenderArmEvent;""",
"""import net.neoforged.neoforge.client.event.RenderArmEvent;
import net.neoforged.neoforge.client.event.RenderHandEvent;""")
edit("client/V176MicroMgVisualClient.java",
""" @SubscribeEvent public static void worldSuit(RenderLivingEvent.Post<?,?,?> event){""",
""" @SubscribeEvent public static void firstPersonWithItem(RenderHandEvent event){
  // The original RenderArmEvent fires only when the itemless arm is rendered.
  if(event.getHand()!=net.minecraft.world.InteractionHand.MAIN_HAND
       ||event.getItemStack().isEmpty())return;
  Minecraft mc=Minecraft.getInstance();
  if(mc.player==null || !has(mc.player.getItemBySlot(EquipmentSlot.CHEST),"micro_mg")
      || !has(mc.player.getItemBySlot(EquipmentSlot.CHEST),"micro_mg_on"))return;
  int variant=tier(mc.player);
  if(variant==0)return;
  float amount=extension(mc.player.getId(),true);
  if(amount<=0F)return;
  float hatch=phase(amount,4F/12F,7F/12F);
  float barrel=phase(amount,7F/12F,1F);
  PoseStack pose=event.getPoseStack();
  pose.pushPose();
  // Camera position of right upper arm. The held item remains untouched.
  pose.translate(0.34F,-0.32F,-0.48F);
  if(hatch>0F){
   pose.pushPose();
   pose.mulPose(com.mojang.math.Axis.XP.rotationDegrees(-16F*hatch));
   event.getSubmitNodeCollector().submitModelPart(HATCH,pose,
     RenderTypes.entitySolid(texture(variant)),event.getPackedLight(),
     OverlayTexture.NO_OVERLAY,null,false,false,0xFFFFFFFF,null,0);
   pose.popPose();
  }
  if(barrel>0F){
   pose.pushPose();
   pose.translate(0F,-(1F-barrel)*0.32F,0F);
   event.getSubmitNodeCollector().submitModelPart(BARREL,pose,
     RenderTypes.entitySolid(texture(variant)),event.getPackedLight(),
     OverlayTexture.NO_OVERLAY,null,false,false,0xFFFFFFFF,null,0);
   pose.popPose();
  }
  pose.popPose();
 }
 @SubscribeEvent public static void worldSuit(RenderLivingEvent.Post<?,?,?> event){""")
edit("client/V176MicroMgVisualClient.java",
"""  if(event.getRenderState().entityType!=EntityType.ARMOR_STAND)return;""",
"""  // RenderLivingEvent has LivingEntityRenderState without an entity id.
  // The current owned world suits are vanilla ArmorStand entities.
  if(event.getRenderState().entityType!=EntityType.ARMOR_STAND)return;""")

visual=(J/"client/V176MicroMgVisualClient.java").read_text(encoding="utf-8")
mode=(J/"powerarmor/V176CompanionMode.java").read_text(encoding="utf-8")
attack=(J/"powerarmor/V176AttackModeServer.java").read_text(encoding="utf-8")
assert "model.leftArm" not in visual
assert "submitModelPart(model.rightArm" in visual
assert "firstPersonWithItem(RenderHandEvent event)" in visual
assert "walkingPose(suit,walking" in mode and "setLeftLegPose" in mode
assert "p.setItemSlot(EquipmentSlot.CHEST,chest.copy());" in attack
print("V176_B750_VISIBLE_AIM_WEAPON_AND_FOLLOW_WALK_POSES_PASS")
