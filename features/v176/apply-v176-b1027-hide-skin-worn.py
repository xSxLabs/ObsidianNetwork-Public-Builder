#!/usr/bin/env python3
"""B1027: only the vanilla player skin disappears while a FULL PowerArmor set
is worn. No player invisibility status, no world entity flags, no hiding armor
layers or the separate 3P/1P Micro-MG render submissions.

AvatarRenderState.TIER is extracted every frame from synchronized armor
equipment (0 when removed). A null base RenderType prevents only the
PlayerModel skin from being submitted; normal armor/equipment layers remain.
The vanilla bare first-person arm is independently suppressed.
"""
import json
import os
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])
state=(J/"client/V176AttackRenderState.java").read_text(encoding="utf-8")
assert 'state.setRenderData(TIER,tier);' in state, "B1027_MISSING_WORN_TIER_STATE"
assert 'int tier=V176MicroMgVisualClient.tier(player);' in state, "B1027_NOT_FULL_SET_GATE"
assert 'state.setRenderData(TIER,0);' in state, "B1027_MISSING_UNEQUIP_RESET"

mixin=J/"mixin/V176WornSkinRenderTypeMixin.java"
assert not mixin.exists(), "B1027_DUPLICATE_SKIN_MIXIN"
mixin.parent.mkdir(parents=True,exist_ok=True)
mixin.write_text(r'''package dev.obsidiannetwork.mixin;

import dev.obsidiannetwork.client.V176AttackRenderState;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.AvatarRenderer;
import net.minecraft.client.renderer.entity.LivingEntityRenderer;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Hide ONLY the vanilla PlayerModel texture pass, never the entire entity.
 * LivingEntityRenderer still submits all independent equipment/weapon layers.
 * Full PowerArmor set tier is read from the per-player render state on EACH
 * frame; when the armor is removed tier=0 and vanilla skin renders again.
 */
@Mixin(LivingEntityRenderer.class)
public abstract class V176WornSkinRenderTypeMixin {
 @Inject(method="getRenderType",at=@At("HEAD"),cancellable=true,require=1)
 private void xsxlabs$hideWornVanillaSkin(LivingEntityRenderState state,
     boolean bodyVisible, boolean transparent, boolean glowing,
     CallbackInfoReturnable<RenderType> cir) {
  if(!((Object)this instanceof AvatarRenderer<?>))return;
  if(!(state instanceof AvatarRenderState avatar))return;
  Integer tier=avatar.getRenderData(V176AttackRenderState.TIER);
  if(tier!=null&&tier>=1&&tier<=24)
   cir.setReturnValue(null); // skip base player skin, NOT armor/render layers
 }
}
''',encoding="utf-8")

handler=J/"client/V176WornSkinClient.java"
assert not handler.exists(), "B1027_DUPLICATE_FIRST_PERSON_HANDLER"
handler.parent.mkdir(parents=True,exist_ok=True)
handler.write_text(r'''package dev.obsidiannetwork.client;

import net.minecraft.client.Minecraft;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.RenderArmEvent;

/** Removes only the vanilla bare first-person arm while the suit is worn.
 * RenderHandEvent and custom Micro-MG/armored-forearm submissions stay intact.
 */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class V176WornSkinClient {
 private V176WornSkinClient(){}
 @SubscribeEvent public static void hideBareArm(RenderArmEvent event){
  var player=Minecraft.getInstance().player;
  if(player!=null&&V176MicroMgVisualClient.tier(player)>0)
   event.setCanceled(true);
 }
}
''',encoding="utf-8")

config=R/"obsidiannetwork.mixins.json"
data=json.loads(config.read_text(encoding="utf-8"))
assert "client" in data and isinstance(data["client"],list)
assert "V176WornSkinRenderTypeMixin" not in data["client"]
data["client"].append("V176WornSkinRenderTypeMixin")
config.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
assert "V176WornSkinRenderTypeMixin" in config.read_text(encoding="utf-8")
assert "if(tier!=null&&tier>=1&&tier<=24)" in mixin.read_text(encoding="utf-8")
assert "if(player!=null&&V176MicroMgVisualClient.tier(player)>0)" in handler.read_text(encoding="utf-8")
assert "cir.setReturnValue(null)" in mixin.read_text(encoding="utf-8")
print("B1027_FULL_SUIT_SKIN_HIDDEN_ON_UNEQUIP_RESTORED_1P_ARM_ONLY_ARMOR_LAYERS_PRESERVED_PASS")
