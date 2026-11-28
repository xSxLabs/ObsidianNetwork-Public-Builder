#!/usr/bin/env python3
"""v21 regression checks for the Mining Builder's user-visible GUI text layout."""
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v178/apply-v178-v21-b1895-miner-gui-layout.py").read_text("utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text("utf-8")

class MiningBuilderGuiV21(unittest.TestCase):
 def test_three_labels_have_separate_rows(self):
  self.assertIn('g.text(font,"Insert configured card",x+14,y+51',PATCH)
  self.assertIn('g.text(font,"SPEED "+Math.min(16,installed)+"/16",x+105,y+62',PATCH)
  self.assertIn('g.text(font,"INVENTORY",8,74',PATCH)
  # 9-pixel Minecraft HUD font, with >1 px gap on both boundaries.
  self.assertLess(51+9,62)
  self.assertLess(62+9,74)
  self.assertLess(74+9,84) # first inventory row begins at y+84
  # The patch must explicitly validate that legacy help is absent from Java.
  self.assertIn("assert 'g.text(font,\"Drag a configured card\"' not in s",PATCH)
  self.assertIn("assert 'g.text(font,\"into the real card slot\"' not in s",PATCH)
 def test_slots_and_functionality_unchanged(self):
  for anchor in ('new Slot(base.container,0,20,27)',
                 'new Slot(speedSlot.container,1,143,27)',
                 'for(int i=2;i<27;i++){',
                 'int sy=y+(i<27?84+(i/9)*18:142)'):
   self.assertIn(anchor,PATCH)
  self.assertNotIn("B1895_V21_GUI_LAYOUT_CONTRACT",WF)
 def test_build_delivers_correct_version(self):
  self.assertIn('apply-v178-v21-b1895-miner-gui-layout.py',WF)
  self.assertIn("test_v178_b1895_miner_gui_layout.py",WF)
  self.assertIn("xSxLabs-Network-Storage-1.7.8-v21.jar",WF)
  self.assertIn("xsxlabs-network-storage-1.7.8-v21",WF)
  self.assertLess(WF.index("apply-v178-v20-b1883-stable-claim-map.py"),
                  WF.index("apply-v178-v21-b1895-miner-gui-layout.py"))

if __name__=="__main__":
 unittest.main()
