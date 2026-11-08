#!/usr/bin/env python3
"""v1.7.7 Armor Station-specific NutriPaste transfer through existing Fluid Cables.

The regular LogisticsCable fluid import defaults to 250 mB every five ticks,
which cannot refill a 1,000,000 mB helmet within 30 seconds. Give only Armor
Station destinations a 25,000 mB per transfer budget. The normal 250 mB plus
upgrades limit remains untouched for every other destination, and both source
and destination are still simulated and executed authoritatively.
"""
import os
import re
from pathlib import Path

p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/blockentity/LogisticsCableBlockEntity.java"
s=p.read_text(encoding="utf-8")
matches=list(re.finditer(r"^ private void transferFluid\(Direction in\)\{[^\r\n]*$",s,re.MULTILINE))
assert len(matches)==1,("V177_STATION_FLUID_IMPORT_SHAPE_DRIFT",len(matches))
old=matches[0].group()
# Earlier reconstruction patches can change the transactional method's formatting.
# Match its unique method signature; the replacement below preserves simulated
# source/destination transfer and refunds unused fluid.
assert "Capabilities.Fluid.BLOCK" in old, "V177_STATION_FLUID_CAPABILITY_MISSING"
new=""" private void transferFluid(Direction in){
  var srcR=level.getCapability(Capabilities.Fluid.BLOCK,worldPosition.relative(in),in.getOpposite());
  IFluidHandler src=srcR==null?null:IFluidHandler.of(srcR);
  if(src==null)return;
  for(Endpoint e:exports()){
   var dstR=level.getCapability(Capabilities.Fluid.BLOCK,e.pos.relative(e.side),e.side.getOpposite());
   IFluidHandler dst=dstR==null?null:IFluidHandler.of(dstR);
   if(dst==null)continue;
   // V177_STATION_FAST_PASTE_IMPORT: ONLY an actual Armor Station destination
   // receives the special budget. All other targets retain fluidAmount(in).
   int max=fluidAmount(in);
   if(level.getBlockEntity(e.pos.relative(e.side))
      instanceof dev.obsidiannetwork.powerarmor.ArmorStationBlockEntity)
    max=Math.max(max,25_000);
   FluidStack sim=src.drain(max,IFluidHandler.FluidAction.SIMULATE);
   if(sim.isEmpty())return;
   int accepted=dst.fill(sim,IFluidHandler.FluidAction.SIMULATE);
   if(accepted<=0)continue;
   FluidStack got=src.drain(accepted,IFluidHandler.FluidAction.EXECUTE);
   int put=dst.fill(got,IFluidHandler.FluidAction.EXECUTE);
   // Never discard fluid when the destination shrinks between simulation
   // and execution; refund any unused amount to the original source.
   if(put<got.getAmount()){
    FluidStack back=got.copy();
    back.setAmount(got.getAmount()-put);
    src.fill(back,IFluidHandler.FluidAction.EXECUTE);
   }
   return;
  }
 }"""
s=s[:matches[0].start()]+new+s[matches[0].end():]
p.write_text(s,encoding="utf-8")
print("V177_STATION_25000_MB_PER_FLUID_CABLE_TRANSFER_OTHER_TARGETS_UNCHANGED_PASS")
