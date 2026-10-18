#!/usr/bin/env python3
"""GameTest-only proof that unloaded/unknown network sources cannot supply FE.

Applied after the live Nether and persistence injectors; uses the same 12k
committed source. Unregister/re-register models a loaded-source index update
without touching production chunk tickets. Existing 20k FE conservation and
rollback assertions remain in place.
"""
import os
from pathlib import Path

target=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/build103/Build103GameTests.java"
s=target.read_text()
anchor='check(crossTx.stored()==12000,"WIRELESS crossdim aborted FE pull reverts Nether buffer");'
assert s.count(anchor)==1,"wireless rollback anchor changed"

extra=r'''
                     // WIRELESS_LOADED_SOURCE_ISOLATION_V1: no ghost transport and
                     // no FE destruction when a registered source is detached.
                     String validId="obsidiannetwork:main";
                     String absentId="obsidiannetwork:wireless-nonexistent";
                     crossTx.selectNetwork(absentId);
                     check(validId.equals(crossTx.networkId()),
                      "WIRELESS cannot bind a transmitter to a non-existent network ID");
                     try(var absent=net.neoforged.neoforge.transfer.transaction.Transaction.openRoot()){
                      check(dev.obsidiannetwork.wireless.WirelessEnergyRuntime.pull(
                       helper.getLevel().getServer(),absentId,1024,absent)==0,
                       "WIRELESS non-existent network cannot withdraw FE");
                     }
                     dev.obsidiannetwork.wireless.WirelessEnergyRuntime.unregister(crossTx);
                     check(dev.obsidiannetwork.wireless.WirelessEnergyRuntime.available(
                       helper.getLevel().getServer(),validId)==0,
                      "WIRELESS source detached from loaded registry is unavailable");
                     try(var detached=net.neoforged.neoforge.transfer.transaction.Transaction.openRoot()){
                      check(dev.obsidiannetwork.wireless.WirelessEnergyRuntime.pull(
                       helper.getLevel().getServer(),validId,1024,detached)==0,
                       "WIRELESS detached transmitter cannot supply FE");
                     }
                     check(crossTx.stored()==12000,
                      "WIRELESS detached transmitter retains all stored FE");
                     dev.obsidiannetwork.wireless.WirelessEnergyRuntime.register(crossTx);
                     check(dev.obsidiannetwork.wireless.WirelessEnergyRuntime.available(
                       helper.getLevel().getServer(),validId)>=12000,
                      "WIRELESS reloaded transmitter becomes available without FE loss");
                     System.out.println("WIRELESS_LOADED_SOURCE_ISOLATION_V1 PASS");
'''
s=s.replace(anchor,anchor+extra,1)
target.write_text(s)
print("WIRELESS_LOADED_SOURCE_ISOLATION_V1 INJECTED")
