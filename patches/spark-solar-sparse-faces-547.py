#!/usr/bin/env python3
"""B547: walk only the connected solar FE faces in original round-robin order.

No throttling or buffering. Every tick produces the same FE and offers the
same budget to the same recipients in the same order. A typical one-cable
solar panel visits one candidate rather than all six directions.
"""
import os
from pathlib import Path
p = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork/blockentity/SolarGeneratorBlockEntity.java"
s = p.read_text(encoding="utf-8")
assert "B536_SOLAR_MSPT_FACE_MASK" in s
assert "XSXLABS_SPARK_SOLAR_STATIC_DIRECTIONS_V1" in s
assert "B547_SOLAR_SPARSE_FACE_WALK" not in s
old_loop = "for (int off = 0; off < sides.length && budget > 0L; off++) {"
old_face = "Direction side = sides[(start + off) % sides.length];"
old_skip = "if((be.xsxSolarFaceMask&(1<<side.get3DDataValue()))==0)continue;"
for anchor in (old_loop, old_face, old_skip,
  "int start = be.nextSide++ % sides.length;",
  "be.energyJournal.updateSnapshots(tx);",
  "long extracted = be.energy.extract(accepted);",
  "tx.commit();",
  "budget -= accepted;",
  "long made = Math.min(be.tier.output(), be.energy.capacity() - be.energy.stored());",
  "long budget = be.energy.stored();"):
 assert s.count(anchor)==1, ("B547_SOLAR_SOURCE_DRIFT",anchor,s.count(anchor))
# Minecraft Direction.values() order and its get3DDataValue() are the same
# six indices. Check all 63 masks and 6 starts for identical scan order.
for mask in range(1,64):
 for start in range(6):
  previous=[(start+off)%6 for off in range(6)
            if mask&(1<<((start+off)%6))]
  rotated=((mask>>start)|(mask<<(6-start)))&63
  optimized=[]
  while rotated:
   bit=(rotated&-rotated).bit_length()-1
   optimized.append((start+bit)%6)
   rotated&=rotated-1
  assert previous==optimized, ("B547_ORDER_CHANGED",mask,start)
# Never skip a connected target or change transaction boundaries. Replace only
# face-index enumeration; preserve the complete live FE transfer body.
s=s.replace(old_loop, """// B547_SOLAR_SPARSE_FACE_WALK: scan only active directions, zero allocations.
            int solarMask = be.xsxSolarFaceMask & 63;
            int solarRotated = ((solarMask >>> start) |
                  (solarMask << (sides.length - start))) & 63;
            while (solarRotated != 0 && budget > 0L) {""",1)
s=s.replace(old_face, """int off = Integer.numberOfTrailingZeros(solarRotated);
               solarRotated &= solarRotated - 1;
               Direction side = sides[(start + off) % sides.length];""",1)
s=s.replace(old_skip,"// B547: all enumerated faces are already present in the live cached mask.",1)
assert "for (int off = 0; off < sides.length && budget > 0L; off++)" not in s
assert s.count("Integer.numberOfTrailingZeros(solarRotated)")==1
for contract in ("long budget = be.energy.stored();",
 "be.energyJournal.updateSnapshots(tx);",
 "long extracted = be.energy.extract(accepted);",
 "tx.commit();", "budget -= accepted;"):
 assert s.count(contract)==1
assert s.index("be.energyJournal.updateSnapshots(tx);") < s.index("long extracted = be.energy.extract(accepted);") < s.index("tx.commit();")
p.write_text(s,encoding="utf-8")
print("B547_SOLAR_SPARSE_FACES_PASS: 378 mask/rotation checks; exact FE/t, unlimited export and rollback retained")
