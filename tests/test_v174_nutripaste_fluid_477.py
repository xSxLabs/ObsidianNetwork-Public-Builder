#!/usr/bin/env python3
"""B477 NutriPaste genuine native fluid, transactional transfer and lifecycle."""
import ast
import os
import subprocess
import sys
import tempfile
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
# B479: six spaces in the genuine decompiled B475 mod constructor.
assert '"      BLOCKS.register(modEventBus);"' in script
assert '"       BLOCKS.register(modEventBus);"' not in script
assert wf.rindex("python3 features/v174/apply-nutripaste-fluid-477.py") < wf.rindex("python3 tests/test_v174_nutripaste_fluid_477.py")
# B481: execute the actual B477 injector against the precise B438 Java
# templates BEFORE spending ~15 minutes on Minecraft decompilation/GameTests.
# Covers both drift-prone anchors and fluid registration/translation writes.
base=(root/"features/v174/apply-nutrition-438.py").read_text(encoding="utf-8")
def template(relative):
 marker="java("+chr(34)+relative+chr(34)+",r'''"
 start=base.index(marker)+len(marker)
 return base[start:base.index("''')",start)]
with tempfile.TemporaryDirectory() as tmp:
 source=Path(tmp)/"java"
 java=source/"dev/obsidiannetwork"
 java.mkdir(parents=True)
 for filename in ("NutrinatorBlockEntity.java","NutrinatorCapabilities.java"):
  (java/"nutrition").mkdir(parents=True,exist_ok=True)
  (java/"nutrition"/filename).write_text(template("nutrition/"+filename),encoding="utf-8")
 (java/"ObsidianNetwork.java").write_text("      BLOCKS.register(modEventBus);\n",encoding="utf-8")
 resources=Path(tmp)/"resources"
 for lang in ("en_us","de_de"):
  f=resources/"assets/obsidiannetwork/lang"/(lang+".json")
  f.parent.mkdir(parents=True,exist_ok=True)
  f.write_text("{}\n",encoding="utf-8")
 env=os.environ.copy()
 env["V1_SOURCE_ROOT"]=str(source)
 env["V1_RESOURCE_ROOT"]=str(resources)
 result=subprocess.run([sys.executable,str(root/"features/v174/apply-nutripaste-fluid-477.py")],
    env=env,text=True,capture_output=True)
 assert result.returncode==0,"B481 native-fluid injector failed preflight: "+result.stdout+result.stderr
 assert "NutriPasteFluids.register(modEventBus)" in (java/"ObsidianNetwork.java").read_text()
 assert '.descriptionId("fluid.obsidiannetwork.nutripaste")' in (java/"nutrition/NutriPasteFluids.java").read_text()
 assert "net.minecraft.Util.makeDescriptionId" not in (java/"nutrition/NutriPasteFluids.java").read_text()
 assert "B477_NUTRIPASTE_TRANSACTIONAL_FLUID" in (java/"nutrition/NutrinatorBlockEntity.java").read_text()
 assert "Capabilities.Fluid.BLOCK" in (java/"nutrition/NutrinatorCapabilities.java").read_text()
 assert (java/"nutrition/NutriPasteFluids.java").is_file()

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
