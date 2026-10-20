#!/usr/bin/env python3
"""Assert shipped ENERGY BFS helpers share immutable registered block types.

Checking the final class prevents a source-only patch from being reported
as a performance gain if it never reached the release JAR. Original cable
cuts, conduit ENERGY layer, sided enabled and live BE lookup are mandatory.
Full transactional NeoForge and network GameTests run separately.
"""
import argparse
import re
import subprocess
from pathlib import Path
from zipfile import ZipFile

CLASS="dev.obsidiannetwork.blockentity.EnergyCableBlockEntity"
ENTRY="dev/obsidiannetwork/blockentity/EnergyCableBlockEntity.class"
CACHE_CLASS="dev.obsidiannetwork.blockentity.EnergyCableBlockEntity$XsxRegisteredEnergyBlocks"
CACHE_ENTRY="dev/obsidiannetwork/blockentity/EnergyCableBlockEntity$XsxRegisteredEnergyBlocks.class"

def method_code(disassembly,name):
    marker=f"  private static boolean {name}("
    starts=[m.start() for m in re.finditer(re.escape(marker),disassembly)]
    assert len(starts)==1, f"Missing or ambiguous {name}"
    fragment=disassembly[starts[0]:]
    following=re.search(r"\n  (?:private|public|protected|static) ",fragment[1:])
    assert following, f"Method boundary {name} not found"
    return fragment[:following.start()+1]

def verify(jar):
    assert jar.is_file(),f"Missing final JAR: {jar}"
    with ZipFile(jar) as z:
        assert ENTRY in z.namelist(),"Compiled ENERGY cable class missing"
        assert CACHE_ENTRY in z.namelist(),"Compiled lazily initialized ENERGY block cache class missing"
        assert not any(p.startswith("dev/obsidiannetwork/build103/") for p in z.namelist()), \
            "Test-only GameTests leaked into release"
    code=subprocess.run(["javap","-c","-p","-classpath",str(jar),CLASS],
        check=True,capture_output=True,text=True).stdout
    for name in ("energyCable","energyOpen"):
        method=method_code(code,name)
        # Each helper reads the ENERGY_CABLE blockstate once, and when
        # necessary the CONDUIT_BUNDLE blockstate once. No duplicate lookup.
        assert method.count("BlockState.is:")==2, f"Repeated BlockState.is in {name}"
        # Build 347 resolves these immutable registry entries ONCE in
        # XsxRegisteredEnergyBlocks.<clinit>, never in the BFS helper.
        assert method.count("XsxRegisteredEnergyBlocks.ENERGY:")==1, \
            f"Cached energy block predicate missing or duplicated in {name}"
        assert method.count("XsxRegisteredEnergyBlocks.BUNDLE:")==1, \
            f"Cached bundle predicate missing or duplicated in {name}"
        assert "ObsidianNetwork.ENERGY_CABLE:" not in method
        assert "ObsidianNetwork.CONDUIT_BUNDLE:" not in method
        assert "DeferredHolder.get:" not in method
        assert "ServerLevel.getBlockEntity:" in method, f"Lost live bundle check in {name}"
        assert "ConduitBundleBlockEntity" in method, f"Lost live bundle type in {name}"
        assert "ConduitBundleBlockEntity$Layer.ENERGY" in method, f"Wrong bundle layer in {name}"
        if name=="energyOpen":
            assert "EnergyCableBlock.isCut:" in method, "Lost cable cut"
            assert "ConduitBundleBlockEntity.enabled:" in method, "Lost side-specific bundle setting"
        else:
            assert "ConduitBundleBlockEntity.has:" in method, "Lost bundle ENERGY layer test"
    # Require a real one-time nested-class initializer in the distributable
    # JAR, not just a reference to an undeclared field in transformed source.
    cache=subprocess.run(["javap","-c","-p","-classpath",str(jar),CACHE_CLASS],
        check=True,capture_output=True,text=True).stdout
    assert "static {};" in cache, "Missing lazy Java class initializer"
    assert cache.count("ObsidianNetwork.ENERGY_CABLE:")==1, "Energy registry holder not resolved once"
    assert cache.count("ObsidianNetwork.CONDUIT_BUNDLE:")==1, "Bundle registry holder not resolved once"
    assert "DeferredHolder.get:" in cache or "DeferredBlock.get:" in cache or ".get:" in cache, "No registration resolution in cache"
    print("COMPILED_ENERGY_HELPERS_LAZY_REGISTERED_BLOCKS_V2 PASS")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("jar",type=Path)
    verify(p.parse_args().jar)
