#!/usr/bin/env python3
"""Do not re-scan an ITEM conduit network on duplicate invocations in one tick.

ItemConduitTicker already prevents the second transfer in the same tick using
lastTransferTick. Previously it rebuilt endpoints BEFORE that guard, repeating
the entire network scan for every second+ node tick. Moving the guard before
the scan preserves the one-transfer-per-tick behavior and refresh cadence.
"""
from pathlib import Path
import os

root = Path(os.environ.get("V1_SOURCE_ROOT", "work/src/main/java"))
p = root / "dev/obsidiannetwork/conduit/ItemConduitTicker.java"
s = p.read_text()

outer = "if(network.type()!=ConduitType.ITEM||level.getGameTime()%5!=0)return;"
scan_head = "if(network.dirty() || level.getGameTime()%5 == 0)"
scan_call = "network.cacheEndpoints(ConduitRuntime.scanEndpoints(level,network,true),ConduitRuntime.scanEndpoints(level,network,false));"
guard_first = "Long previous=lastTransferTick.put(network,level.getGameTime());"
guard_second = "if(previous!=null&&previous.longValue()==level.getGameTime())return;"
assert all(s.count(x) == 1 for x in [outer, scan_head, scan_call, guard_first, guard_second]), (
    "ITEM ticker structure changed; no modification is safe"
)

start = s.index(scan_head)
scan_end = s.index(guard_first, start)
end = s.index(guard_second, scan_end) + len(guard_second)
scan = s[start:scan_end]
guard = s[scan_end:end]
assert scan_call in scan and guard_first in guard and guard_second in guard
assert s.index(outer) < start, "transfer cadence must remain intact"
assert s.count("XSXLABS_BUNDLE_TPS_CACHE_V1") == 1, "expected existing endpoint cache patch missing"
s = s[:start] + guard + "\n" + scan + s[end:]
assert s.index(guard_first) < s.index(scan_call)
p.write_text(s)
print("ITEM_CONDUIT_DUPLICATE_SCAN_ELISION_V1 PASS")
