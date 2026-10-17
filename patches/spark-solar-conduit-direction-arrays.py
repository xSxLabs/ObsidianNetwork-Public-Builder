#!/usr/bin/env python3
"""Remove per-tick/per-node Direction.values() array clones in Spark hot paths.

Direction values are immutable enums, the two arrays are private and read-only
in these traversals. Never change energy accounting, capability checks,
transactions, round-robin order, or topology validation. Fail closed and
validate both source files before any write.
"""
import os
from pathlib import Path

root = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork"
solar = root / "blockentity/SolarGeneratorBlockEntity.java"
conduit = root / "conduit/EnergyConduitTicker.java"
s = solar.read_text(encoding="utf-8")
c = conduit.read_text(encoding="utf-8")
marker_s = "XSXLABS_SPARK_SOLAR_STATIC_DIRECTIONS_V1"
marker_c = "XSXLABS_SPARK_CONDUIT_STATIC_DIRECTIONS_V1"
assert marker_s not in s and marker_c not in c, "Directions patch already present"

def require_exact(source, needle, count=1):
    assert source.count(needle) == count, f"Source drift: {needle[:80]} count={source.count(needle)}"

solar_cls = "public final class SolarGeneratorBlockEntity extends BlockEntity {"
conduit_cls = "public final class EnergyConduitTicker implements ConduitTicker {"
require_exact(s, solar_cls)
require_exact(s, "Direction[] sides = Direction.values();")
require_exact(s, "int start = be.nextSide++ % sides.length;")
require_exact(s, "Direction side = sides[(start + off) % sides.length];")
require_exact(s, "server.getCapability(Energy.BLOCK, pos.relative(side), side.getOpposite())")
require_exact(s, "be.energyJournal.updateSnapshots(tx);")
require_exact(s, "tx.commit();")
require_exact(s, "budget -= accepted;")
require_exact(s, "server.canSeeSky(pos.above())")
# All other code including capability and root transactions stays byte-identical.
s = s.replace(solar_cls, solar_cls + "\n   // " + marker_s + "\n   private static final Direction[] SOLAR_SCAN_SIDES = Direction.values();", 1)
s = s.replace("Direction[] sides = Direction.values();", "Direction[] sides = SOLAR_SCAN_SIDES;", 1)

require_exact(c, conduit_cls)
require_exact(c, "for(net.minecraft.core.Direction d:net.minecraft.core.Direction.values())")
require_exact(c, "for(var node:network.nodes())")
require_exact(c, "Transaction.openRoot()")
require_exact(c, "from.extract(1000,tx)")
require_exact(c, "to.insert(got,tx)")
require_exact(c, "from.insert(got-put,tx)")
require_exact(c, "tx.commit();return;")
require_exact(c, "if(connected.size()<2)return;")
c = c.replace(conduit_cls, conduit_cls + "\n // " + marker_c + "\n private static final net.minecraft.core.Direction[] CONDUIT_SCAN_SIDES = net.minecraft.core.Direction.values();", 1)
c = c.replace("for(net.minecraft.core.Direction d:net.minecraft.core.Direction.values())", "for(net.minecraft.core.Direction d:CONDUIT_SCAN_SIDES)", 1)

require_exact(s, marker_s)
require_exact(c, marker_c)
require_exact(s, "Direction.values()")
require_exact(c, "net.minecraft.core.Direction.values()")
solar.write_text(s, encoding="utf-8")
conduit.write_text(c, encoding="utf-8")
print("SPARK_SOLAR_CONDUIT_DIRECTIONS_V1 PASS: no per-tick/per-node direction array allocations")
