#!/usr/bin/env python3
"""Extend the existing two-JVM dedicated-server item restart proof with wireless FE.

The existing restart harness uses the SAME world across separate server JVMs,
and removes the CI-only subscriber before packaging. Fail closed if the probe
or task shape changes. All existing ITEM checks remain.
"""
from pathlib import Path

probe=Path("tests/integration/ItemConduitRestartProbe.java")
source=probe.read_text()

def change(old,new):
 global source
 assert source.count(old)==1, "wireless dedicated restart anchor drift: "+old[:110]
 source=source.replace(old,new,1)

change(
 "                // Preserve explicit sparse filter slots as well as empty",
 '''                // CI-only: create a buffered wireless transmitter before
                // the first server shutdown, but NO receiver yet.
                if (PHASE.equals("before")) createWirelessBefore(level);
                else createWirelessAfter(level);
                // Preserve explicit sparse filter slots as well as empty''')

change(
 "            if (stage == 1 && allDrained(level)) {",
 '''            if (stage == 1 && allDrained(level) &&
                (!PHASE.equals("after") || wirelessAfterTransferComplete(level))) {''')

change(
 '                if (PHASE.equals("before")) finish(server, true, null);',
 '''                if (PHASE.equals("before")) {
                    verifyWirelessBeforeStop(level);
                    finish(server, true, null);
                }''')

change(
 "    private static BlockPos source(int lane) {",
 '''    // WIRELESS_DEDICATED_PROCESS_RESTART_V1
    // Fixture coordinates are inside the two-by-two test-only forced chunk square
    // but away from all existing item conduit lanes. No production chunk tickets.
    private static final BlockPos WIRELESS_TX = new BlockPos(24,Y,24);
    private static final BlockPos WIRELESS_RX = new BlockPos(27,Y,24);
    private static final BlockPos WIRELESS_CELL = new BlockPos(28,Y,24);
    private static final long WIRELESS_FUNDED_FE = 12000L;

    private static dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity wirelessSource(ServerLevel level) {
        var be=level.getBlockEntity(WIRELESS_TX);
        check(be instanceof dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity,
              "WIRELESS persisted transmitter BE absent after real process restart");
        var source=(dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity)be;
        check(source.isTransmitter(),"WIRELESS restarted device type changed");
        check(source.networkId().equals("obsidiannetwork:main"),
              "WIRELESS network identity failed across restart");
        return source;
    }
    private static void createWirelessBefore(ServerLevel level) {
        for (int x=24;x<=28;x++)level.setBlock(new BlockPos(x,Y,24),Blocks.AIR.defaultBlockState(),3);
        level.setBlock(WIRELESS_TX,ObsidianNetwork.NETWORK_TRANSMITTER.get().defaultBlockState(),3);
        var source=wirelessSource(level);
        try(var tx=net.neoforged.neoforge.transfer.transaction.Transaction.openRoot()) {
            check(source.energyHandler().insert((int)WIRELESS_FUNDED_FE,tx)==WIRELESS_FUNDED_FE,
                "WIRELESS first server failed to buffer 12000 FE");
            tx.commit();
        }
        check(source.stored()==WIRELESS_FUNDED_FE,
            "WIRELESS first server did not commit 12000 FE");
        report.put("wireless_fe_initial",WIRELESS_FUNDED_FE);
    }
    private static void verifyWirelessBeforeStop(ServerLevel level) {
        check(wirelessSource(level).stored()==WIRELESS_FUNDED_FE,
             "WIRELESS FE changed before first server save");
    }
    private static void createWirelessAfter(ServerLevel level) {
        var source=wirelessSource(level);
        check(source.stored()==WIRELESS_FUNDED_FE,
              "WIRELESS FE was not reloaded from the persisted disk world");
        check(source.isActive(),"WIRELESS loaded persisted transmitter not active");
        long indexed=dev.obsidiannetwork.wireless.WirelessEnergyRuntime.available(
            level.getServer(),"obsidiannetwork:main");
        check(indexed>=WIRELESS_FUNDED_FE,
              "WIRELESS loaded transmitter missing from post-restart registry");
        report.put("wireless_fe_persisted",true);
        report.put("wireless_fe_after_restart",source.stored());
        // Receiver exists only in the SECOND process, so any delivered FE
        // demonstrably came from the actual saved and reloaded transmitter.
        level.setBlock(WIRELESS_RX,ObsidianNetwork.NETWORK_RECEIVER.get().defaultBlockState(),3);
        level.setBlock(WIRELESS_CELL,ObsidianNetwork.BASIC_ENERGY_CELL.get().defaultBlockState(),3);
        var receiver=level.getBlockEntity(WIRELESS_RX);
        var sink=level.getBlockEntity(WIRELESS_CELL);
        check(receiver instanceof dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity,
              "WIRELESS receiver absent in second dedicated-server process");
        check(sink instanceof dev.obsidiannetwork.blockentity.EnergyCellBlockEntity,
              "WIRELESS real energy sink absent after restart");
        var cell=(dev.obsidiannetwork.blockentity.EnergyCellBlockEntity)sink;
        check(cell.stored()==0,"WIRELESS post-restart sink unexpectedly precharged");
        check(cell.sideMode(Direction.WEST)==dev.obsidiannetwork.blockentity.EnergyCellBlockEntity.SideMode.INPUT,
              "WIRELESS post-restart cell must accept FE on WEST");
    }
    private static boolean wirelessAfterTransferComplete(ServerLevel level) {
        var source=wirelessSource(level);
        var target=level.getBlockEntity(WIRELESS_CELL);
        check(target instanceof dev.obsidiannetwork.blockentity.EnergyCellBlockEntity,
              "WIRELESS sink disappeared during resumed FE transfer");
        var cell=(dev.obsidiannetwork.blockentity.EnergyCellBlockEntity)target;
        long total=source.stored()+cell.stored();
        check(total==WIRELESS_FUNDED_FE,
              "WIRELESS after-restart FE conservation failed: "+total);
        if(cell.stored()==0)return false;
        report.put("wireless_fe_received_after_restart",cell.stored());
        report.put("wireless_fe_conserved",true);
        System.out.println("WIRELESS_DEDICATED_PROCESS_RESTART_V1 PASS saved="+WIRELESS_FUNDED_FE
          +" received="+cell.stored()+" remaining="+source.stored());
        return true;
    }

    private static BlockPos source(int lane) {''')

probe.write_text(source)
print("WIRELESS_DEDICATED_PROCESS_RESTART_V1 INJECTED")
