#!/usr/bin/env python3
"""Check the BUILT JAR, not only the injected Java, for component-once count."""
from pathlib import Path
import subprocess
import sys

if len(sys.argv)!=2:
    raise SystemExit("Usage: verify_compiled_autocrafter_count.py compiled-mod.jar")
jar=Path(sys.argv[1])
if not jar.is_file():
    raise SystemExit("Missing compiled JAR")
r=subprocess.run(
    ["javap","-c","-p","-classpath",str(jar),
     "dev.obsidiannetwork.network.WorldTopologyBridge"],
    capture_output=True,text=True,check=True)
data=r.stdout
method="public static int autocrafterCount("
next_method="public static int autoChiselerCount("
assert data.count(method)==1 and data.count(next_method)==1, "Compiled Java method layout drift"
start=data.index(method);end=data.index(next_method,start)
code=data[start:end]
for name in ("TopologyBindingManager.stateAt", "NetworkGraph.component",
             "HashSet"):
    assert name in code, "Required compiled method contract missing: "+name
assert code.count("NetworkGraph.component")==1, "Repeated component traversal in compiled method"
assert "WorldTopologyBridge.runtimeForNode" not in code, "Compiled method still uses per-node BFS"
assert "LEVELS:" in code, "Expected level map unchanged"
assert "autocrafters" in code, "Expected authoritative registered autocrafters membership"
print("AUTOCRAFTER_COUNT_COMPONENT_ONCE_BYTECODE_GATE_V1 PASS")
