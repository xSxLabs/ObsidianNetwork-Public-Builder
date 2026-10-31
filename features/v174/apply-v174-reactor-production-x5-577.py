#!/usr/bin/env python3
"""B577: 5x actual reactor generation capacity for ALL formed sizes.

The current implementation generates once every 20 server ticks and
limits generation by reactor FE storage; multiply generation per rod by
five while leaving interval, fuel and water use, rod insertion, safety,
inventory, output capabilities and transfers unchanged. GUI uses exactly
the same production unit (600 FE/t per rod assembly).
"""
import os
from pathlib import Path

j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
reactor=j/"reactor/ReactorControllerBlockEntity.java"
gui=j/"client/V174MachineScreen.java"
s=reactor.read_text(encoding="utf-8")
h=gui.read_text(encoding="utf-8")
assert "B577_REACTOR_REAL_PRODUCTION_X5" not in s
assert "B577_REACTOR_MAX_GUI_X5" not in h
# Source B489: 20-tick generation batch, optional rod insertion throttle.
# KEEP the exact same 20-tick cadence; energy increased by 5, not TPS load.
old="(long)be.rodAssemblies*120L*20L*(100-be.controlRodInsertion)/100L"
new="(long)be.rodAssemblies*600L*20L*(100-be.controlRodInsertion)/100L"
assert s.count(old)==1,("B577_REACTOR_PRODUCTION_FORMULA_DRIFT",s.count(old))
s=s.replace(old,new+" /* B577_REACTOR_REAL_PRODUCTION_X5 */",1)
# Reactor diagnostic rate must match the real generator and rod control.
old="(long)rodAssemblies*120L*(100-controlRodInsertion)/100L"
new="(long)rodAssemblies*600L*(100-controlRodInsertion)/100L"
assert s.count(old)==1,("B577_REACTOR_GUI_TELEMETRY_DRIFT",s.count(old))
s=s.replace(old,new,1)
assert "be.waterMb=Math.max(0,be.waterMb-activity);" in s
assert "be.fuelTicks=Math.max(0,be.fuelTicks-activity);" in s
assert "Math.min(FE_CAPACITY-be.storedFe," in s
assert "controlRodInsertion" in s and "enabled" in s
assert "long generated=" in s
old="long b568Maximum=120L*Math.max(0,ctrl.guiRodAssemblies()); // B575_REACTOR_MAX_SYNCED_RODS"
new="long b568Maximum=600L*Math.max(0,ctrl.guiRodAssemblies()); // B577_REACTOR_MAX_GUI_X5 B575_REACTOR_MAX_SYNCED_RODS"
assert h.count(old)==1,("B577_MAX_GUI_ANCHOR",h.count(old))
h=h.replace(old,new,1)
reactor.write_text(s,encoding="utf-8")
gui.write_text(h,encoding="utf-8")
print("B577_REACTOR_ALL_SIZES_TRUE_5X_FE_WITH_UNCHANGED_TICK_RATE_AND_RESOURCES_PASS")
