#!/usr/bin/env python3
"""Verify compiled Controller device counting uses one direction-array read."""
import re
import subprocess
import sys
from pathlib import Path

if len(sys.argv)!=2:
    raise SystemExit("Usage: verify_compiled_controller_device_scan.py distributable.jar")
jar=Path(sys.argv[1])
assert jar.is_file(), "Missing final JAR"
text=subprocess.run(["javap","-c","-p","-classpath",str(jar),
   "dev.obsidiannetwork.network.WorldTopologyBridge"],capture_output=True,
   text=True,check=True).stdout
lines=text.splitlines()
sig="connectedDeviceCounts(net.minecraft.server.level.ServerLevel, dev.obsidiannetwork.core.NetworkRuntime);"
starts=[i for i,x in enumerate(lines) if x.strip().endswith(sig)]
assert len(starts)==1, ("Expected exact Controller device summary signature",starts)
start=starts[0]
end=next((i for i in range(start+1,len(lines))
    if lines[i].startswith("  ") and not lines[i].startswith("    ")
    and not re.match(r"  \d+: ",lines[i])),len(lines))
method="\n".join(lines[start:end])
# Direction.values in source must become a single enum clone per invocation,
# not one copy per graph node and another per candidate capability.
assert method.count("Direction.values")==1, "Compiled device scan still clones six directions repeatedly"
assert "HashSet.add:" in method and "HashSet.size:" in method, "Missing dedup/count contract"
assert "getCapability" in method, "Live capability detection must be retained"
assert "getBlockState" in method, "Actual world block state detection must be retained"
print("COMPILED_CONTROLLER_EXTERNAL_ONCE_PER_CALL_V1 PASS")
