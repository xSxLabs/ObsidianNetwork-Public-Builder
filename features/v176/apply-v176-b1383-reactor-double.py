#!/usr/bin/env python3
"""B1383: 2x production and exactly 2x fuel/coolant consumption, all reactor sizes.

Apply after B577 and all existing Reactor, Powerbank, GUI patches on
1.7.6-powerbank only. Do not change transfer rate limits or other machines.
"""
import os
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
reactor=J/"reactor/ReactorControllerBlockEntity.java"
screen=J/"client/V174MachineScreen.java"
r=reactor.read_text("utf8")
g=screen.read_text("utf8")

def replace(s,old,new,label):
    n=s.count(old)
    assert n==1,("B1383_DRIFT",label,n,old)
    return s.replace(old,new,1)

assert "B577_REACTOR_REAL_PRODUCTION_X5" in r
assert "B1380_REACTOR_OFF_BLOCKS_ALL_SERVER_TICKS" in r
assert "B577_REACTOR_MAX_GUI_X5" in g
assert "B1383_REACTOR_DOUBLE_OUTPUT" not in r

r=replace(r,
    "(long)be.rodAssemblies*600L*20L*(100-be.controlRodInsertion)/100L",
    "(long)be.rodAssemblies*1200L*20L*(100-be.controlRodInsertion)/100L"
    " /* B1383_REACTOR_DOUBLE_OUTPUT */","real_generation")
r=replace(r,
    "(long)rodAssemblies*600L*(100-controlRodInsertion)/100L",
    "(long)rodAssemblies*1200L*(100-controlRodInsertion)/100L",
    "telemetry_generation")
g=replace(g,
    "long b568Maximum=600L*Math.max(0,ctrl.guiRodAssemblies());",
    "long b568Maximum=1200L*Math.max(0,ctrl.guiRodAssemblies());"
    " // B1383_REACTOR_MAX_2X","gui_max")

# The legacy rod-insertion scaling is max(1,ceil(20*remaining_percent/100)).
# Twice as much fuel time AND twice as much water are spent *only* when
# the generator actually produces. Avoid underfunded coolant batches.
r=replace(r,
    "int activity=Math.max(1,(20*(100-be.controlRodInsertion)+99)/100);",
    "int activity=2*Math.max(1,(20*(100-be.controlRodInsertion)+99)/100);"
    " // B1383_DOUBLE_FUEL_WATER","actual_consumption")
r=replace(r,
    "if(be.fuelTicks<=0||be.waterMb<20)",
    "if(be.fuelTicks<=0||be.waterMb<"
    "2*Math.max(1,(20*(100-be.controlRodInsertion)+99)/100))",
    "coolant_minimum_for_2x")
r=replace(r,
    "waterMb>=20?",
    "waterMb>=2*Math.max(1,(20*(100-controlRodInsertion)+99)/100)?",
    "live_rate_matches_water")
# Formation light and rate telemetry should not say RUNNING while the
# doubled coolant requirement is unsatisfied.
lighting="boolean b530Active=be.formed&&be.enabled&&be.fuelTicks>0&&be.waterMb>=20;"
if lighting in r:
    r=replace(r,lighting,
      "boolean b530Active=be.formed&&be.enabled&&be.fuelTicks>0"
      "&&be.waterMb>=2*Math.max(1,(20*(100-be.controlRodInsertion)+99)/100);",
      "active_light")
assert "be.waterMb=Math.max(0,be.waterMb-activity);" in r
assert "be.fuelTicks=Math.max(0,be.fuelTicks-activity);" in r
assert "Math.min(FE_CAPACITY-be.storedFe," in r
assert "if(!be.xsxNetworkEnabled)return;" in r
reactor.write_text(r,"utf8")
screen.write_text(g,"utf8")
print("B1383_REACTOR_1200_FE_PER_ROD_PER_TICK_DOUBLE_WATER_AND_FUEL_PASS")
