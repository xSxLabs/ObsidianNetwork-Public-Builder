#!/usr/bin/env python3
"""B718: nearest owned standing suit in Action Wheel, even with multiple nearby.

Server already selects the nearest owned suit. Match its semantics on client
rather than hiding Follow/Turret whenever two of the 24 variants are in range.
"""
import os
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/client/V176CompanionClient.java"
s=p.read_text(encoding="utf-8")
old="  return stands.size()==1?stands.get(0):null;"
new=("  // Match server's nearest-owned-suit selection when multiple are parked.\n"
     "  return stands.stream().min(java.util.Comparator.comparingDouble(\n"
     "    stand->stand.distanceToSqr(mc.player))).orElse(null);")
assert s.count(old)==1,("V176_B718_SOURCE_DRIFT",s.count(old))
assert 'xsxlabs_v176_owner_' in s, "B718 must retain the synced owner protection"
p.write_text(s.replace(old,new,1),encoding="utf-8")
print("V176_B718_MULTIPLE_OWNED_SUITS_NEAREST_ACTION_WHEEL_PASS")
