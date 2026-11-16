#!/usr/bin/env python3
"""B1651: prohibit cross-claim fluid block formation, but allow owner-internal mechanics.

The B1646 guard intentionally failed closed for every claimed destination.
Refine to deny only when a fluid originated outside the same owner's claim:
lava/water generators inside a claim work normally, cross-border grief stays
blocked. No loaded chunk lookup, no IO, only two map lookups per relevant event.
"""
import os
from pathlib import Path
P=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/claims/V178Claims.java"
s=P.read_text(encoding="utf-8")
old='''  // B1646_FLUID_FORMATION_GUARD: block formation caused by fluids has no
  // accountable player. Cancel only if the destination belongs to a claim;
  // unclaimed cobblestone/obsidian formation remains unchanged.
  @SubscribeEvent public static void protectFluidFormation(BlockEvent.FluidPlaceBlockEvent event){
   if(!(event.getLevel() instanceof ServerLevel level))return;
   ensure(level);
   BlockPos destination=event.getPos();
   if(map(level).containsKey(key(destination.getX()>>4,destination.getZ()>>4)))
    event.setCanceled(true);
  }
'''
new='''  // B1651_FLUID_BOUNDARY_GUARD: ordinary water/lava interactions within a
  // single owner's claims still work. Deny only cross-owner/unclaimed fluid
  // formation into protected destination. Never loads or generates chunks.
  @SubscribeEvent public static void protectFluidFormation(BlockEvent.FluidPlaceBlockEvent event){
   if(!(event.getLevel() instanceof ServerLevel level))return;
   ensure(level);
   Map<Long,Claim> claims=map(level);
   if(claims.isEmpty())return;
   BlockPos destination=event.getPos();
   Claim target=claims.get(key(destination.getX()>>4,destination.getZ()>>4));
   if(target==null)return;
   BlockPos origin=event.getLiquidPos();
   Claim source=claims.get(key(origin.getX()>>4,origin.getZ()>>4));
   if(source==null||!source.owner().equals(target.owner()))
    event.setCanceled(true);
  }
'''
assert s.count(old)==1,("V178_FLUID_BORDER_DRIFT",s.count(old))
s=s.replace(old,new,1)
assert s.count("protectFluidFormation(BlockEvent.FluidPlaceBlockEvent")==1
assert "getLiquidPos()" in s
assert "if(source==null||!source.owner().equals(target.owner()))" in s
P.write_text(s,encoding="utf-8")
print("V178_B1651_FLUID_OWNER_BOUNDARY_GUARD_PASS")
