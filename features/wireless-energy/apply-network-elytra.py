#!/usr/bin/env python3
"""Network Elytra: FE-only glide, shift acceleration, non-breaking and craftable.

Run after the smithing-only wireless charging guard: normal tools must never
be retroactively converted to FE tools. No world scans or extra tick handlers.
"""
from pathlib import Path
import os, json

java = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork"
res = Path(os.environ["V1_RESOURCE_ROOT"])
mod = java / "ObsidianNetwork.java"
s = mod.read_text(encoding="utf-8")
marker = "XSXLABS_NETWORK_ELYTRA_V1"
assert marker not in s, "network elytra already patched"
anchor = '   public static final DeferredItem<BlockItem> NETWORK_RECEIVER_ITEM = ITEMS.registerSimpleBlockItem("network_receiver", NETWORK_RECEIVER);'
assert s.count(anchor) == 1, "wireless item registry moved"
registration = '''
   // XSXLABS_NETWORK_ELYTRA_V1: explicitly energy-marked by default.
   // Elytra's EQUIPPABLE and GLIDER components preserve vanilla wearing/gliding.
   public static final DeferredItem<dev.obsidiannetwork.item.NetworkElytraItem> NETWORK_ELYTRA = ITEMS.registerItem(
      "network_elytra", p -> new dev.obsidiannetwork.item.NetworkElytraItem(
         p.durability(2000000)
          .component(net.minecraft.core.component.DataComponents.EQUIPPABLE,
              net.minecraft.world.item.Items.ELYTRA.components().get(net.minecraft.core.component.DataComponents.EQUIPPABLE))
          .component(net.minecraft.core.component.DataComponents.GLIDER, net.minecraft.util.Unit.INSTANCE)
          .component(dev.obsidiannetwork.registry.ModDataComponents.ENERGY_TOOL_FE.get(), 0L)
      )
   );
'''
s = s.replace(anchor, anchor + registration, 1)
tab = 'output.accept((ItemLike)NETWORK_RECEIVER_ITEM.get());'
assert s.count(tab) == 1, "wireless creative tab insertion moved"
s = s.replace(tab, tab + '\n            output.accept((ItemLike)NETWORK_ELYTRA.get());', 1)
mod.write_text(s, encoding="utf-8")

item = java / "item/NetworkElytraItem.java"
assert not item.exists()
item.write_text(r'''package dev.obsidiannetwork.item;

import dev.obsidiannetwork.core.EnergyTool;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ElytraItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

/**
 * Energy powered glider. The vanilla flight callback is overridden, so no
 * durability damage is ever applied. Flight stops as soon as energy runs out.
 *
 * No world/network lookup: wireless FE arrives through WirelessPlayerCharging.
 * Movement is server-authoritative and only while the elytra is gliding.
 */
public final class NetworkElytraItem extends ElytraItem {
    public static final long FLIGHT_COST_PER_5_TICKS = 125L;
    public static final long SHIFT_COST_PER_5_TICKS = 1500L;
    private static final double BOOST_ACCELERATION = 0.09D;
    private static final double BOOST_MAX_SPEED = 2.4D;

    public NetworkElytraItem(Properties properties) {
        super(properties);
    }

    @Override
    public boolean canElytraFly(ItemStack stack, LivingEntity entity) {
        return !stack.isEmpty() && EnergyTool.upgraded(stack)
             && EnergyTool.energy(stack) >= FLIGHT_COST_PER_5_TICKS;
    }

    @Override
    public boolean elytraFlightTick(ItemStack stack, LivingEntity entity, int flightTicks) {
        boolean boosting = entity.isShiftKeyDown();
        long charge = boosting ? SHIFT_COST_PER_5_TICKS : FLIGHT_COST_PER_5_TICKS;
        if (EnergyTool.energy(stack) < charge) {
            // If the high-cost boost cannot be paid, keep normal flight if
            // affordable instead of abruptly dropping the player.
            if (EnergyTool.energy(stack) < FLIGHT_COST_PER_5_TICKS) return false;
            boosting = false;
            charge = FLIGHT_COST_PER_5_TICKS;
        }

        if (!entity.level().isClientSide()) {
            if (flightTicks % 5 == 0 && !EnergyTool.consume(stack, charge)) return false;
            // No call to ElytraItem.super.elytraFlightTick(): it would apply wear.
            if (boosting) {
                Vec3 motion = entity.getDeltaMovement();
                Vec3 look = entity.getLookAngle().normalize();
                Vec3 next = motion.add(look.scale(BOOST_ACCELERATION));
                if (next.lengthSqr() > BOOST_MAX_SPEED * BOOST_MAX_SPEED)
                    next = next.normalize().scale(BOOST_MAX_SPEED);
                entity.setDeltaMovement(next);
                entity.hasImpulse = true;
            }
        }
        return true;
    }
}
''', encoding="utf-8")

def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

put(res / "data/obsidiannetwork/recipe/network_elytra.json", {
    "type":"minecraft:crafting_shaped",
    "pattern":["RNR","BEB","RGR"],
    "key":{
        "R":"minecraft:redstone",
        "N":"minecraft:nether_star",
        "B":"obsidiannetwork:battery",
        "E":"minecraft:elytra",
        "G":"minecraft:glowstone_dust"
    },
    "result":{"id":"obsidiannetwork:network_elytra","count":1}
})
put(res / "assets/obsidiannetwork/models/item/network_elytra.json", {
    "parent":"minecraft:item/generated",
    "textures":{"layer0":"minecraft:item/elytra"}
})
put(res / "assets/obsidiannetwork/items/network_elytra.json", {
    "model":{"type":"minecraft:model","model":"obsidiannetwork:item/network_elytra"}
})
for locale,name in [("en_us","Network Elytra"),("de_de","Netzwerk-Elytra")]:
    lang=res / "assets/obsidiannetwork/lang" / (locale + ".json")
    data=json.loads(lang.read_text(encoding="utf-8"))
    data["item.obsidiannetwork.network_elytra"]=name
    put(lang,data)

assert marker in mod.read_text()
assert "EnergyTool.consume(stack, charge)" in item.read_text()
assert "WirelessPlayerCharging" in (java / "wireless/WirelessPlayerCharging.java").read_text()
assert "if(EnergyTool.upgraded(stack))" in (java / "wireless/WirelessPlayerCharging.java").read_text()
print("NETWORK_ELYTRA_V1 PATCH PASS: recipe+registry+glider+FE+shift acceleration, no extra network scans")
