#!/usr/bin/env python3
"""Build 70: GeckoLib entities must have attribute suppliers before first spawn."""
import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v17/apply-power-armor-attributes-70.py").read_text(encoding="utf-8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")
class PowerArmorAttributes70(unittest.TestCase):
 def test_valid_injector_and_mod_bus_lifecycle(self):
  ast.parse(PATCH)
  self.assertIn("EntityAttributeCreationEvent event",PATCH)
  self.assertIn("@EventBusSubscriber(modid=",PATCH)
  self.assertIn("LivingEntity.createLivingAttributes().build()",PATCH)
 def test_all_four_entity_types(self):
  for kind in ("ARMOR_VISUAL_ENTITY_MK1","ARMOR_VISUAL_ENTITY_MK2",
               "POWER_ARMOR_WORLD_MK1","POWER_ARMOR_WORLD_MK2"):
   self.assertIn("event.put(ObsidianNetwork."+kind+".get(),vanillaStandBase)",PATCH)
 def test_order_after_existing_reliability_and_before_runtime_gametests(self):
  self.assertLess(WF.index("python3 features/v17/apply-power-armor-reliability-65.py"),
                  WF.index("python3 features/v17/apply-power-armor-attributes-70.py"))
  self.assertLess(WF.index("python3 features/v17/apply-power-armor-attributes-70.py"),
                  WF.index("python3 features/v17/inject-power-armor-roundtrip-gametest-69.py"))
if __name__=="__main__": unittest.main()
