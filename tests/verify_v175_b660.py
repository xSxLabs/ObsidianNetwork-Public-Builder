#!/usr/bin/env python3
"""B660 post-overlay fail-closed tests for client lock and chest obstruction."""
import os,re
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
client=(J/"client/PowerArmorExitInputLock654.java").read_text(encoding="utf8")
reg=(J/"ObsidianNetwork.java").read_text(encoding="utf8")
assert "PowerArmorRuntime.full(p)" not in client
assert "v->v.isOpeningFor654(p.getUUID())" in client
assert "p.input=ZERO_INPUT;" in client and "p.input=previousInput;" in client
assert "isExitOpening659" in (J/"powerarmor/PowerArmorVisualEntity.java").read_text(encoding="utf8")
assert "registerAvatarEntityModifier" in (J/"client/PowerArmorExitRender659.java").read_text(encoding="utf8")
matches=re.findall(r'BLOCKS\.registerBlock\("(network_planter(?:_stripped_[a-z_]+)?)",\s*'
 r'dev\.obsidiannetwork\.block\.NetworkPlanterBlock::new,\s*'
 r'p\s*->\s*p\.mapColor\(MapColor\.WOOD\)\.strength\(1\.0F,6\.0F\)'
 r'\.noOcclusion\(\)\.isRedstoneConductor\(\(state,level,pos\)->false\)\);',reg)
assert matches and len(matches)==len(set(matches)),("B660_PLANTER_REGISTRY",matches)
assert "network_planter" in matches
assert "NetworkPlanterBlock" in (J/"block/NetworkPlanterBlock.java").read_text(encoding="utf8")
print("B660_PLANTER_CHEST_AND_CLIENT_LOCK_SOURCE_GATE_PASS count="+str(len(matches)))
