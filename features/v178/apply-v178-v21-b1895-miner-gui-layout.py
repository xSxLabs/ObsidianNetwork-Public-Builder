#!/usr/bin/env python3
"""1.7.8 v21: mining-builder GUI labels no longer overlap.

Only client GUI text/background geometry is affected. The Shape Card,
16-upgrade input Slot, inventory routing, menu click semantics, renderer,
server mining logic, and FE/TPS budgets remain untouched.
Apply after B1815 and the full v20 patches.
"""
import os
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
p=J/"client/V178MiningBuilderOperationsScreen.java"
s=p.read_text("utf-8")

def replace_once(old,new):
    global s
    n=s.count(old)
    assert n==1,("B1895_V21_MINER_GUI_DRIFT",old,n)
    s=s.replace(old,new,1)

# The old 2-line help occupies y+57..77, and the speed label at y+56
# intersects it. Fit the help in one concise line, put speed beneath it
# and keep the inventory label above the first native row (y+84).
replace_once(
'''   g.text(font,"Drag a configured card",x+14,y+57,0xff8eacbb);
   g.text(font,"into the real card slot",x+14,y+68,0xff8eacbb);''',
'''   // B1895: a single short help line leaves a distinct speed row.
   g.text(font,"Insert configured card",x+14,y+51,0xff8eacbb);''')
replace_once(
'''   g.text(font,"SPEED "+Math.min(16,installed)+"/16",x+88,y+56,0xff66deee);''',
'''   // Separate from help (y+51) and INVENTORY (y+74), even at max GUI scale.
   g.text(font,"SPEED "+Math.min(16,installed)+"/16",x+105,y+62,0xff66deee);''')
replace_once(
'''   g.text(font,"INVENTORY",8,71,0xffa6c5d4);''',
'''   // Vanilla item-slot row begins at y+84: label fits fully above it.
   g.text(font,"INVENTORY",8,74,0xffa6c5d4);''')
# Keep the dark help surface within its own section. The inventory title
# follows below, not on top of the status/slot instructions.
replace_once(
'''   g.fill(x+5,y+18,x+171,y+78,0xff102335);''',
'''   g.fill(x+5,y+18,x+171,y+72,0xff102335);''')
for token in (
  'new Slot(base.container,0,20,27)',
  'new Slot(speedSlot.container,1,143,27)',
  'for(int i=2;i<27;i++){',
  'g.text(font,"SHAPE CARD",x+47,y+31',
  'g.text(font,"Insert configured card",x+14,y+51',
  'g.text(font,"SPEED "+Math.min(16,installed)+"/16",x+105,y+62',
  'g.text(font,"INVENTORY",8,74',
  'int sy=y+(i<27?84+(i/9)*18:142)',
):
    assert token in s,("B1895_V21_GUI_LAYOUT_CONTRACT",token)
assert 'g.text(font,"Drag a configured card"' not in s
assert 'g.text(font,"into the real card slot"' not in s
p.write_text(s,"utf-8")
print("B1895_V21_MINER_HELP_SPEED_INVENTORY_NO_OVERLAP_PASS")
