#!/usr/bin/env python3
import os,subprocess,sys,tempfile,unittest
from pathlib import Path
PATCH=Path(__file__).resolve().parents[1]/"features/v176/apply-v176-companion-676.py"
class TestCompanion(unittest.TestCase):
 def test_two_modes_and_module_gate(self):
  with tempfile.TemporaryDirectory() as tmp:
   j=Path(tmp)/"dev/obsidiannetwork";(j/"powerarmor").mkdir(parents=True);(j/"client").mkdir()
   (j/"powerarmor/PowerArmorCommands.java").write_text(
    '   .then(Commands.literal("fire").executes(c->V176MicroMgFire.fire(c.getSource().getPlayerOrException()))));')
   (j/"client/NetworkActionWheelClient.java").write_text('''
 private static int[] wheelActions(boolean vision,boolean attack){
case 5->V176AttackModeClient.toggleFromWheel();
String name=i==4?"VISION":i==5?("ATTACK "+(V176AttackModeClient.active()?"ON":"OFF")):ACTIONS[i];
''')
   proc=subprocess.run([sys.executable,str(PATCH)],env={**os.environ,"V1_SOURCE_ROOT":tmp},text=True,capture_output=True)
   self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
   wheel=(j/"client/NetworkActionWheelClient.java").read_text()
   mode=(j/"powerarmor/V176CompanionMode.java").read_text()
   self.assertIn("case 6->V176CompanionClient.toggleFollow()",wheel)
   self.assertIn("case 7->V176CompanionClient.toggleTurret()",wheel)
   self.assertIn("if(turret&&!hasModule(suit))return 0;",mode)
   self.assertIn('suit.removeTag(FOLLOW);suit.removeTag(TURRET);',mode)
   self.assertIn('e->e.isAlive()&&!e.isAlliedTo(player)',mode)
   self.assertIn('new ClipContext(start,end',mode)
   self.assertIn('EnergyTool.consume(chest,V176MicroMgRules.FE_PER_SHOT)',mode)
   proc2=subprocess.run([sys.executable,str(PATCH)],env={**os.environ,"V1_SOURCE_ROOT":tmp},text=True,capture_output=True)
   self.assertNotEqual(proc2.returncode,0)
if __name__=="__main__":unittest.main()
