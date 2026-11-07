#!/usr/bin/env python3
"""B1390: double 20Hz Reactor generation and real 20-tick fuel/coolant use.

B579 changed generation from once/20 ticks to EVERY tick, then B591 added
auto-full pause. Patch both generation paths, not the retired 20x formula.
No edits to input/output FE port capabilities or Powerbank.
"""
import os
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
reactor=J/"reactor/ReactorControllerBlockEntity.java"
screen=J/"client/V174MachineScreen.java"
r=reactor.read_text("utf8")
g=screen.read_text("utf8")

def once(s,old,new,label,n=1):
    found=s.count(old)
    assert found==n,("B1390_REACTOR_DRIFT",label,found,n,
                     [line.strip() for line in s.splitlines()
                      if ("rodAssemblies*" in line or "waterMb" in line
                          or "activity" in line)][:30])
    return s.replace(old,new,n)

assert "B577_REACTOR_REAL_PRODUCTION_X5" in r
assert "B579_REACTOR_GENERATE_EVERY_TICK" in r
assert "B591_REACTOR_AUTO_FULL_GATE" in r
assert "B1380_REACTOR_OFF_BLOCKS_ALL_SERVER_TICKS" in r
assert "B577_REACTOR_MAX_GUI_X5" in g
assert "B1383_REACTOR_DOUBLE_OUTPUT" not in r

# 600 FE/t -> 1200 FE/t per fuel-assembly unit. B579 has two real
# pathways: 19 regular ticks + the one fuel/water maintenance tick.
src="(long)be.rodAssemblies*600L*(100-be.controlRodInsertion)/100L"
dst="(long)be.rodAssemblies*1200L*(100-be.controlRodInsertion)/100L"
r=once(r,src,dst,"both_live_tick_generation_paths",2)
assert r.count(dst)==2
r=once(r,"  // B579_REACTOR_GENERATE_EVERY_TICK:",
          "  // B1383_REACTOR_DOUBLE_OUTPUT: both live generation paths.\n"
          "  // B579_REACTOR_GENERATE_EVERY_TICK:",
          "double_output_marker")

# Double the real resource deductions, ONLY when generating FE.
r=once(r,"int activity=Math.max(1,(20*(100-be.controlRodInsertion)+99)/100);",
       "int activity=2*Math.max(1,(20*(100-be.controlRodInsertion)+99)/100);"
       " // B1383_DOUBLE_FUEL_WATER","twice_real_consumption")
assert "be.waterMb=Math.max(0,be.waterMb-activity);" in r
assert "be.fuelTicks=Math.max(0,be.fuelTicks-activity);" in r

# The 20-tick maintenance guard must allow generation only if there is
# enough water for twice the prior consumption. Apply the same check to
# B579's 19 intermediate ticks and to the auto-full pause path.
required="2*Math.max(1,(20*(100-be.controlRodInsertion)+99)/100)"
r=once(r,"if(be.fuelTicks<=0||be.waterMb<20)",
       "if(be.fuelTicks<=0||be.waterMb<"+required+")",
       "maintenance_coolant_guard")
assert r.count("be.waterMb>=20")>=1, "B1390_EXPECTS_ORIGINAL_LIVE_WATER_GUARD"
r=r.replace("be.waterMb>=20","be.waterMb>="+required)

# B579 GUI rate is measured ACTUAL generation, not a hypothetical formula.
assert "public long guiFePerTick(){return b579ActualGeneration;}" in r
g=once(g,"long b568Maximum=600L*Math.max(0,ctrl.guiRodAssemblies());",
       "long b568Maximum=1200L*Math.max(0,ctrl.guiRodAssemblies());"
       " // B1383_REACTOR_MAX_2X","power_max_gui")
assert "Math.min(FE_CAPACITY-be.storedFe," in r
assert "if(!be.xsxNetworkEnabled)return;" in r
reactor.write_text(r,"utf8")
screen.write_text(g,"utf8")
print("B1390_REACTOR_1200_FE_EVERY_TICK_DOUBLE_FUEL_WATER_MATCHED_PASS")
