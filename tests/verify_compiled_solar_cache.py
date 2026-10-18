#!/usr/bin/env python3
"""Verify the *shipped* solar FE cache did not fall back to EnumMap or bypass FE.

Source assertions alone are insufficient: only the final JAR bytecode is
checked here. This gate is supplementary to live NeoForge FE GameTests.
"""
import argparse
import subprocess
from pathlib import Path
from zipfile import ZipFile

CLASS="dev.obsidiannetwork.blockentity.SolarGeneratorBlockEntity"
ENTRY="dev/obsidiannetwork/blockentity/SolarGeneratorBlockEntity.class"

def verify(jar: Path):
    if not jar.is_file():
        raise AssertionError(f"Final compiled JAR missing: {jar}")
    with ZipFile(jar) as z:
        assert ENTRY in z.namelist(), "Solar generator class missing in shipped JAR"
        assert not any(name.startswith("dev/obsidiannetwork/build103/") for name in z.namelist()), \
            "CI-only GameTests leaked into release"
    code=subprocess.run(["javap","-c","-p","-classpath",str(jar),CLASS],
                        capture_output=True,text=True,check=True).stdout
    assert "energyNeighbors" in code, "Solar FE endpoint cache missing"
    assert "get3DDataValue:()I" in code, "Physical face slot index absent"
    assert "BlockCapabilityCache.create:" in code, "Invalidation-aware capability creation absent"
    assert "BlockCapabilityCache.getCapability:()" in code, "Live capability access absent"
    assert code.count("java/util/Arrays.fill:") >= 3, \
        "World/load/removal cache invalidation not compiled"
    assert "java/util/EnumMap" not in code, "Old EnumMap overhead remains"
    assert "Transaction.openRoot:" in code and "Transaction.commit:" in code, \
        "Original transactional solar FE delivery absent"
    print("COMPILED_SOLAR_SIX_FACE_SAFE_CACHE_V1 PASS")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("jar",type=Path)
    verify(parser.parse_args().jar)
