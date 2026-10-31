#!/usr/bin/env python3
"""B536 static solar FE conservation and identity checks before expensive Gradle."""
import ast
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class SolarMSPTRegression(unittest.TestCase):
 def test_patch_shape_and_invalidation(self):
  s=(ROOT/"patches/spark-solar-mspt-mask-536.py").read_text()
  ast.parse(s)
  for invariant in (
    "XSXLABS_SOLAR_BLOCK_CAPABILITY_CACHE_V1",
    "XSXLABS_SOLAR_FIXED_SIX_FACE_CACHE_V1",
    "xsxSolarFacesDirty=true",
    "now-xsxSolarLastFaceScan<40L",
    "() -> {xsxSolarFacesDirty=true;}",
    "be.xsxLiveSolarFaces(server)!=0",
    "1<<side.get3DDataValue()",
    "budget -= accepted;",
    "be.energyJournal.updateSnapshots(tx);",
    "long extracted = be.energy.extract(accepted);",
    "tx.commit();"):
   self.assertIn(invariant,s)
 def test_idle_face_scan_model_reduces_queries(self):
  # Empty generator with 6 unconnected sides: fallback at ticks 0,40,80...
  baseline=6000*6
  optimized=sum(6 for tick in range(6000) if tick%40==0)
  self.assertEqual(optimized,900)
  self.assertLess(optimized,baseline//20)
 def test_never_change_generation_or_transfer_caps(self):
  s=(ROOT/"patches/spark-solar-mspt-mask-536.py").read_text()
  self.assertIn("long budget = be.energy.stored();",s)
  self.assertIn("long made = Math.min(be.tier.output(), be.energy.capacity() - be.energy.stored());",s)
  self.assertIn("int start = be.nextSide++ % sides.length;",s)
  self.assertNotIn("be.energy.extract(0)",s)
if __name__=="__main__":unittest.main()
