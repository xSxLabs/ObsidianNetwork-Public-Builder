#!/usr/bin/env python3
"""Deduplicate ITEM dispatch before the expensive endpoint/component scan.

The old code scanned every network once per member bundle on each transport
tick, and only then checked whether another member had already dispatched it.
This changes no transfer cadence, persisted data, endpoint policy, or item math.
"""
import os
from pathlib import Path

root = Path(os.environ.get("V1_SOURCE_ROOT", "work/src/main/java"))
path = root / "dev/obsidiannetwork/conduit/ItemConduitTicker.java"
source = path.read_text()
marker = "XSXLABS_ITEM_DEDUP_BEFORE_ENDPOINT_SCAN_V1"
check = """  Long previous=lastTransferTick.put(network,level.getGameTime());
  if(previous!=null&&previous.longValue()==level.getGameTime())return;
"""
cadence = "if(network.type()!=ConduitType.ITEM||level.getGameTime()%5!=0)return;"
scan = "network.cacheEndpoints(ConduitRuntime.scanEndpoints(level,network,true),ConduitRuntime.scanEndpoints(level,network,false));"
assert source.count(cadence) == 1, "ITEM transport cadence anchor changed"
assert source.count(check) == 1, "ITEM per-network dispatch guard anchor changed"
assert source.count(scan) == 1, "ITEM endpoint scan anchor changed"
if marker not in source:
    assert source.index(scan) < source.index(check), "Unexpected existing ITEM guard placement"
    source = source.replace(check, "", 1)
    source = source.replace(cadence, cadence + "\n  // " + marker + "\n" + check.rstrip(), 1)
    path.write_text(source)
assert source.index(cadence) < source.index(check) < source.index(scan), "ITEM dedup must precede endpoint scans"
assert "network.endpoints(true)" in source and "network.endpoints(false)" in source
print("ITEM_CONDUIT_DEDUP_BEFORE_SCAN_V1 PASS")
