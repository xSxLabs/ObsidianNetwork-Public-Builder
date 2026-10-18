#!/usr/bin/env python3
"""Hoist duplicate ENERGY_CABLE BlockState.is/registry lookup in both hot helpers.

After the existing fail-closed non-bundle guard, energyCable/energyOpen each
test the very same immutable BlockState against the same ENERGY_CABLE block
*again*. Save that single boolean for the rest of that one helper call.
No caching across calls/ticks, no changing face cuts, ConduitBundle.enabled,
world/BE lookups, transfer rates, capability invalidation or transactions.
"""
import os
import re
from pathlib import Path

path=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/blockentity/EnergyCableBlockEntity.java"
source=path.read_text(encoding="utf-8")
marker="XSXLABS_ENERGY_HELPER_DUPLICATE_BLOCKTYPE_ELISION_V1"
assert marker not in source
assert source.count("XSXLABS_SPARK_ENERGY_NONBUNDLE_FAST_REJECT_V1")==2
assert "XSXLABS_SPARK_CABLE_ENDPOINT_CAPABILITY_CACHE_V1" in source
assert source.count("private final class CableEnergyHandler implements EnergyHandler")==1

pattern=(
    r"private\s+static\s+boolean\s+{method}"
    r"\s*\(\s*(?:net\.minecraft\.server\.level\.)?ServerLevel\s+\w+\s*,"
    r"\s*(?:net\.minecraft\.core\.)?BlockPos\s+\w+\s*,"
    r"\s*(?:net\.minecraft\.world\.level\.block\.state\.)?BlockState\s+(?P<state>\w+)"
    r"{direction}\s*\)\s*\{"
)

def helper(source,name):
    direction=(r"\s*,\s*(?:net\.minecraft\.core\.)?Direction\s+\w+"
        if name=="energyOpen" else "")
    # Use literal token replacement: regex needs a raw opening brace (\\{).
    # Python str.format interprets it as a format brace and breaks the script.
    sig=pattern.replace("{method}",name).replace("{direction}",direction)
    found=list(re.finditer(sig,source))
    assert len(found)==1, f"Unexpected {name} signature"
    match=found[0]
    p=match.end()
    depth=1
    while depth and p<len(source):
        if source[p]=="{":
            depth+=1
        elif source[p]=="}":
            depth-=1
        p+=1
    assert depth==0
    return match,p

# Build changes in memory; source stays byte-identical if either helper drifts.
out=source
for name in ("energyOpen","energyCable"):
    m,end=helper(out,name)
    state=m.group("state")
    body=out[m.end():end-1]
    energy_call=f"{state}.is((Block)ObsidianNetwork.ENERGY_CABLE.get())"
    bundle_call=f"{state}.is((Block)ObsidianNetwork.CONDUIT_BUNDLE.get())"
    old=f"if(!{energy_call} && !{bundle_call}) return false;"
    assert body.count(old)==1, f"{name} nonbundle safety gate changed"
    assert body.count(energy_call)==2, f"{name} duplicate cable type lookup shape changed"
    assert body.count(bundle_call)==1, f"{name} bundle type guard changed"
    assert body.count("getBlockEntity(")==1, f"{name} live bundle lookup changed"
    assert "ConduitBundleBlockEntity" in body, f"{name} bundle type gate changed"
    if name=="energyOpen":
        assert "EnergyCableBlock.isCut(" in body, "Side cut semantics changed"
        assert ".enabled(" in body, "Bundle side-enabled gate changed"
    else:
        assert ".has(" in body, "Bundle energy layer gate changed"

    # Reuse one local, immutable block type decision; the original second
    # branch still checks the same cable, while the early bundle gate stays.
    new=f"// {marker}\n      boolean physicalEnergyCable = {energy_call};\n      if(!physicalEnergyCable && !{bundle_call}) return false;"
    prefix,suffix=body.split(old,1)
    assert suffix.count(energy_call)==1, "Expected exactly one repeated cable branch"
    suffix=suffix.replace(energy_call,"physicalEnergyCable",1)
    body=prefix+new+suffix
    assert body.count(energy_call)==1
    assert body.count("if(!physicalEnergyCable && !"+bundle_call+") return false;")==1
    assert body.count("physicalEnergyCable")==3, "one initializer, one guard, one original branch"
    assert body.count("getBlockEntity(")==1
    out=out[:m.end()]+body+out[end-1:]

assert out.count(marker)==2
assert out.count("BlockCapabilityCache.create(")==source.count("BlockCapabilityCache.create(")
assert out.count("source.extract(")==source.count("source.extract(")
assert out.count("target.insert(")==source.count("target.insert(")
assert out.count("Transaction.openRoot()")==source.count("Transaction.openRoot()")
assert out.count("EnergyCableBlock.isCut(")==source.count("EnergyCableBlock.isCut(")
path.write_text(out,encoding="utf-8")
print("ENERGY_HELPER_DUPLICATE_BLOCKTYPE_ELISION_V1 PASS: same live topology and side cuts, fewer registry/state checks")
