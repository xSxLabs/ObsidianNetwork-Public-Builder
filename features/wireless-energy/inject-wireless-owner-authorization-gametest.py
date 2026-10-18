#!/usr/bin/env python3
"""CI-only real server-side owner authorization checks with two fake ServerPlayers.

Run after the chunk life-cycle injector. FakePlayerFactory produces independent
server player UUIDs in the actual NeoForge GameTest JVM. This covers authorizing
create/list/rename/delete, per-network charge toggle, and antenna selection.
Client GUI and socket networking still require manual multiplayer acceptance.
"""
import os
from pathlib import Path

file=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/build103/Build103GameTests.java"
s=file.read_text()
anchor='''                     System.out.println("WIRELESS_REAL_CHUNK_UNLOAD_RELOAD_V1 PASS");
                   })'''
assert s.count(anchor)==1,"wireless chunk/owner test anchor changed"
assert "WIRELESS_SERVER_TWO_OWNER_AUTHORIZATION_V1" not in s
addition=r'''
                   .thenExecuteAfter(2,()->{
                     // Distinct real server-side player identities, without a
                     // client or network connection. Never shipped in the JAR.
                     var level=helper.getLevel();
                     var a=net.neoforged.neoforge.common.util.FakePlayerFactory.get(
                      level,new com.mojang.authlib.GameProfile(
                       java.util.UUID.fromString("22130b0e-1c47-4bc4-822a-a78c5f61ea01"),"WirelessA"));
                     var b=net.neoforged.neoforge.common.util.FakePlayerFactory.get(
                      level,new com.mojang.authlib.GameProfile(
                       java.util.UUID.fromString("22130b0e-1c47-4bc4-822a-a78c5f61ea02"),"WirelessB"));
                     check(!a.getUUID().equals(b.getUUID()),"WIRELESS distinct server owners");
                     var storage=dev.obsidiannetwork.wireless.WirelessNetworkData.get(level.getServer());
                     var owned=storage.create(a,"GameTest Private A");
                     check(owned!=null,"WIRELESS owner A can create private network");
                     String id=owned.id();
                     check(storage.canAccess(a,id),"WIRELESS owner A accesses own private network");
                     check(!storage.canAccess(b,id),"WIRELESS owner B forbidden from A private network");
                     check(storage.available(b).stream().noneMatch(n->n.id().equals(id)),
                      "WIRELESS network list must not disclose a private ID to B");
                     check(!storage.setCharging(b,id,31),"WIRELESS B cannot modify A charging masks");
                     check(!storage.rename(b,id,"Stolen Network"),"WIRELESS B cannot rename A network");
                     check(!storage.delete(b,id),"WIRELESS B cannot delete A network");
                     check(storage.rename(a,id,"GameTest Renamed A"),
                      "WIRELESS A can rename network while preserving UUID");
                     check(id.equals(storage.find(id).id()) &&
                           "GameTest Renamed A".equals(storage.find(id).name()),
                      "WIRELESS stable private ID and updated name");
                     check(storage.setCharging(a,id,17),"WIRELESS A can set owned network charging");
                     check(storage.find(id).chargingMask()==17,"WIRELESS charging toggles persisted in entry");
                     BlockPos pos=helper.absolutePos(new BlockPos(7,1,1));
                     level.setBlock(pos,ObsidianNetwork.NETWORK_TRANSMITTER.get().defaultBlockState(),3);
                     var antenna=(dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity)level.getBlockEntity(pos);
                     check(antenna!=null&&antenna.isTransmitter(),"WIRELESS owner antenna placed");
                     antenna.markPlacedBy(a);
                     check(!antenna.canConfigure(b),"WIRELESS B cannot configure A antenna");
                     check(!antenna.selectNetworkFor(b,id),"WIRELESS B cannot select A private channel");
                     check(antenna.selectNetworkFor(a,id)&&id.equals(antenna.networkId()),
                      "WIRELESS A can bind owned antenna to own private channel");
                     // Deleting a network must revoke transfer, not erase a
                     // paid-for energy buffer on the transmitter.
                     try(var funded=net.neoforged.neoforge.transfer.transaction.Transaction.openRoot()){
                      check(antenna.energyHandler().insert(1024,funded)==1024,
                       "WIRELESS owned private sender accepts 1024 FE");
                      funded.commit();
                     }
                     check(dev.obsidiannetwork.wireless.WirelessEnergyRuntime.available(
                      level.getServer(),id)==1024,"WIRELESS private sender funds its own network");
                     check(storage.delete(a,id),"WIRELESS A can delete private network");
                     check(storage.find(id)==null,"WIRELESS deleted private network is unavailable");
                     check(antenna.stored()==1024,"WIRELESS deleting network must preserve antenna FE");
                     check(dev.obsidiannetwork.wireless.WirelessEnergyRuntime.available(
                      level.getServer(),id)==0,"WIRELESS removed private network forbids FE");
                     check(antenna.selectNetworkFor(a,
                      dev.obsidiannetwork.wireless.WirelessNetworkData.DEFAULT_ID),
                      "WIRELESS owner can rebind buffered sender to Main");
                     check(dev.obsidiannetwork.wireless.WirelessEnergyRuntime.available(
                      level.getServer(),dev.obsidiannetwork.wireless.WirelessNetworkData.DEFAULT_ID)==1024,
                      "WIRELESS preserved FE can be recovered after network deletion");
                     level.setBlock(pos,Blocks.AIR.defaultBlockState(),3);
                     System.out.println("WIRELESS_SERVER_TWO_OWNER_AUTHORIZATION_V1 PASS");
                   })'''
file.write_text(s.replace(anchor,anchor+addition,1))
print("WIRELESS_SERVER_TWO_OWNER_AUTHORIZATION_V1 INJECTED")
