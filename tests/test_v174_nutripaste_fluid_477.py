#!/usr/bin/env python3
"""B477 NutriPaste genuine native fluid, transactional transfer and lifecycle."""
import ast
import os
from pathlib import Path
root=Path(__file__).resolve().parents[1]
script=(root/"features/v174/apply-nutripaste-fluid-477.py").read_text()
wf=(root/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
ast.parse(script)
for token in ("B477_NUTRIPASTE_REAL_FLUID","DeferredRegister.create(Registries.FLUID",
              "DeferredRegister.create(NeoForgeRegistries.FLUID_TYPES",
              "BaseFlowingFluid.Source","BaseFlowingFluid.Flowing",
              "SnapshotJournal<Long> pasteJournal","pasteJournal.updateSnapshots(tx)",
              "return 0;","paste-=given","Capabilities.Fluid.BLOCK",
              "NutriPasteFluids.register(modEventBus)","nutrinatorPaste"):
 assert token in script,token
assert wf.index("python3 features/v174/apply-wip-public-test-476.py") < wf.index("python3 features/v174/apply-nutripaste-fluid-477.py")
assert wf.rindex("python3 features/v174/apply-nutripaste-fluid-477.py") < wf.rindex("python3 tests/test_v174_nutripaste_fluid_477.py")
if os.environ.get("V1_SOURCE_ROOT"):
 j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
 reg=(j/"nutrition/NutriPasteFluids.java").read_text()
 tank=(j/"nutrition/NutrinatorBlockEntity.java").read_text()
 cap=(j/"nutrition/NutrinatorCapabilities.java").read_text()
 assert 'FLUIDS.register("nutripaste"' in reg
 assert 'FLUIDS.register("flowing_nutripaste"' in reg
 assert "B477_NUTRIPASTE_TRANSACTIONAL_FLUID" in tank
 assert "PASTE_CAPACITY" in tank and 'out.putLong("nutrinatorPaste",paste);' in tank
 assert "pasteJournal.updateSnapshots(tx)" in tank
 assert "e.registerBlockEntity(Capabilities.Fluid.BLOCK" in cap
 assert "return 0;" in tank
print("B477_NUTRIPASTE_REAL_FLUID_TEST_PASS")
