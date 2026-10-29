#!/usr/bin/env python3
"""Regression for FE decoration flicker with wireless recharge + armor drain."""
import ast
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v173/apply-armor-fe-bar-stability-365.py"
WF=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"

ORIGINAL="""package dev.obsidiannetwork.core;
import net.minecraft.world.item.ItemStack;
public final class EnergyTool {
 public static long capacity(ItemStack s){return 4000000L;}
 public static long energy(ItemStack s){return 4000000L;}
 public static void setEnergy(ItemStack s,long v){}
 public static int barWidth(ItemStack s){return (int)Math.max(0L,Math.min(13L,(13L*energy(s))/capacity(s)));}
 public static int barColor(ItemStack s){return net.minecraft.util.ARGB.color(255,255,0,0);}
}
"""

def expected_width(charge,capacity):
 return max(0,min(13,math.floor(13.0*charge/capacity+0.5)))

class ArmorFEBarStability365(unittest.TestCase):
 def test_patch_syntax_and_full_source_rewrite(self):
  ast.parse(PATCH.read_text(encoding="utf-8"))
  with tempfile.TemporaryDirectory() as td:
   f=Path(td)/"dev/obsidiannetwork/core/EnergyTool.java"
   f.parent.mkdir(parents=True)
   f.write_text(ORIGINAL)
   args=[sys.executable,str(PATCH)]
   first=subprocess.run(args,capture_output=True,text=True,
                        env={**os.environ,"V1_SOURCE_ROOT":td})
   self.assertEqual(first.returncode,0,first.stdout+first.stderr)
   changed=f.read_text()
   self.assertIn("V173_B365_STABLE_ARMOR_FE_BAR",changed)
   self.assertIn("Math.round(13.0D*energy(s)/(double)capacity(s))",changed)
   self.assertIn("public static int barColor(ItemStack s)",changed)
   self.assertIn("public static void setEnergy(ItemStack s,long v){}",changed)
   self.assertNotIn("(13L*energy(s))/capacity(s)",changed)
   # Fail closed instead of silently reapplying against an unknown class.
   second=subprocess.run(args,capture_output=True,text=True,
                         env={**os.environ,"V1_SOURCE_ROOT":td})
   self.assertNotEqual(second.returncode,0)
   self.assertEqual(f.read_text(),changed)

 def test_charge_oscillations_stable_but_large_loss_visible(self):
  cap=4_000_000
  # 1...50,000 FE drains from full and small wireless top-ups
  # must never change the full 13-pixel bar.
  for loss in [0,1,20,64,250,1000,10000,50000,100000]:
   self.assertEqual(expected_width(cap-loss,cap),13,loss)
  self.assertLess(expected_width(cap-250000,cap),13)
  self.assertEqual(expected_width(0,cap),0)
  self.assertEqual(expected_width(cap//2,cap),7)
  self.assertEqual(expected_width(cap,cap),13)
  # All widths are monotone as remaining FE increases.
  widths=[expected_width(e,cap) for e in range(0,cap+1,10000)]
  self.assertEqual(widths,sorted(widths))

 def test_only_rendered_width_changes(self):
  s=PATCH.read_text(encoding="utf-8")
  for unsafe in ("setEnergy(s,","WirelessPlayerCharging.java","consume(ItemStack","EnergyToolEvents.java",
                 "setBlockAndUpdate(","ENERGY_TOOL_FE.get(),"):
   self.assertNotIn(unsafe,s)

 def test_workflow_calls_patch_after_existing_features(self):
  s=WF.read_text(encoding="utf-8")
  self.assertIn("python3 features/v173/apply-armor-fe-bar-stability-365.py",s)
  self.assertIn("test_v173_armor_fe_bar_stability_365.py",s)
  self.assertLess(s.index("python3 features/v173/apply-hologram-text-bundle-362.py"),
                  s.index("python3 features/v173/apply-armor-fe-bar-stability-365.py"))

if __name__=="__main__":unittest.main()
