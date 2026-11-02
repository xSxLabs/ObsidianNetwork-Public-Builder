#!/usr/bin/env python3
"""B843: wearable right-arm attack pose at model setup time, not an obsolete pre-render rotation.

NeoForge 26.1 recomputes HumanoidModel.setupAnim after the render pre-event.
Inject at TAIL on the CLIENT and apply to the player and copied armor rig.
Never change suit recall/entry animation, offhand, or non-attack modes.
"""
import os,json
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])
visual=J/"client/V176MicroMgVisualClient.java"
s=visual.read_text(encoding="utf-8")
needle=""" private static int tier(LivingEntity entity){"""
assert s.count(needle)==1,("B843_TIER_METHOD_DRIFT",s.count(needle))
s=s.replace(needle,""" /** Shared gate for the final 26.1 client model animation; never aim other players or modes. */
 public static boolean armedForAttack(Player player){
  ItemStack chest=player.getItemBySlot(EquipmentSlot.CHEST);
  return tier(player)>0 && has(chest,"micro_mg") && has(chest,"micro_mg_on");
 }
"""+needle,1)
needle="""  event.getRenderState().rightArmPose=HumanoidModel.ArmPose.BLOCK;"""
assert s.count(needle)==1,("B843_OLD_PRE_POSE_DRIFT",s.count(needle))
s=s.replace(needle,"""  // The real final arm rotation is applied AFTER HumanoidModel.setupAnim by
  // V176AttackRightArmMixin. Keep the vanilla arm pose neutral here.
  event.getRenderState().rightArmPose=HumanoidModel.ArmPose.EMPTY;""",1)
# Player post-render pose stack is at entity origin, while the humanoid
# arm ModelPart has a local origin relative to the 24px-high model.
# Correct only worn-post submission, never the ArmorStand's pose stack.
needle="""   drawArm(event.getPoseStack(),event.getSubmitNodeCollector(),
      event.getRenderState().lightCoords,model.rightArm,tier,amount);"""
assert s.count(needle)==1,("B843_WORN_POST_BARREL_DRIFT",s.count(needle))
s=s.replace(needle,"""   event.getPoseStack().pushPose();
   // RenderPlayerEvent.Post is relative to the player's FEET. Lift the
   // isolated upper-arm barrel to player shoulder coordinates.
   event.getPoseStack().translate(0.0F,1.35F,0.0F);
   drawArm(event.getPoseStack(),event.getSubmitNodeCollector(),
      event.getRenderState().lightCoords,model.rightArm,tier,amount);
   event.getPoseStack().popPose();""",1)
visual.write_text(s,encoding="utf-8")
source=J/"mixin/V176AttackRightArmMixin.java"
assert not source.exists(),("B843_MIXIN_ALREADY_EXISTS",str(source))
source.parent.mkdir(parents=True,exist_ok=True)
source.write_text("""package dev.obsidiannetwork.mixin;

import dev.obsidiannetwork.client.V176MicroMgVisualClient;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.renderer.entity.state.HumanoidRenderState;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.world.entity.player.Player;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * Pose the actual right arm in the humanoid animation that player AND
 * armor rendering consumes. RenderPlayerEvent.Pre ran too early and was
 * overwritten by setupAnim. This tail injection also handles armor models.
 */
@Mixin(HumanoidModel.class)
public abstract class V176AttackRightArmMixin {
 @Shadow @Final public ModelPart rightArm;

 @Inject(method="setupAnim(Lnet/minecraft/client/renderer/entity/state/HumanoidRenderState;)V", at=@At("TAIL"))
 private void xsxlabs$forwardArmedRightArm(HumanoidRenderState state,CallbackInfo callback){
  if(!(state instanceof AvatarRenderState avatar))return;
  Minecraft mc=Minecraft.getInstance();
  if(mc.level==null)return;
  var entity=mc.level.getEntity(avatar.id);
  if(!(entity instanceof Player player) || !V176MicroMgVisualClient.armedForAttack(player))return;
  // Approx. 88deg forward. The left arm, both legs and the base suit
  // animations remain untouched. Rotation is rebuilt every render frame.
  rightArm.xRot=-1.535F;
  rightArm.yRot=0.0F;
  rightArm.zRot=0.0F;
 }
}
""",encoding="utf-8")
mx=R/"obsidiannetwork.mixins.json"
data=json.loads(mx.read_text(encoding="utf-8"))
assert data.get("package")=="dev.obsidiannetwork.mixin",("B843_MIXIN_PACKAGE_DRIFT",data.get("package"))
client=data.setdefault("client",[])
assert "V176AttackRightArmMixin" not in client,("B843_DUPLICATE_MIXIN",client)
client.append("V176AttackRightArmMixin")
mx.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
assert "armedForAttack(Player player)" in s and "translate(0.0F,1.35F,0.0F)" in s
print("V176_B843_RIGHT_ARM_SETUP_ANIM_AND_WORN_BARREL_ORIGIN PASS")
