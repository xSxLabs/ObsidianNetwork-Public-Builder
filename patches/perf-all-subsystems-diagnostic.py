#!/usr/bin/env python3
"""One-run diagnostic inventory for crafting, cable, conduit, solar, and terminal.
Prints method-level operation counts from the reconstructed, fully patched source.
Never exports private Java source.
"""
import os,re
from pathlib import Path
root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
targets={
"craft_menu":"menu/StorageTerminalMenu.java",
"craft_inventory":"blockentity/TerminalInventoryBlockEntity.java",
"energy_cable":"blockentity/EnergyCableBlockEntity.java",
"conduit_ticker":"conduit/EnergyConduitTicker.java",
"solar":"blockentity/SolarGeneratorBlockEntity.java",
"importer":"blockentity/ImporterBlockEntity.java",
"exporter":"blockentity/ExporterBlockEntity.java",
"controller":"blockentity/NetworkControllerBlockEntity.java",
"autocrafter":"blockentity/AutocrafterBlockEntity.java",
}
operations=("Transaction.openRoot(", ".extract(", ".insert(", "getBlockEntity(", "getCapability(", "broadcastChanges(", "setChanged(", "keysSnapshot(", "getCraftItem(", "setCraftItem(", "getItem(", "setItem(")
for name,rel in targets.items():
 p=root/rel
 if not p.is_file():
  print("PERF_DIAG_MISSING",name,rel)
  continue
 text=p.read_text(encoding="utf-8")
 print("PERF_DIAG_FILE",name,"bytes",len(text),*[f"{op}={text.count(op)}" for op in operations])
 methods=[]
 for m in re.finditer(r"(?m)^\s*(?:public|private|protected)\s+(?:(?:static|final|synchronized)\s+)*[\w<>\[\], ?]+\s+(\w+)\s*\([^;{}]*\)\s*\{",text):
  depth=1
  j=m.end()
  while j<len(text) and depth:
   if text[j]=="{":depth+=1
   elif text[j]=="}":depth-=1
   j+=1
  body=text[m.end():j]
  weight=sum(body.count(op) for op in operations)
  if weight:methods.append((weight,m.group(1),len(body),[f"{op}:{body.count(op)}" for op in operations if body.count(op)]))
 for weight,method,length,counts in sorted(methods,reverse=True)[:12]:
  print("PERF_DIAG_METHOD",name,method,"operations",weight,"chars",length,*counts)
print("PERF_DIAG_ALL_SUBSYSTEMS_COMPLETE")
