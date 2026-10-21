#!/usr/bin/env python3
"""Network Elytra build 368 regression: Curios optional, client motion and custom assets."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
S=(ROOT/"features/wireless-energy/apply-network-elytra-hotfix.py").read_text()
T=(ROOT/"patches/terminal-live-storage-meter.py").read_text()
class ElytraAndMeterRegressions(unittest.TestCase):
 def test_curios_not_classloaded_when_absent(self):
  self.assertIn('isLoaded("curios")',S)
  self.assertIn('NetworkElytraCurios.find(player)',S)
  self.assertIn('NetworkElytraCuriosGlideMixin',S)
  self.assertIn('@Inject(method="canGlide"',S)
  self.assertIn('result.setReturnValue(true)',S)
  self.assertNotIn('NeoForgeMod.GLIDING_FLIGHT',S)
  self.assertIn('if(inv.isEmpty())return ItemStack.EMPTY;',S)
  self.assertIn('for(String slot : new String[]{"back","elytra"})',S)
 def test_server_and_client_motion(self):
  self.assertIn('player.setDeltaMovement(next)',S)
  self.assertIn('ClientTickEvent.Post',S)
  self.assertIn('mc.options.keyShift.isDown()',S)
  self.assertIn('SHIFT_COST_PER_5_TICKS',S)
 def test_elytra_models_and_tags(self):
  self.assertIn('equipment/network_elytra.json',S)
  self.assertIn('wings/network_elytra.png',S)
  self.assertIn('textures/item/network_elytra.png',S)
  self.assertIn('data/curios/tags/item/',S)
 def test_meter_is_footer_not_sort_header(self):
  self.assertIn('this.imageHeight*61',T)
  self.assertNotIn('this.topPos+8;',T)
  self.assertIn('xsxBarX=xsxX-38',T)
if __name__=="__main__":
 unittest.main()
