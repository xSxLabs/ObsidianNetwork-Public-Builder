#!/usr/bin/env python3
"""Fail-closed reentrancy protection for cyclic cross-mod FE capability graphs.

A third-party conduit can route a cable capability call back into the same
cable before the original transfer completes. Stop only that recursive branch;
keep original transactions, limits, routing, and successful transfer semantics.
"""
import os,re
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/blockentity/EnergyCableBlockEntity.java"
s=p.read_text(encoding="utf-8")
marker="XSXLABS_CROSSMOD_ENERGY_REENTRY_GUARD_V1"
cls="public final class EnergyCableBlockEntity extends BlockEntity implements FacadeCable {"
assert s.count(cls)==1 and marker not in s
start=re.search(r'private\s+final\s+class\s+CableEnergyHandler\s+implements\s+EnergyHandler\s*\{',s)
assert start, "CableEnergyHandler missing"
def end_brace(source,at):
    depth=1;i=at+1
    while depth and i<len(source):
        if source[i]=='{':depth+=1
        elif source[i]=='}':depth-=1
        i+=1
    assert depth==0
    return i
end=end_brace(s,s.index('{',start.start()))
handler=s[start.start():end]
field="energyActiveTransfer"
for name,ret in (("getAmountAsLong","0L"),("extract","0"),("insert","0")):
    match=re.search(r'\b'+name+r'\s*\([^)]*\)\s*\{',handler)
    assert match, "missing energy method: "+name
    brace=match.end()-1
    finish=end_brace(handler,brace)
    body=handler[brace+1:finish-1]

    replacement=(
      "{\\n      var active = "+field+".get();\\n"
      "      if (!active.add(EnergyCableBlockEntity.this)) return "+ret+";\\n"
      "      try {"+body+"\\n      } finally {\\n"
      "         active.remove(EnergyCableBlockEntity.this);\\n"
      "         if (active.isEmpty()) "+field+".remove();\\n"
      "      }\\n   }")
    handler=handler[:brace]+replacement+handler[finish:]
s=s[:start.start()]+handler+s[end:]
s=s.replace(cls,cls+"\n   // "+marker+"\n   private static final ThreadLocal<java.util.Set<Object>> "+field+" = ThreadLocal.withInitial(() -> java.util.Collections.newSetFromMap(new java.util.IdentityHashMap<>()));",1)
assert s.count(marker)==1
p.write_text(s,encoding="utf-8")
print("CROSSMOD_ENERGY_LOOP_GUARD_PASS: cyclic FE reentry blocked, transactions untouched")
