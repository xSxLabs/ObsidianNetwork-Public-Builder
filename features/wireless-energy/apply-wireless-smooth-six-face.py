#!/usr/bin/env python3
"""Ingame feedback: wall/floor/ceiling points and smooth 20Hz FE/item charging.

Runs AFTER all existing wireless runtime, GUI, point model and quick-mine
patches. Exact anchors fail closed so an upstream change cannot silently
rewrite unrelated generated Java. No forced chunks or new devices.
"""
from pathlib import Path
import json
import os

java = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork"
assets = Path(os.environ["V1_RESOURCE_ROOT"]) / "assets/obsidiannetwork"


def change(path, old, new):
    f = java / path
    current = f.read_text(encoding="utf-8")
    count = current.count(old)
    assert count == 1, f"WIRELESS_SMOOTH_6FACE anchor drift {path}: {old[:85]!r} ({count})"
    f.write_text(current.replace(old, new, 1), encoding="utf-8")


# Face normal follows the side clicked: wall/ceiling/floor all orient the point
# outward instead of treating vertical clicks as horizontal directions.
block = "block/WirelessNetworkBlock.java"
change(block,
       "import net.minecraft.world.level.block.HorizontalDirectionalBlock;",
       "import net.minecraft.world.level.block.state.properties.BlockStateProperties;")
change(block,
       "public static final Property<Direction> FACING=HorizontalDirectionalBlock.FACING;",
       "public static final Property<Direction> FACING=BlockStateProperties.FACING;")
change(block,
       "registerDefaultState(stateDefinition.any().setValue(FACING,Direction.NORTH));",
       "registerDefaultState(stateDefinition.any().setValue(FACING,Direction.UP));")
change(block,
       "return defaultBlockState().setValue(FACING,context.getHorizontalDirection().getOpposite());",
       "return defaultBlockState().setValue(FACING,context.getClickedFace());")

# The authored point geometry has its bottom attached at Y=0 and glows at
# Y=16. Rotate the entire model to match the six directional block states.
# Ingame #267: north/south X rotations were reversed; other four faces verified correct.
rotations = {
    "facing=up": {},
    "facing=down": {"x": 180},
    "facing=north": {"x": 90},
    "facing=south": {"x": 270},
    "facing=east": {"x": 90, "y": 90},
    "facing=west": {"x": 90, "y": 270},
}
for slug in ("network_transmitter", "network_receiver"):
    f = assets / "blockstates" / (slug + ".json")
    root = json.loads(f.read_text(encoding="utf-8"))
    variants = root.get("variants")
    assert isinstance(variants, dict) and set(variants) == {
        "facing=north", "facing=east", "facing=south", "facing=west"
    }, f"Unexpected four-face blockstates: {slug}"
    models = {value.get("model") for value in variants.values()}
    assert models == {"obsidiannetwork:block/" + slug}
    root["variants"] = {
        facing: {"model": "obsidiannetwork:block/" + slug, **rotation}
        for facing, rotation in rotations.items()
    }
    f.write_text(json.dumps(root, indent=2) + "\n", encoding="utf-8")

# Receiver runs every server tick, transferring a bounded 64k FE each tick
# instead of one 320k burst every fifth tick (same nominal 64k FE/t).
# Existing rollback-safe transactions and lazy one-sender-index-walk remain.
entity = "blockentity/WirelessNetworkBlockEntity.java"
change(entity,
       "if(!(level instanceof ServerLevel server)||be.transmitter||server.getGameTime()%5!=0)return;",
       "if(!(level instanceof ServerLevel server)||be.transmitter)return;")
change(entity,
       "int remainingBudget=MAX_TRANSFER;",
       "// Smooth, bounded per-tick delivery: 64k FE/t, not 320k each five ticks.\n"
       "  int remainingBudget=Math.min(MAX_TRANSFER,64000);")
change(entity,
       "remainingSupply=(int)Math.min(MAX_TRANSFER,WirelessEnergyRuntime.available(server.getServer(),be.networkId));",
       "remainingSupply=(int)Math.min(remainingBudget,WirelessEnergyRuntime.available(server.getServer(),be.networkId));")

# Ingame inventory charging formerly fired every 20 ticks and supplied only
# 16k FE each SECOND. Keep the single inventory/armor/Curios pass, FE
# conservation, distinct category toggles and shared player budget, but
# charge each tick with at most 64k FE per player each tick.
charging = "wireless/WirelessPlayerCharging.java"
change(charging,
       "private static final int MAX_PER_PLAYER_TICK=16000;",
       "private static final int MAX_PER_PLAYER_TICK=64000;")
change(charging,
       "if(!(event.getEntity() instanceof ServerPlayer player)||player.level().getGameTime()%20!=0)return;",
       "if(!(event.getEntity() instanceof ServerPlayer player))return;")

print("WIRELESS_SIX_FACE_V1 PASS; WIRELESS_SMOOTH_64K_FE_PER_TICK_V1 PASS; WIRELESS_CHARGE_64K_FE_PER_PLAYER_TICK_V1 PASS")
