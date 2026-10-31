#!/usr/bin/env python3
"""B577 exact 5x generator/GUI contract and representative rod control values."""
import os
from pathlib import Path
j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
r=(j/"reactor/ReactorControllerBlockEntity.java").read_text()
g=(j/"client/V174MachineScreen.java").read_text()
assert "(long)be.rodAssemblies*600L*20L*(100-be.controlRodInsertion)/100L" in r
assert "(long)rodAssemblies*600L*(100-controlRodInsertion)/100L" in r
assert "long b568Maximum=600L*Math.max(0,ctrl.guiRodAssemblies());" in g
assert "B577_REACTOR_REAL_PRODUCTION_X5" in r
assert "B577_REACTOR_MAX_GUI_X5" in g
assert "(long)be.rodAssemblies*120L*20L" not in r
assert "rodAssemblies*120L*" not in r
assert "b568Maximum=120L" not in g
assert "Math.min(FE_CAPACITY-be.storedFe," in r
assert "be.waterMb=Math.max(0,be.waterMb-activity);" in r
assert "be.fuelTicks=Math.max(0,be.fuelTicks-activity);" in r
for rods in (0,1,2,15,25,64,100):
 old_max=120*rods
 new_max=600*rods
 assert new_max==5*old_max
 for inserted in (0,10,50,90,100):
  # Original truncation/order retained; no fractional FE inflation.
  old=rods*120*20*(100-inserted)//100
  new=rods*600*20*(100-inserted)//100
  assert new==old*5, (rods,inserted,old,new)
assert 600*15==9000
assert 600*15*(100-90)//100==900
print("B577_REACTOR_ALL_SIZES_5X_REAL_OUTPUT_MAX_RATE_ROD_INSERTION_PASS")
