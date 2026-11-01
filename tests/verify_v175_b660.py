#!/usr/bin/env python3
"""B661 postpatch verify all registered planter variants nonconducting."""
import os,re
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
client=(J/"client/PowerArmorExitInputLock654.java").read_text(encoding="utf8")
registry=(J/"ObsidianNetwork.java").read_text(encoding="utf8")
assert "PowerArmorRuntime.full(p)" not in client
assert "v->v.isOpeningFor654(p.getUUID())" in client
assert "p.input=ZERO_INPUT;" in client and "p.input=previousInput;" in client
pattern=re.compile(r'BLOCKS\.registerBlock\("(network_planter(?:_stripped_[a-z_]+)?)"[^;]*?NetworkPlanterBlock::new[^;]*?;',re.S)
entries={m.group(1):m.group(0) for m in pattern.finditer(registry)}
names=re.findall(r'BLOCKS\.registerBlock\("(network_planter(?:_stripped_[a-z_]+)?)"',registry)
assert names and len(names)==len(entries)==len(set(names)),("B661_REGISTRY_COVERAGE",names,list(entries))
for name,section in entries.items():
 assert section.count(".isRedstoneConductor((state,level,pos)->false)")==1,name
assert "network_planter" in entries
assert "NetworkPlanterBlock" in (J/"block/NetworkPlanterBlock.java").read_text(encoding="utf8")
assert "isExitOpening659" in (J/"powerarmor/PowerArmorVisualEntity.java").read_text(encoding="utf8")
print("B661_ALL_PLANTERS_CHEST_SAFE_AND_LOCAL_LOCK_PASS count="+str(len(entries)))
