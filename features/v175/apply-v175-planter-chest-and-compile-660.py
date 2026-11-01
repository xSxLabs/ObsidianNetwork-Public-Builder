#!/usr/bin/env python3
"""B661 revised B660: tolerate all actual planter property-builder variants."""
import os,re
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
client=J/"client/PowerArmorExitInputLock654.java"
s=client.read_text(encoding="utf8")
bad="v->v.isOpeningFor654(p.getUUID()) && (!v.isClosingFor659(p.getUUID()) || !dev.obsidiannetwork.powerarmor.PowerArmorRuntime.full(p))"
assert s.count(bad)==1,("B660_LOCAL_PLAYER_ANCHOR",s.count(bad))
client.write_text(s.replace(bad,"v->v.isOpeningFor654(p.getUUID())"),encoding="utf8")
registry=J/"ObsidianNetwork.java"
s=registry.read_text(encoding="utf8")
allNames=re.findall(r'BLOCKS\.registerBlock\("(network_planter(?:_stripped_[a-z_]+)?)"',s)
assert allNames and len(allNames)==len(set(allNames)),("B661_NAMES",allNames)
# Match each actual registration as a UNIT, independently of hardness,
# formatting, sounds or previously added BlockBehaviour properties.
pat=re.compile(r'BLOCKS\.registerBlock\("(network_planter(?:_stripped_[a-z_]+)?)"[^;]*?NetworkPlanterBlock::new[^;]*?;',re.S)
seen=[]
def fix(m):
 name=m.group(1);source=m.group(0);seen.append(name)
 assert source.rstrip().endswith(");"),("B661_REGISTRATION_FORMAT",name)
 assert re.search(r'\bp\s*->\s*p\.',source),("B661_NOT_PROPERTIES_LAMBDA",name)
 assert "isRedstoneConductor(" not in source,("B661_DUPLICATE",name)
 # Append only ONE property; preserve the existing block, shape, inventory,
 # collision, animations, growth, capability and all existing properties.
 return source.rstrip()[:-2]+".isRedstoneConductor((state,level,pos)->false));"
s,n=pat.subn(fix,s)
assert n==len(allNames)==len(set(seen)),("B661_REGISTRY_DRIFT",n,len(allNames),seen,allNames)
assert set(seen)==set(allNames),("B661_NAMES_DRIFT",seen,allNames)
registry.write_text(s,encoding="utf8")
print("B661_LOCAL_PLAYER_COMPILE_FIX_PASS")
print("B661_CHEST_OPEN_UNDER_PLANTER_PASS variants="+str(n))
