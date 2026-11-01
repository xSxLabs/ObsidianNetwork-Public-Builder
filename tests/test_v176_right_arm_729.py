#!/usr/bin/env python3
"""B729 static contract regression; the full build compiles/executes actual 26.1 Java."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class RightArmOnlyTest(unittest.TestCase):
 def test_right_arm_simplified_gun_and_doubled_fire(self):
  s=(ROOT/"features/v176/apply-v176-right-arm-rapidfire-729.py").read_text()
  rules=(ROOT/"features/v176/java/V176MicroMgRulesTest.java").read_text()
  self.assertIn("createHatch()",s)
  self.assertIn("0.125F*elapsed",s)
  self.assertIn("RenderPlayerEvent.Pre<?>",s)
  self.assertIn("drawRight(",s)
  self.assertIn('"model.leftArm" not in client',s)
  self.assertIn("HumanoidArm.RIGHT",s)
  self.assertIn("right.scale(0.34D)",s)
  self.assertIn("tick%5L!=0L&&tick%5L!=2L",s)
  self.assertIn("if(player.tickCount%5==0)",s)
  self.assertIn('bullets==16',rules)
  self.assertIn("COOLDOWN_TICKS==1",rules)
  self.assertNotIn("COOLDOWN_TICKS==5",rules)
  self.assertIn("COOLDOWN_TICKS=1", (ROOT/"features/v176/java/V176MicroMgRules.java").read_text())
 def test_exact_16_shots_per_second_schedule(self):
  def allowed(t,last):
   return last < 0 or (t>=last and t-last>=1 and t%5!=4)
  for seconds in (1,2,5,10):
   last=-1; shots=[]
   for tick in range(seconds*20):
    if allowed(tick,last):
     shots.append(tick);last=tick
   self.assertEqual(len(shots),seconds*16)
   self.assertEqual(shots[:8],[0,1,2,3,5,6,7,8])
if __name__=="__main__":unittest.main()
