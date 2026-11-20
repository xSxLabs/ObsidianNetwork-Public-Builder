#!/usr/bin/env python3
"""B1687 flight radial server auth contract and no client gameplay privilege."""
import ast,os,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NAME="features/v178/apply-v178-b1687-fly-wheel.py"
SOURCE=(ROOT/NAME).read_text(encoding="utf8")
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
class FlyWheel1687(unittest.TestCase):
 def test_pipeline_and_syntax(self):
  ast.parse(SOURCE,filename=NAME)
  self.assertEqual(WF.count("python3 "+NAME),1)
  self.assertLess(WF.index("python3 features/v177/apply-v177-jarvis-voice.py"),
     WF.index("python3 "+NAME))
  self.assertIn("FLY ON",SOURCE)
  self.assertIn("FLY OFF",SOURCE)
 def test_authority_no_free_creative(self):
  for required in ("PowerArmorRuntime.full(p)",
       "PowerArmorRuntime.hasCardWithoutFlySwitch(p,",
       "p.getAbilities().mayfly=false;",
       "p.getAbilities().flying=false;",
       "p.onUpdateAbilities();",
       "return hasCardWithoutFlySwitch(",
       "mc.player.connection.sendCommand(",
       'if("flight".equals(', "V178FlyModuleSwitch.disabled(",
       "p.sendOverlayMessage(Component.literal(message))"):
   self.assertIn(required,SOURCE)
  self.assertNotIn("p.getAbilities().mayfly=true;",SOURCE)
 def test_generated_interfaces(self):
  root=os.getenv("V1_SOURCE_ROOT")
  if not root:return
  j=Path(root)/"dev/obsidiannetwork"
  for path in ("client/V178FlyModuleClient.java",
    "powerarmor/V178FlyModuleSwitch.java"):
   self.assertTrue((j/path).is_file(),path)
  wheel=(j/"client/NetworkActionWheelClient.java").read_text()
  self.assertIn("V178FlyModuleClient.withFly(",wheel)
  self.assertIn("V178FlyModuleClient.toggleFromWheel()",wheel)
  self.assertIn("V178FlyModuleClient.active()",wheel)
  runtime=(j/"powerarmor/PowerArmorRuntime.java").read_text()
  self.assertIn("public static boolean hasCardWithoutFlySwitch(",runtime)
  self.assertIn("V178FlyModuleSwitch.disabled(",runtime)
  server=(j/"powerarmor/V178FlyModuleSwitch.java").read_text()
  self.assertIn('notice(p,turnOn?"Fly ON',server)
  self.assertIn("!p.isCreative()&&!p.isSpectator()",server)
  self.assertIn('V178FlyModuleSwitch.toggle(', 
    (j/"powerarmor/PowerArmorCommands.java").read_text())
if __name__=="__main__":unittest.main()
