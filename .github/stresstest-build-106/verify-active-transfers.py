#!/usr/bin/env python3
"""Transport acceptance gate for frozen Build 106.

Requires an actual test fixture with configured Network Storage import/export
faces, source/destination inventories and tanks. Never substitutes command
injection, hopper movement or arbitrary /data edits for mod transport.
"""
import json,sys
from pathlib import Path
p=Path("transport-results.json")
if not p.exists():
 print("TRANSPORT TEST NOT RUN: no instrumented importer/exporter fixture supplied.")
 print("Build 106 is frozen; a compatible runtime test fixture is required.")
 sys.exit(2)
data=json.loads(p.read_text())
required=("item_imported","item_exported","item_cable_moved","fluid_imported_mb","fluid_exported_mb","fluid_cable_moved_mb","avg_mspt","p95_mspt")
missing=[k for k in required if k not in data]
if missing:raise SystemExit("Transport metrics missing: "+", ".join(missing))
for k in required[:6]:
 if not isinstance(data[k],(int,float)) or data[k]<=0:
  raise SystemExit("Transport not proven: "+k)
if data["avg_mspt"]<=0 or data["p95_mspt"]<=0:
 raise SystemExit("MSPT measurements missing")
print("PASS: real mod transport metrics",json.dumps(data,sort_keys=True))
