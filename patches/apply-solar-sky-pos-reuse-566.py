#!/usr/bin/env python3
"""B566: no per-tick BlockPos allocation for identical solar sky lookup.

Preserves actual live canSeeSky query every generating tick, all FE/t,
transactions, routing, and snapshot semantics. No cached sun visibility.
"""
import os
from pathlib import Path
p=Path(os.environ['V1_SOURCE_ROOT'])/'dev/obsidiannetwork/blockentity/SolarGeneratorBlockEntity.java'
s=p.read_text(encoding='utf8')
marker='B566_SOLAR_SKY_BLOCKPOS_REUSE'
assert marker not in s
for anchor in ('B536_SOLAR_MSPT_FACE_MASK','B547_SOLAR_SPARSE_FACE_WALK',
               'B565_SOLAR_FULL_BUFFER_SKY_FASTPATH',
               'private ServerLevel energyCacheLevel;',
               'void onLoad()',
               'server.canSeeSky(pos.above())',
               'long budget = be.energy.stored();',
               'long made = Math.min(be.tier.output(), be.energy.capacity() - be.energy.stored());',
               'be.energyJournal.updateSnapshots(tx);',
               'tx.commit();','budget -= accepted;'):
 assert s.count(anchor)==1,('B566_SOLAR_SOURCE_DRIFT',anchor,s.count(anchor))
s=s.replace('private ServerLevel energyCacheLevel;', '''// B566_SOLAR_SKY_BLOCKPOS_REUSE: reuse immutable above-position only.
 private net.minecraft.core.BlockPos xsxSolarAbove;
 private net.minecraft.core.BlockPos xsxSolarAbove() {
  if(xsxSolarAbove==null)xsxSolarAbove=worldPosition.above();
  return xsxSolarAbove;
 }
 private ServerLevel energyCacheLevel;''',1)
s=s.replace('server.canSeeSky(pos.above())','server.canSeeSky(be.xsxSolarAbove())',1)
assert s.count(marker)==1
assert s.count('server.canSeeSky(be.xsxSolarAbove())')==1
assert s.index('be.energyJournal.updateSnapshots(tx);')<s.index('tx.commit();')
p.write_text(s,encoding='utf8')
print('B566_SOLAR_SKY_BLOCKPOS_REUSE_PASS: zero daylight sky-pos allocations after warmup, live sunlight and FE preserved')
