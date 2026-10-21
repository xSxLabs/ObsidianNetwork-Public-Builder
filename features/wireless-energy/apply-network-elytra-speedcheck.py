#!/usr/bin/env python3
"""Build 378: scope the 26.1.2 vanilla Elytra speed-check exemption to powered Network Elytras.

The user confirmed that "minecraft:elytra_movement_check false" removes the
rubber-banding at the intended 2.4 blocks/t boost cap. Do NOT change a global
gamerule: selectively mirror that behavior solely in the player movement
listener when a real, charged Network Elytra is actively gliding.
"""
import json
import os
from pathlib import Path

j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
res=Path(os.environ["V1_RESOURCE_ROOT"])
path=j/"mixin/NetworkElytraSpeedCheckMixin.java"
config=res/"obsidiannetwork.mixins.json"
wing=j/"item/NetworkElytraItem.java"
curios=j/"wireless/NetworkElytraCurios.java"
existing=j/"mixin/NetworkElytraCuriosGlideMixin.java"
marker="XSXLABS_NETWORK_ELYTRA_SCOPED_SPEED_CHECK_V1"
assert not path.exists(), "Flight speed-check mixin already exists"
data=json.loads(config.read_text(encoding="utf-8"))
assert data.get("package")=="dev.obsidiannetwork.mixin", "Mixin package drift"
assert isinstance(data.get("mixins"),list), "Unexpected mixin configuration"
assert "NetworkElytraCuriosGlideMixin" in data["mixins"], "Previous Curios takeoff fix missing"
assert "NetworkElytraSpeedCheckMixin" not in data["mixins"]
elytra=wing.read_text(encoding="utf-8")
assert "BOOST_MAX_SPEED = 2.4D" in elytra
assert "SHIFT_COST_PER_5_TICKS = 1500L" in elytra
assert "FLIGHT_COST_PER_5_TICKS = 125L" in elytra
assert "XSXLABS_ELYTRA_GROUND_AND_TAKEOFF_GUARD_V1" in elytra
assert "CuriosApi.getCuriosInventory(player)" in curios.read_text(encoding="utf-8")
assert "XSXLABS_ELYTRA_GROUND_AND_TAKEOFF_GUARD_V1" in existing.read_text(encoding="utf-8")

source=r'''package dev.obsidiannetwork.mixin;

import dev.obsidiannetwork.core.EnergyTool;
import dev.obsidiannetwork.item.NetworkElytraItem;
import dev.obsidiannetwork.wireless.NetworkElytraCurios;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.ServerGamePacketListenerImpl;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import net.neoforged.fml.ModList;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * XSXLABS_NETWORK_ELYTRA_SCOPED_SPEED_CHECK_V1
 * Only the vanilla Elytra speed-check *decision* is relaxed during legitimate
 * powered Network Elytra flight. Keep game rules unchanged for the world and
 * for all other players; do not affect collision, finite-position, vehicles,
 * on-foot movement, chunk limits, flight start, FE drain, or landing.
 *
 * Minecraft/NeoForge 26.1.2: shouldCheckPlayerMovement(boolean isFallFlying).
 */
@Mixin(ServerGamePacketListenerImpl.class)
public abstract class NetworkElytraSpeedCheckMixin {
    @Shadow ServerPlayer player;

    @Inject(method="shouldCheckPlayerMovement", at=@At("RETURN"),
            cancellable=true, require=1)
    private void xsxNetworkElytraSpeedCheck(boolean isFallFlying,
            CallbackInfoReturnable<Boolean> result) {
        // Leave every vanilla decision intact except the powered Network Elytra.
        if (!isFallFlying || !result.getReturnValueZ()) return;
        ServerPlayer p = this.player;
        if (p == null || !p.isFallFlying() || p.onGround()) return;

        ItemStack wing = p.getItemBySlot(EquipmentSlot.CHEST);
        if (!(wing.getItem() instanceof NetworkElytraItem)) {
            if (!ModList.get().isLoaded("curios")) return;
            wing = NetworkElytraCurios.find(p);
        }
        if (!(wing.getItem() instanceof NetworkElytraItem)) return;
        if (EnergyTool.energy(wing) < NetworkElytraItem.FLIGHT_COST_PER_5_TICKS) return;

        // Never exempt malformed or implausibly fast server-side velocity.
        // The boost implementation itself hard-caps at 2.4 blocks/tick.
        Vec3 motion = p.getDeltaMovement();
        if (!Double.isFinite(motion.x) || !Double.isFinite(motion.y) ||
            !Double.isFinite(motion.z) || motion.lengthSqr() > 6.76D) return;

        // Equivalent to the working gamerule workaround, but ONLY for this
        // player's currently powered Network Elytra flight.
        result.setReturnValue(false);
    }
}
'''
assert source.count(marker)==1
assert 'method="shouldCheckPlayerMovement"' in source
assert "setReturnValue(false)" in source
assert "getGameRules(" not in source and "GameRules." not in source, "Do not mutate GameRules"
# Publish only after all source/asset validation has succeeded.
path.write_text(source,encoding="utf-8")
data["mixins"].append("NetworkElytraSpeedCheckMixin")
config.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
print("NETWORK_ELYTRA_SCOPED_SPEED_CHECK_V1 PASS: only powered Elytra fall-flying bypasses vanilla speed gate; normal movement and gamerules untouched")
