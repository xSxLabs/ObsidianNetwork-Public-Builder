#!/usr/bin/env python3
"""Fail-closed live transport probe for the frozen Build 106 dedicated server.

This probe never counts commands, hopper moves, or cable placement as transport.
It is a diagnostic precursor to a Java fixture, not a substitute for it.
"""
import json, runpy, time
from pathlib import Path
state=runpy.run_path(str(Path(__file__).with_name("benchmark.py")))
r=state["r"]
observations={}
for block in ("importer","exporter","item_cable","fluid_cable","fluid_importer","fluid_exporter"):
    response=r.cmd("setblock 8 90 8 obsidiannetwork:"+block)
    observations[block]=response
    r.cmd("setblock 8 90 8 minecraft:air")
print("ACTIVE_TRANSPORT_DIAGNOSTIC",json.dumps(observations,sort_keys=True),flush=True)
Path("active-transport-diagnostic.json").write_text(json.dumps({"block_registry_probes":observations,"active_transfers_verified":False},indent=2))
raise SystemExit("FAIL: An external Java fixture must configure importer/exporter block entities, supply capability-backed inventories/tanks, and independently verify movement before this benchmark can pass.")
