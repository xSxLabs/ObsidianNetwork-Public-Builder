#!/usr/bin/env python3
"""v21: Mining Builder GUI layout only; preserve native slots and server logic.

Apply after the v20 patches. Replace each unique Java statement independently
rather than anchoring multi-line blocks with generator-dependent indentation.
"""
import os
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
p=J/"client/V178MiningBuilderOperationsScreen.java"
s=p.read_text("utf-8")

def replace_once(old,new):
    global s
    assert s.count(old)==1,("B1895_V21_MINER_GUI_DRIFT",old,s.count(old))
    s=s.replace(old,new,1)

# Single concise help text row (y=51), with speed moved to y=62
# and inventory at y=74. Native item slots start at y=84.
replace_once(
 'g.text(font,"Drag a configured card",x+14,y+57,0xff8eacbb);',
 'g.text(font,"Insert configured card",x+14,y+51,0xff8eacbb);')
replace_once(
 'g.text(font,"into the real card slot",x+14,y+68,0xff8eacbb);',
 '// B1895: folded into the short instruction above.')
replace_once(
 'g.text(font,"SPEED "+Math.min(16,installed)+"/16",x+88,y+56,0xff66deee);',
 'g.text(font,"SPEED "+Math.min(16,installed)+"/16",x+105,y+62,0xff66deee);')
replace_once(
 'g.text(font,"INVENTORY",8,71,0xffa6c5d4);',
 'g.text(font,"INVENTORY",8,74,0xffa6c5d4);')
replace_once(
 'g.fill(x+5,y+18,x+171,y+78,0xff102335);',
 'g.fill(x+5,y+18,x+171,y+72,0xff102335);')

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
