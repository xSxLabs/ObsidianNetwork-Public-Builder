#!/usr/bin/env python3
"""B433 reactor IO regression; generated source checked during full build."""
import ast,os
from pathlib import Path
r=Path(__file__).resolve().parents[1]
p=(r/"features/v174/apply-reactor-ports-433.py").read_text()
w=(r/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
ast.parse(p)
for t in ("V174_B433_APPROVED_PORTS","approvedPorts.clear()","approvedPorts.add(at.asLong())",
 "be.allowsPort(worldPosition)","VanillaContainerWrapper.of(this)",
 "coolantJournal.updateSnapshots(tx)","Fluids.WATER","Capabilities.Item.BLOCK",
 "Capabilities.Fluid.BLOCK","Capabilities.Energy.BLOCK","out.putLong(\"reactorController\",linkedPos)",
 "new Result(true,\"FORMED\",sx,sy,sz,rods,java.util.List.copyOf(ports))"):
 assert t in p,t
for t in ("python3 features/v174/apply-reactor-ports-433.py","python3 tests/test_v174_reactor_ports_433.py"):
 assert t in w,t
assert w.index("python3 features/v174/apply-multiblock-recovery-431.py")<w.index("python3 features/v174/apply-reactor-ports-433.py")
if os.environ.get("V1_SOURCE_ROOT"):
 j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
 assert "approvedPorts.clear()" in (j/"reactor/ReactorControllerBlockEntity.java").read_text()
 assert "be.allowsPort(worldPosition)" in (j/"reactor/ReactorPortBlockEntity.java").read_text()
 for f in ("ReactorPortBlock.java","ReactorPortBlockEntity.java","ReactorPortCapabilities.java"):
  assert (j/"reactor"/f).is_file()
print("V174_REACTOR_PORTS_433_TEST_PASS")
