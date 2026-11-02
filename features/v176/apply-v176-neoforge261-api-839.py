#!/usr/bin/env python3
"""Fix exact NeoForge/Minecraft 26.1 APIs diagnosed by build 835.

Executes after all v1.7.6 scripts. Fails closed if source no longer matches.
Preserves feature behavior: world clock sleep skip, actionbar, GUI clicks,
the backpack's facing state and the compressed cobblestone/magnet items.
"""
import os
from pathlib import Path

ROOT=Path(os.environ.get("V1_SOURCE_ROOT","work/src/main/java"))/"dev/obsidiannetwork"

def change(rel,old,new,n=1):
    p=ROOT/rel
    code=p.read_text(encoding="utf-8")
    actual=code.count(old)
    assert actual==n,(rel,"NeoForge26.1 API source drift",actual,n,old[:100])
    code=code.replace(old,new,n)
    p.write_text(code,encoding="utf-8")
    print("B839_NE0FORGE261_API",rel,"x",n)

change("backpack/NetworkBackpackBlock.java",
       "import net.minecraft.world.level.block.state.properties.DirectionProperty;",
       "import net.minecraft.world.level.block.state.properties.EnumProperty;")
change("backpack/NetworkBackpackBlock.java",
       "public static final DirectionProperty FACING=BlockStateProperties.HORIZONTAL_FACING;",
       "public static final EnumProperty<Direction> FACING=BlockStateProperties.HORIZONTAL_FACING;")

change("power/V176PowerMonitorCommands.java",
       '''if(!done)p.displayClientMessage(Component.literal(
                      "Power Monitor: device unavailable or not on this network"),true);''',
       '''if(!done)p.connection.send(new net.minecraft.network.protocol.game.ClientboundSetActionBarTextPacket(Component.literal(
                      "Power Monitor: device unavailable or not on this network")));''')

change("powerarmor/V176PowerSleepServer.java",
       "Math.floorMod(w.getDayTime(),24000L)",
       "Math.floorMod(w.getOverworldClockTime(),24000L)")
change("powerarmor/V176PowerSleepServer.java",
       "!p.isInWaterOrBubble()",
       "!p.isInWater()&&!p.level().getBlockState(p.blockPosition()).is(net.minecraft.world.level.block.Blocks.BUBBLE_COLUMN)")
change("powerarmor/V176PowerSleepServer.java",
       '''long day=world.getDayTime();
  world.setDayTime(Math.multiplyExact(Math.addExact(Math.floorDiv(day,24000L),1L),24000L));''',
       '''// NeoForge 26.1: daylight belongs to the world's default clock, not ServerLevel.
  world.dimensionType().defaultClock().ifPresent(clock ->
      world.clockManager().moveToTimeMarker(
        clock,net.minecraft.world.clock.ClockTimeMarkers.WAKE_UP_FROM_SLEEP));''')

for screen,coords in (
    ("client/V176PowerMonitorScreen.java",("mouseX","mouseY")),
    ("client/V176BackpackScreen.java",("mx","my")),
):
    x,y=coords
    change(screen,
           f"@Override public boolean mouseClicked(double {x},double {y},int button){{",
           f"@Override public boolean mouseClicked(net.minecraft.client.input.MouseButtonEvent event,boolean doubleClick){{\n"
           f"  double {x}=event.x(),{y}=event.y(); int button=event.button();")
    change(screen,
           f"return super.mouseClicked({x},{y},button);",
           "return super.mouseClicked(event,doubleClick);")

main="ObsidianNetwork.java"
for name,max_stack in (("compressed_cobblestone_1x",64),("compressed_cobblestone_3x",64),("network_backpack_magnet_upgrade",1)):
    change(main,
           f'ITEMS.registerSimpleItem("{name}",new net.minecraft.world.item.Item.Properties().stacksTo({max_stack}));',
           f'ITEMS.registerSimpleItem("{name}",() -> new net.minecraft.world.item.Item.Properties().stacksTo({max_stack}));')

print("B839_NEOFORGE261_COMPILE_COMPATIBILITY_PATCH PASS")
