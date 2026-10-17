#!/usr/bin/env python3
"""Spark hot path: avoid block-entity lookups for non-energy/non-bundle blocks.

The compiled mod shows energyCable and energyOpen falling back to
ServerLevel.getBlockEntity for EVERY adjacent non-energy-cable BlockState.
ConduitBundleBlockEntity is only valid at the registered CONDUIT_BUNDLE
block. We merely reject impossible block kinds earlier; no FE, modes,
topology, capability, or transaction behavior is cached or changed.
Fail closed on any unrecognized decompiled helper signature or body.
"""
import os,re
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/blockentity/EnergyCableBlockEntity.java"
s=p.read_text(encoding="utf-8")
marker="XSXLABS_SPARK_ENERGY_NONBUNDLE_FAST_REJECT_V1"
assert marker not in s,"already applied"
assert s.count("class EnergyCableBlockEntity")==1,"wrong source class"
for name in ("energyCable","energyOpen"):
    sig=(r"private\s+static\s+boolean\s+"+name+
         r"\s*\(\s*(?:net\.minecraft\.server\.level\.)?ServerLevel\s+\w+\s*,"
         r"\s*(?:net\.minecraft\.core\.)?BlockPos\s+\w+\s*,"
         r"\s*(?:net\.minecraft\.world\.level\.block\.state\.)?BlockState\s+(\w+)"
         +(r"\s*,\s*(?:net\.minecraft\.core\.)?Direction\s+\w+" if name=="energyOpen" else "")+
         r"\s*\)\s*\{")
    all_matches=list(re.finditer(sig,s))
    assert len(all_matches)==1,f"Ambiguous/missing {name} helper, matches={len(all_matches)}"
    m=all_matches[0]
    pos=m.end();depth=1
    while depth>0 and pos<len(s):
        if s[pos]=="{":depth+=1
        elif s[pos]=="}":depth-=1
        pos+=1
    assert depth==0,f"Unbalanced {name} helper"
    body=s[m.end():pos-1]
    for required in ("getBlockEntity(","ConduitBundleBlockEntity","ObsidianNetwork.ENERGY_CABLE.get()"):
        assert required in body,f"Missing {name} safety guard: {required}"
    state=m.group(1)
    early=("\n      // "+marker+"\n"
           "      if(!"+state+".is((Block)ObsidianNetwork.ENERGY_CABLE.get()) && !"
           +state+".is((Block)ObsidianNetwork.CONDUIT_BUNDLE.get())) return false;\n")
    s=s[:m.end()]+early+s[m.end():]
assert s.count(marker)==2
assert s.count("ObsidianNetwork.CONDUIT_BUNDLE.get()")>=2
p.write_text(s,encoding="utf-8")
print("SPARK_ENERGY_NONBUNDLE_FAST_REJECT_V1 PASS; skipped needless BE queries for normal blocks")
