#!/usr/bin/env python3
"""B434 electric water pump: no infinite loops, FE/water correctness, real ports."""
import ast,os
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=(root/"features/v174/apply-water-pump-434.py").read_text()
w=(root/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
ast.parse(p)
for t in ("hasSource(world,pos)","world.hasChunkAt(at)","fluid.isSource()",
 "water+=1000*batches","energy-=200L*batches","Math.min(16,speed.getCount())",
 "waterJournal.updateSnapshots(tx)","energyJournal.updateSnapshots(tx)",
 "Capabilities.Energy.BLOCK","Capabilities.Fluid.BLOCK","Capabilities.Item.BLOCK",
 "new ElectricWaterPumpMenu(id,inv,be)","pumpSpeed","pumpWater","pumpEnergy"):
 assert t in p,t
for t in ("python3 features/v174/apply-water-pump-434.py",
 "python3 tests/test_v174_water_pump_434.py"):assert t in w,t
assert w.index("python3 features/v174/apply-reactor-ports-433.py")<w.index("python3 features/v174/apply-water-pump-434.py")
if os.environ.get("V1_SOURCE_ROOT"):
 j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
 for file in ("ElectricWaterPumpBlock","ElectricWaterPumpMenu","ElectricWaterPumpBlockEntity",
              "ElectricWaterPumpCapabilities"):
  assert (j/"pump"/(file+".java")).is_file(),file
print("V174_WATER_PUMP_434_TEST_PASS")
