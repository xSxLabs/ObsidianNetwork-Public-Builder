#!/usr/bin/env python3
"""Inspect the distributed Java bytecode for all three Spark live-scan fixes.

Source-only marker checks are insufficient: this executes javap against the
actual built mod JAR. Do not accept a test fixture or CI-only GameTest class.
"""
from pathlib import Path
import subprocess
import sys

if len(sys.argv)!=2:
    raise SystemExit("Usage: verify_compiled_spark_live_scan_guards.py compiled-mod.jar")
jar=Path(sys.argv[1])
assert jar.is_file(),"Built distributable JAR missing"

def bytecode(java_class):
    return subprocess.run(["javap","-c","-p","-classpath",str(jar),java_class],
                          text=True,capture_output=True,check=True).stdout
world=bytecode("dev.obsidiannetwork.network.WorldTopologyBridge")
conduit=bytecode("dev.obsidiannetwork.conduit.ConduitRuntime")

def isolate(all_text,first,after):
    assert all_text.count(first)==1,("Expected one Java method",first,all_text.count(first))
    assert all_text.count(after)>=1,("Java method boundary missing",after)
    a=all_text.index(first)
    b=all_text.index(after,a+len(first))
    return all_text[a:b]

auto=isolate(world,"public static int autocrafterCount(","public static int autoChiselerCount(")
devices=isolate(world,"public static dev.obsidiannetwork.network.WorldTopologyBridge$DeviceCounts connectedDeviceCounts(",
                "public static java.util.List<net.minecraft.core.BlockPos> externalCandidates(")
scan=isolate(conduit,"public static java.util.List<dev.obsidiannetwork.conduit.ConduitRuntime$Endpoint> scanEndpoints(",
             "public static java.util.List<dev.obsidiannetwork.conduit.ConduitRuntime$Endpoint> endpoints(")
for name,part in (("autocrafterCount",auto),("connectedDeviceCounts",devices)):
    for invariant in ("BlockPos.getX:", "BlockPos.getZ:", "hasChunkAt"):
        assert invariant in part,(name,"same-chunk live predicate absent:",invariant)
assert "HashSet" in auto and "level" not in ""  # component counting remains live
for name in ("IdentityHashMap", "IdentityHashMap.get:", "IdentityHashMap.put:",
             "getBlockState", "traversable", "hasChunkAt"):
    assert name in scan,("Conduit endpoint registry memo not compiled",name)
assert "getKey:" in scan and "getPath:" in scan,"Original registered block path classification absent"
print("COMPILED_SPARK_LIVE_SCAN_THREE_FIXES_V1 PASS: both live chunk guards and per-call Conduit registry memo")
