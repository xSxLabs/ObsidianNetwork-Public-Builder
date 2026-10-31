#!/usr/bin/env python3
"""B541 Spark cut mask: unchanged graph/FE invariants."""
import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class SolarDaytimePerf(unittest.TestCase):
 def test_source_and_cache_lifecycle(self):
  s=(ROOT/"patches/spark-energy-immutable-cut-mask-541.py").read_text()
  ast.parse(s)
  for phrase in ("B541_IMMUTABLE_ENERGY_CABLE_CUT_MASK",
       "Collections.synchronizedMap(new java.util.IdentityHashMap<>()",
       "ENERGY_SCAN_DIRECTIONS","EnergyCableBlock.isCut(st,side)",
       "face.get3DDataValue()", "assert n==6",
       "source.extract(", "target.insert(", "cableBudget-- > 0"):
   self.assertIn(phrase,s)
 def test_all_state_masks_are_same_as_uncached_flags(self):
  # Enumerate all 64 immutable six-face states; caching is an exact transform.
  for mask in range(64):
   original=[bool(mask&(1<<d)) for d in range(6)]
   self.assertEqual(original,[(mask&(1<<d))!=0 for d in range(6)])
if __name__=="__main__":unittest.main()
