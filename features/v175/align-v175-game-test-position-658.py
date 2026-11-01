#!/usr/bin/env python3
"""B658 real MK1/MK2 GameTest spatial isolation, no runtime changes.
New entry actually makes the FakePlayer walk into MK1, so the subsequent
MK2 scenario must reset its starting position to the SAME controlled base
where the original regression fixture began. Both item conservation,
right-click hold-open and actual 64-tick exit checks remain unchanged.
"""
import os
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/build103/Build103GameTests.java"
s=p.read_text(encoding="utf8")
old='''                for(int tier=0;tier<2;tier++){
                  var parts=tier==0?new net.minecraft.world.item.Item[]{'''
new='''                for(int tier=0;tier<2;tier++){
                  // B658: the MK1 "physically walk inside" regression moved
                  // this FakePlayer into a suit. Run MK2 from the SAME safe
                  // original test origin as MK1; each tier has isolated space.
                  player.setPos(base.getX()+0.5D,base.getY(),base.getZ()+0.5D);
                  var parts=tier==0?new net.minecraft.world.item.Item[]{'''
assert s.count(old)==1,("B658 fixture tier loop",s.count(old))
s=s.replace(old,new,1)
assert s.count("completeExitOpening650(player,level,base);")==2
assert "for(int openTick=0;openTick<96;openTick++)" in s
assert 'check(stand.isRemoved(),"entered world suit still exists, tier "+tier);' in s
assert 'protection5_roundtrip=true' in s
assert s.count("POWER_ARMOR_REAL_ROUNDTRIP_V69")==2
p.write_text(s,encoding="utf8")
print("B658_MK1_MK2_REAL_SPATIAL_ISOLATION: identical baseline start after physical walk-in; all item proof retained")
