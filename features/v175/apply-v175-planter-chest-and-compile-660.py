#!/usr/bin/env python3
"""B660: fix LocalPlayer/server type mixup, and keep chests usable under all planters."""
import os,re
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
client=J/"client/PowerArmorExitInputLock654.java"
s=client.read_text(encoding="utf8")
broken="v->v.isOpeningFor654(p.getUUID()) && (!v.isClosingFor659(p.getUUID()) || !dev.obsidiannetwork.powerarmor.PowerArmorRuntime.full(p))"
assert s.count(broken)==1,("B660_LOCAL_PLAYER_ANCHOR",s.count(broken))
s=s.replace(broken,"v->v.isOpeningFor654(p.getUUID())",1)
assert "PowerArmorRuntime.full(p)" not in s
client.write_text(s,encoding="utf8")
# Minecraft Java chest checks redstone-conductive blocks directly above it.
# This preserves all existing physical and graphical behavior of the planter.
registry=J/"ObsidianNetwork.java"
s=registry.read_text(encoding="utf8")
pat=re.compile(
 r'(BLOCKS\.registerBlock\("network_planter(?:_stripped_[a-z_]+)?",\s*'
 r'dev\.obsidiannetwork\.block\.NetworkPlanterBlock::new,\s*'
 r'p\s*->\s*p\.mapColor\(MapColor\.WOOD\)\.strength\(1\.0F,6\.0F\)\.noOcclusion\(\))(\);)')
names=re.findall(r'BLOCKS\.registerBlock\("(network_planter(?:_stripped_[a-z_]+)?)"',s)
assert names and len(names)==len(set(names)),("B660_PLANTER_NAMES",names)
s,count=pat.subn(lambda m:m.group(1)+'.isRedstoneConductor((state,level,pos)->false)'+m.group(2),s)
assert count==len(names),("B660_REGISTRY_DRIFT",count,len(names),names)
assert "BLOCKS.registerBlock(\"network_planter\"" in s
registry.write_text(s,encoding="utf8")
print("B660_LOCAL_PLAYER_COMPILE_FIX_PASS")
print("B660_PLANTER_CHEST_NONCONDUCTOR_PASS variants="+str(count))
