#!/usr/bin/env python3
"""Build427 static and generated-source regression checks for v1.7.4 reactor phase 1."""
import ast,os
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=(root/"features/v174/apply-reactor-core-427.py").read_text()
ast.parse(p)
wf=(root/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
for item in ("python3 features/v174/apply-reactor-core-427.py",
             "python3 tests/test_v174_reactor_core_427.py"):
    assert item in wf, item
assert wf.index("python3 features/v174/apply-uranium-fuel-chain.py")<wf.index("python3 features/v174/apply-reactor-core-427.py")
for item in ("V174_REACTOR_GEOMETRY","MIN=5,MAX=64","shellLimit=6*MAX*MAX",
             "world.hasChunkAt(p)","Exactly one reactor controller",
             "at least one interior fuel assembly","REACTOR_POWER_PORT",
             "REACTOR_FLUID_PORT","REACTOR_ITEM_PORT","FE_CAPACITY=1_000_000_000L",
             "Capabilities.Energy.BLOCK","TransactionContext","SnapshotJournal",
             "fuelTicks=12_000","waterMb-=20","ItemStack.CODEC","getBooleanOr"):
    assert item in p,item
assert "world.getChunkAt(" not in p
assert "new ChunkPos(" not in p
assert "private static final Map<BlockPos" not in p
if os.environ.get("V1_SOURCE_ROOT"):
    j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
    a=(j/"ObsidianNetwork.java").read_text()
    for item in ("REACTOR_CASING","REACTOR_GLASS","REACTOR_CONTROLLER","REACTOR_POWER_PORT",
                 "REACTOR_FLUID_PORT","REACTOR_ITEM_PORT","REACTOR_FUEL_ASSEMBLY","URANIUM_ROD"):
        assert item in a,item
    r=j/"reactor"
    for source in ("ReactorStructure","ReactorControllerBlock","ReactorControllerBlockEntity","ReactorMenu","ReactorEnergyCapabilities"):
        assert (r/(source+".java")).is_file(),source
    resources=Path(os.environ["V1_RESOURCE_ROOT"])/"data/obsidiannetwork/recipe"
    for name in ("reactor_casing","reactor_glass","reactor_controller","reactor_fuel_assembly"):
        assert (resources/(name+".json")).is_file(),name
print("V174_REACTOR_CORE_427_REGRESSION_PASS")
