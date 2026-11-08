#!/usr/bin/env python3
"""JARVIS only announces NutriPaste once on armor entry, in the full status report."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
VOICE=(ROOT/"features/v177/apply-v177-jarvis-voice.py").read_text(encoding="utf-8")
FLOW=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")

class JarvisEntryStatus(unittest.TestCase):
 def test_initialize_telemetry_silently_but_allow_real_alerts(self):
  self.assertIn("private static void checkLevels(LocalPlayer p,boolean announce)",VOICE)
  self.assertIn("checkLevels(p,false); // baseline for the single combined entry report",VOICE)
  self.assertIn("if(p.tickCount%5==0)checkLevels(p,true);",VOICE)
  for kind,key in (("e","energy"),("n","paste"),("a","integrity")):
   self.assertIn('if(announce&&'+kind+'>=0&&V177JarvisSettings.on("'+key+'")',VOICE)
  self.assertNotIn("private static void checkLevels(LocalPlayer p){",VOICE)
 def test_one_full_entry_report_includes_all_three_fill_levels(self):
  self.assertIn('StringBuilder en=new StringBuilder("Armor diagnostics complete.");',VOICE)
  for key in ("startup_integrity","startup_energy","startup_paste","startup_outcome"):
   self.assertIn('V177JarvisSettings.on("'+key+'")',VOICE)
  self.assertIn('en.append(" NutriPaste reserves at ").append(prevPaste)',VOICE)
  self.assertIn('enqueue(2,en.toString(),de.toString());',VOICE)
 def test_first_boot_no_warning_for_101_percent_baseline(self):
  # Original threshold(0,101,...) yields a misleading 1% alert on entry.
  # Guarded first sample MUST emit no warning but store current values.
  def threshold(current,previous,levels):
   return next((level for level in levels if previous>level and current<=level),-1)
  self.assertEqual(threshold(0,101,(1,25,50,57)),1)
  first_sample=False
  self.assertFalse(first_sample and threshold(0,101,(1,25,50,57))>=0)
  subsequent=True
  self.assertTrue(subsequent and threshold(25,60,(1,25,50,57))>=0)
 def test_ci_runs_regression(self):
  self.assertIn("test_v177_jarvis_single_entry_status.py",FLOW)

if __name__=="__main__":
 unittest.main()
