#!/usr/bin/env python3
"""v1.7.6 first build: source-contract diagnostics for additive, versioned overlays.
Only reads decompiled/post-1.7.5 files. Prints precise source to CI job logs,
so Attack / Follow / Turret / Backpack can be integrated against REAL 26.1 APIs.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
FILES={
 "ACTION_WHEEL":"client/NetworkActionWheelClient.java",
 "ARMOR_RUNTIME":"powerarmor/PowerArmorRuntime.java",
 "SUIT_WORLD":"powerarmor/PowerArmorSuitWorld.java",
 "SUIT_VISUAL":"powerarmor/PowerArmorVisualEntity.java",
 "ACTION_CLIENT":"client/PowerArmorBuild98Client.java",
 "SERVER_COMMANDS":"powerarmor/PowerArmorCommands.java",
 "ARMOR_STATION":"powerarmor/ArmorStationBlock.java",
 "UPGRADE_ITEM":"powerarmor/UpgradeCardItem.java",
 "KEYS":"powerarmor/PowerArmorExitKeyClient.java",
 "STORAGE_MENU":"menu/StorageTerminalMenu.java",
 "STORAGE_ITEM":"core/EnergyTool.java",
 "CLIENT_MENU":"client/ClientModEvents.java",
}
REQUIRED=("ACTION_WHEEL","ARMOR_RUNTIME","SUIT_WORLD","SUIT_VISUAL","SERVER_COMMANDS","ARMOR_STATION")
KEYWORDS=("attack","mouse","left","button","click","fire","action","slot","key","register","equip","item","send","interact","hurt","start","full","powered","update","tick","getEntities","projectile","press","energy","menu","inventory","use")
print("V176_SOURCE_CONTRACTS_BEGIN")
for label,rel in FILES.items():
 p=J/rel
 if not p.is_file():
  if label in REQUIRED:raise RuntimeError("V176_REQUIRED_CLASS_MISSING "+rel)
  print("V176_OPTIONAL_MISSING",rel)
  continue
 lines=p.read_text(encoding="utf-8").splitlines()
 print("V176_CLASS",label,rel,"lines",len(lines))
 if label in ("ACTION_WHEEL","ARMOR_RUNTIME","SERVER_COMMANDS","UPGRADE_ITEM","KEYS"):
  selected=list(enumerate(lines,1))
 elif label in ("SUIT_WORLD","SUIT_VISUAL","ARMOR_STATION","STORAGE_MENU","ACTION_CLIENT"):
  indices={i for i,s in enumerate(lines) if any(k in s.lower() for k in KEYWORDS)}
  expanded=set()
  for i in indices:
   expanded.update(range(max(0,i-2),min(len(lines),i+5)))
  selected=[(i+1,lines[i]) for i in sorted(expanded)][:260]
 else:
  selected=[(i+1,s) for i,s in enumerate(lines) if any(k in s.lower() for k in KEYWORDS)][:85]
 for i,line in selected:
  print(f"V176_SRC {label} L{i:04d} {line[:450]}")
 print("V176_CLASS_END",label)
print("V176_SOURCE_CONTRACTS_PASS")
