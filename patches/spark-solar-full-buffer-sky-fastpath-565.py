#!/usr/bin/env python3
"""B565: skip sky visibility checks when the solar buffer is already full.

The per-tick output loop MUST still run, including when the buffer is full.
Generation, tier rates, FE routing, capability invalidation, atomic transfer,
round-robin order, and persistence stay unchanged.
"""
import os
from pathlib import Path

p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/blockentity/SolarGeneratorBlockEntity.java"
s=p.read_text(encoding="utf-8")
marker="B565_SOLAR_FULL_BUFFER_SKY_FASTPATH"
assert marker not in s,("B565_ALREADY_APPLIED",p)
for needed in ("B536_SOLAR_MSPT_FACE_MASK","B547_SOLAR_SPARSE_FACE_WALK",
 "XSXLABS_SOLAR_BLOCK_CAPABILITY_CACHE_V1","XSXLABS_SOLAR_FIXED_SIX_FACE_CACHE_V1",
 "server.canSeeSky(pos.above())",
 "long made = Math.min(be.tier.output(), be.energy.capacity() - be.energy.stored());",
 "long budget = be.energy.stored();",
 "if (budget > 0L && be.xsxLiveSolarFaces(server)!=0) {",
 "be.energyJournal.updateSnapshots(tx);","long extracted = be.energy.extract(accepted);",
 "tx.commit();","budget -= accepted;","int start = be.nextSide++ % sides.length;"):
 assert s.count(needed)==1,("B565_SOURCE_DRIFT",needed,s.count(needed))
# A full buffer has no free capacity: original Math.min(output,capacity-stored)
# produces 0 whether sunlight is visible or not. Leave export untouched.
old="server.canSeeSky(pos.above())"
new="(be.energy.stored() < be.energy.capacity() && server.canSeeSky(pos.above())) /* "+marker+" */"
s=s.replace(old,new,1)
assert s.count(marker)==1
assert s.count("long budget = be.energy.stored();")==1
assert s.index("be.energyJournal.updateSnapshots(tx);")<s.index("long extracted = be.energy.extract(accepted);")<s.index("tx.commit();")
p.write_text(s,encoding="utf-8")
print("B565_SOLAR_FULL_BUFFER_SKY_FASTPATH_PASS: no full-buffer sky query; exact per-tick generation, unlimited output, rollback preserved")
