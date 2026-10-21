#!/usr/bin/env python3
"""Network Elytra: FE-only glide, shift acceleration, non-breaking and craftable.

Run after the smithing-only wireless charging guard: normal tools must never
be retroactively converted to FE tools. Only one O(1) chest-slot tick check.
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
          .component(net.minecraft.core.component.DataComponents.UNBREAKABLE, net.minecraft.util.Unit.INSTANCE)
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
# Subscribe to the server player tick once. The handler checks only chest slot.
bus = "net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(dev.obsidiannetwork.wireless.WirelessPlayerCharging.class);"
assert s.count(bus)==1, "server wireless charging event registration moved"
s=s.replace(bus,bus+"\n      net.neoforged.neoforge.common.NeoForge.EVENT_BUS.register(dev.obsidiannetwork.item.NetworkElytraItem.class);",1)
mod.write_text(s, encoding="utf-8")

item = java / "item/NetworkElytraItem.java"
assert not item.exists()
item.write_text(r'''package dev.obsidiannetwork.item;

import dev.obsidiannetwork.core.EnergyTool;
import net.minecraft.core.component.DataComponents;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Unit;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;

/** 26.1 data-component glider, zero durability wear, FE-limited flight. */
public final class NetworkElytraItem extends Item {
    public static final long FLIGHT_COST_PER_5_TICKS = 125L;
    public static final long SHIFT_COST_PER_5_TICKS = 1500L;
    private static final double BOOST_ACCELERATION = 0.09D;
    private static final double BOOST_MAX_SPEED = 2.4D;

    public NetworkElytraItem(Properties properties) {
        super(properties);
    }

    // No per-world / per-network / per-inventory lookups. WirelessPlayerCharging
    // is the sole FE supply path and already scans equipment on its own schedule.
    @SubscribeEvent
    public static void onPlayerTick(PlayerTickEvent.Post event) {
        if (!(event.getEntity() instanceof ServerPlayer player)) return;
        ItemStack chest = player.getItemBySlot(EquipmentSlot.CHEST);
        if (!(chest.getItem() instanceof NetworkElytraItem)) return;
        long energy = EnergyTool.energy(chest);
        boolean hasFlightEnergy = energy >= FLIGHT_COST_PER_5_TICKS;
        // GLIDER flag gates vanilla takeoff and ongoing glide. Change it only
        // when transitioning from empty to charged or from charged to empty.
        if (!hasFlightEnergy) {
            if (chest.has(DataComponents.GLIDER)) chest.remove(DataComponents.GLIDER);
            if (player.isFallFlying()) player.stopFallFlying();
            return;
        }
        if (!chest.has(DataComponents.GLIDER))
            chest.set(DataComponents.GLIDER, Unit.INSTANCE);
        if (!player.isFallFlying()) return;
        boolean boosting = player.isShiftKeyDown() && energy >= SHIFT_COST_PER_5_TICKS;
        long charge = boosting ? SHIFT_COST_PER_5_TICKS : FLIGHT_COST_PER_5_TICKS;
        // Spend FE once per five real server ticks, not once per physics tick.
        if (player.tickCount % 5 == 0) {
            if (!EnergyTool.consume(chest, charge)) {
                if (EnergyTool.energy(chest) < FLIGHT_COST_PER_5_TICKS) {
                    chest.remove(DataComponents.GLIDER);
                    player.stopFallFlying();
                }
                return;
            }
            if (EnergyTool.energy(chest) < FLIGHT_COST_PER_5_TICKS) {
                chest.remove(DataComponents.GLIDER);
                player.stopFallFlying();
                return;
            }
        }
        if (boosting) {
            // Accelerate smoothly in facing direction, cap total speed to
            // prevent runaway velocity on large servers.
            Vec3 next = player.getDeltaMovement()
                 .add(player.getLookAngle().normalize().scale(BOOST_ACCELERATION));
            if (next.lengthSqr() > BOOST_MAX_SPEED * BOOST_MAX_SPEED)
                next = next.normalize().scale(BOOST_MAX_SPEED);
            player.setDeltaMovement(next);
            player.hasImpulse = true;
        }
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
assert "EnergyTool.consume(chest, charge)" in item.read_text()
assert "WirelessPlayerCharging" in (java / "wireless/WirelessPlayerCharging.java").read_text()
assert "if(EnergyTool.upgraded(stack))" in (java / "wireless/WirelessPlayerCharging.java").read_text()
print("NETWORK_ELYTRA_V1 PATCH PASS: recipe+registry+26.1 glider+UNBREAKABLE+FE+server Shift acceleration")
