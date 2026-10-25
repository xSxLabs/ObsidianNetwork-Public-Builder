#!/usr/bin/env python3
"""v1.7.3: accept NETWORK-only conduit bundles on both Network devices.

The signal bridge already defines the authoritative NETWORK cable predicate.
The Printer/Hologram device must use exactly that predicate, otherwise a
NETWORK conductor inside a cable bundle is incorrectly reported OFFLINE.
ENERGY and other conduit layers must NOT be treated as storage networks.
"""
import os
from pathlib import Path

root = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork"
device = root / "blockentity/NetworkDeviceBlockEntity.java"
bridge = root / "network/NetworkSignalRelayBridge.java"
s = device.read_text(encoding="utf-8")
b = bridge.read_text(encoding="utf-8")

old = "if(!world.hasChunkAt(p)||!world.getBlockState(p).is(ObsidianNetwork.NETWORK_CABLE.get()))continue;"
new = ("// V173_MACHINE_NETWORK_BUNDLE: one strict NETWORK-only check for Printer/Hologram.\n"
       "   if(!dev.obsidiannetwork.network.NetworkSignalRelayBridge.networkWire(world,p))continue;")
assert s.count(old) == 1, ("unexpected Network Device cable predicate",s.count(old))
assert "public static boolean networkWire(ServerLevel level,BlockPos at)" in b
assert "state.is(ObsidianNetwork.NETWORK_CABLE.get())" in b
assert "state.is(ObsidianNetwork.CONDUIT_BUNDLE.get())" in b
assert "ConduitBundleBlockEntity.Layer.NETWORK" in b
assert "ConduitBundleBlockEntity.Layer.ENERGY" not in b
device.write_text(s.replace(old,new,1),encoding="utf-8")
assert device.read_text(encoding="utf-8").count("V173_MACHINE_NETWORK_BUNDLE") == 1
print("V173_MACHINE_NETWORK_BUNDLE_PASS: Printer/Hologram accept bundled NETWORK wire, never FE-only")
