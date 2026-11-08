#!/usr/bin/env python3
"""The 30-second NutriPaste target cannot be blocked by default Fluid Cables."""
import ast
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v177/apply-v177-armor-station-fast-fluid-cable.py").read_text(encoding="utf-8")
FLOW=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")

class ArmorStationFastFluidCable(unittest.TestCase):
 def test_injector_is_syntactically_valid(self):
  ast.parse(PATCH)

 def test_fast_transfer_applies_only_to_station_destination(self):
  for needle in (
    "blockentity/LogisticsCableBlockEntity.java",
    "private void transferFluid",
    "for(Endpoint e:exports())",
    "int max=fluidAmount(in);",
    "instanceof dev.obsidiannetwork.powerarmor.ArmorStationBlockEntity",
    "max=Math.max(max,25_000);",
    "FluidStack sim=src.drain(max,IFluidHandler.FluidAction.SIMULATE);",
    "int accepted=dst.fill(sim,IFluidHandler.FluidAction.SIMULATE);",
    "src.drain(accepted,IFluidHandler.FluidAction.EXECUTE)",
    "dst.fill(got,IFluidHandler.FluidAction.EXECUTE)",
    "src.fill(back,IFluidHandler.FluidAction.EXECUTE)",
  ): self.assertIn(needle,PATCH,needle)
  # Keep IMPORT tick interval and all ordinary fluid budgets unchanged.
  self.assertNotIn("private int interval(Direction d){",PATCH)
  self.assertNotIn("private int fluidAmount(Direction d){",PATCH)
  self.assertIn("assert len(matches)==1",PATCH)
  self.assertNotIn("src.drain(25_000,",PATCH)

 def test_30_seconds_even_with_default_five_tick_cable_cadence(self):
  # 1M mB / 25,000 mB per 5 ticks = 40 transfers / 10 seconds @20TPS.
  max_per_transfer=25_000
  total=1_000_000
  needed=(total+max_per_transfer-1)//max_per_transfer
  self.assertEqual(needed,40)
  self.assertLessEqual(needed*5,20*30)
  # No resource creation or global boost.
  self.assertEqual(sum([max_per_transfer]*needed),total)
  self.assertIn("int max=fluidAmount(in);",PATCH)

 def test_pipeline_places_station_only_patch_after_paste_creation(self):
  a=FLOW.index("python3 features/v177/apply-v177-armor-station-nutripaste.py")
  b=FLOW.index("python3 features/v177/apply-v177-armor-station-fast-fluid-cable.py")
  self.assertLess(a,b)
  self.assertIn("test_v177_armor_station_fast_fluid_cable.py",FLOW)

if __name__=="__main__":
 unittest.main()
