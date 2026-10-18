#!/usr/bin/env python3
"""CI-only real two-JVM SavedData persistence and network isolation for wireless.

Apply AFTER apply-wireless-dedicated-restart-probe.py and BEFORE the existing
restart integration runner. Does not modify production Java or ship test hooks.

Seed private records via reflection solely because the dedicated offline test
has no ServerPlayer, unlike the normal owner-authorized creation path. The
SavedData actual disk codec and selection/FE runtime are still exercised.
"""
from pathlib import Path

probe=Path("tests/integration/ItemConduitRestartProbe.java")
s=probe.read_text()

def change(old,new):
 global s
 assert s.count(old)==1, f"Wireless private restart anchor drift: {old[:120]}"
 s=s.replace(old,new,1)

change(
 "    private static final long WIRELESS_FUNDED_FE = 12000L;",
 """    private static final long WIRELESS_FUNDED_FE = 12000L;
    private static final String WIRELESS_PRIVATE_ID = "d94b0ba5-333a-49ce-b216-dedicatednetwork001";
    private static final String WIRELESS_OTHER_ID = "d94b0ba5-333a-49ce-b216-dedicatednetwork002";
    private static final String WIRELESS_OWNER_1 = "4f69e184-54f5-4ee2-8898-09b08dd65210";
    private static final String WIRELESS_OWNER_2 = "cd98529b-d79b-4a93-a6dd-b3f4a92b7a61";
    private static boolean wirelessIsolationVerified;""")

change(
 '        check(source.networkId().equals("obsidiannetwork:main"),',
 '        check(source.networkId().equals(WIRELESS_PRIVATE_ID),')

change(
 '        for (int x=24;x<=28;x++)level.setBlock(new BlockPos(x,Y,24),Blocks.AIR.defaultBlockState(),3);',
 '''        seedPrivateNetworkRecords(level);
        for (int x=24;x<=28;x++)level.setBlock(new BlockPos(x,Y,24),Blocks.AIR.defaultBlockState(),3);''')

change(
 '''        var source=wirelessSource(level);
        try(var tx=net.neoforged.neoforge.transfer.transaction.Transaction.openRoot()) {''',
 '''        var source=(dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity)level.getBlockEntity(WIRELESS_TX);
        check(source!=null&&source.isTransmitter(),"WIRELESS private transmitter initial placement");
        source.selectNetwork(WIRELESS_PRIVATE_ID);
        check(source.networkId().equals(WIRELESS_PRIVATE_ID),"WIRELESS private transmitter selection");
        try(var tx=net.neoforged.neoforge.transfer.transaction.Transaction.openRoot()) {''')

change(
 '        report.put("wireless_fe_initial",WIRELESS_FUNDED_FE);',
 '''        report.put("wireless_fe_initial",WIRELESS_FUNDED_FE);
        report.put("wireless_private_networks_initial",2);
        report.put("wireless_private_source_id",source.networkId());''')

change(
 '''        var source=wirelessSource(level);
        check(source.stored()==WIRELESS_FUNDED_FE,
              "WIRELESS FE was not reloaded from the persisted disk world");''',
 '''        verifyPrivateNetworkRecords(level);
        var source=wirelessSource(level);
        check(source.stored()==WIRELESS_FUNDED_FE,
              "WIRELESS FE was not reloaded from the persisted disk world");''')

change(
 '''            level.getServer(),"obsidiannetwork:main");''',
 '''            level.getServer(),WIRELESS_PRIVATE_ID);''')

change(
 '''        check(receiver instanceof dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity,
              "WIRELESS receiver absent in second dedicated-server process");''',
 '''        check(receiver instanceof dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity,
              "WIRELESS receiver absent in second dedicated-server process");
        var receiverBe=(dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity)receiver;
        receiverBe.selectNetwork(WIRELESS_OTHER_ID);
        check(receiverBe.networkId().equals(WIRELESS_OTHER_ID),
              "WIRELESS isolated receiver failed to select other private network");''')

change(
 '''        report.put("wireless_fe_conserved",true);
        System.out.println("WIRELESS_DEDICATED_PROCESS_RESTART_V1 PASS saved="+WIRELESS_FUNDED_FE''',
 '''        check(wirelessIsolationVerified,"WIRELESS separate networks failed isolation window");
        report.put("wireless_fe_conserved",true);
        report.put("wireless_private_networks_persisted",true);
        report.put("wireless_private_network_isolation",true);
        System.out.println("WIRELESS_DEDICATED_PROCESS_RESTART_V1 PASS saved="+WIRELESS_FUNDED_FE''')

change(
 '''            if (stage == 1 && allDrained(level) &&
                (!PHASE.equals("after") || wirelessAfterTransferComplete(level))) {''',
 '''            if (stage == 1 && PHASE.equals("after")) checkWirelessPrivateIsolation(level);
            if (stage == 1 && allDrained(level) &&
                (!PHASE.equals("after") || wirelessAfterTransferComplete(level))) {''')

change(
 '    private static BlockPos source(int lane) {',
 '''    // WIRELESS_PRIVATE_NETWORK_DEDICATED_RESTART_V2: two SavedData records,
    // exact names/owner UUIDs/toggle masks, and real network isolation across JVMs.
    private static void seedPrivateNetworkRecords(ServerLevel level) {
        var data=dev.obsidiannetwork.wireless.WirelessNetworkData.get(level.getServer());
        try {
            var field=dev.obsidiannetwork.wireless.WirelessNetworkData.class.getDeclaredField("networks");
            field.setAccessible(true);
            @SuppressWarnings("unchecked")
            var networks=(java.util.Map<String,dev.obsidiannetwork.wireless.WirelessNetworkData.Entry>)field.get(data);
            check(data.find(WIRELESS_PRIVATE_ID)==null&&data.find(WIRELESS_OTHER_ID)==null,
                "WIRELESS expected clean private network fixtures");
            networks.put(WIRELESS_PRIVATE_ID,new dev.obsidiannetwork.wireless.WirelessNetworkData.Entry(
                WIRELESS_PRIVATE_ID,"Private Solar Alpha",WIRELESS_OWNER_1,17));
            networks.put(WIRELESS_OTHER_ID,new dev.obsidiannetwork.wireless.WirelessNetworkData.Entry(
                WIRELESS_OTHER_ID,"Private Machine Beta",WIRELESS_OWNER_2,6));
            data.setDirty();
            verifyPrivateNetworkRecords(level);
        } catch (ReflectiveOperationException failure) {
            throw new IllegalStateException("WIRELESS test fixture cannot seed actual SavedData",failure);
        }
    }
    private static void verifyPrivateNetworkRecords(ServerLevel level) {
        var data=dev.obsidiannetwork.wireless.WirelessNetworkData.get(level.getServer());
        var one=data.find(WIRELESS_PRIVATE_ID);
        var two=data.find(WIRELESS_OTHER_ID);
        check(one!=null&&two!=null,"WIRELESS private SavedData network IDs did not persist");
        check(one.name().equals("Private Solar Alpha")&&one.owner().equals(WIRELESS_OWNER_1)
            &&one.chargingMask()==17,
            "WIRELESS first private network name/owner/category-mask persistence failed");
        check(two.name().equals("Private Machine Beta")&&two.owner().equals(WIRELESS_OWNER_2)
            &&two.chargingMask()==6,
            "WIRELESS second private network name/owner/category-mask persistence failed");
        check(data.entries().size()>=3,"WIRELESS two private networks and Main must coexist");
        if(PHASE.equals("after")){
            report.put("wireless_private_saveddata_verified",true);
            System.out.println("WIRELESS_PRIVATE_SAVEDDATA_RESTART_V2 PASS");
        }
    }
    private static void checkWirelessPrivateIsolation(ServerLevel level) {
        if(wirelessIsolationVerified || ticks-stageStart<20)return;
        var source=wirelessSource(level);
        var sink=(dev.obsidiannetwork.blockentity.EnergyCellBlockEntity)level.getBlockEntity(WIRELESS_CELL);
        check(sink!=null,"WIRELESS private network sink missing during isolation");
        check(source.stored()==WIRELESS_FUNDED_FE && sink.stored()==0,
            "WIRELESS FE leaked between two different private networks");
        var receiver=(dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity)level.getBlockEntity(WIRELESS_RX);
        check(receiver!=null,"WIRELESS private receiver missing during isolation");
        receiver.selectNetwork(WIRELESS_PRIVATE_ID);
        check(receiver.networkId().equals(WIRELESS_PRIVATE_ID),
            "WIRELESS receiver cannot rebind to saved private network");
        wirelessIsolationVerified=true;
        System.out.println("WIRELESS_PRIVATE_NETWORK_ISOLATION_V2 PASS");
    }

    private static BlockPos source(int lane) {''')

probe.write_text(s)
print("WIRELESS_PRIVATE_NETWORK_DEDICATED_RESTART_V2 INJECTED")
