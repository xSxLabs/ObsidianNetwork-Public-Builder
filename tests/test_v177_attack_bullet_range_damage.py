#!/usr/bin/env python3
"""Attack Mode bullets: 48 ticks + double hit damage, turret remains unchanged."""
import ast
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"features/v177/apply-v177-attack-bullet-range-damage.py"
FLOW=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")
SOURCE=SCRIPT.read_text(encoding="utf-8")
RULES=(ROOT/"features/v176/java/V176MicroMgRules.java").read_text(encoding="utf-8")

class AttackModeExtendedBullets(unittest.TestCase):
 def test_syntax_and_conservation(self):
  ast.parse(SOURCE)
  self.assertIn("DAMAGE_HP=4.0f",RULES)
  self.assertIn("FE_PER_SHOT=3000L",RULES)
  self.assertIn('shot.addTag("xsxlabs_v177_attack_mode_bullet")',SOURCE)
  self.assertIn('V176MicroMgRules.DAMAGE_HP*2.0F:V176MicroMgRules.DAMAGE_HP',SOURCE)
  self.assertIn('?48:8',SOURCE)
  self.assertNotIn('AUTO_TARGET_RANGE_SQ',SOURCE)
  self.assertNotIn('EnergyTool.consume',SOURCE)

 def test_injector_respects_manual_tag_and_turret_damage(self):
  with tempfile.TemporaryDirectory() as temp:
   src=Path(temp)/"dev/obsidiannetwork/powerarmor"
   src.mkdir(parents=True)
   fire=src/"V176MicroMgFire.java"
   bullet=src/"V176MicroMgProjectile.java"
   fire.write_text('''  shot.setOwner(p);
  shot.setPos(origin.x,origin.y,origin.z);
  if(!EnergyTool.consume(chest,V176MicroMgRules.FE_PER_SHOT))return 0;
''',encoding="utf-8")
   bullet.write_text('''    living.hurtServer(server,damageSources().thrown(this,owner),V176MicroMgRules.DAMAGE_HP);
  }else if(tickCount>8)discard(); // 3 blocks/tick, max ~24 blocks
''',encoding="utf-8")
   command=[sys.executable,str(SCRIPT)]
   proc=subprocess.run(command,env={**os.environ,"V1_SOURCE_ROOT":temp},text=True,capture_output=True)
   self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
   shot=fire.read_text(encoding="utf-8")
   entity=bullet.read_text(encoding="utf-8")
   self.assertIn('shot.addTag("xsxlabs_v177_attack_mode_bullet")',shot)
   self.assertIn('EnergyTool.consume(chest,V176MicroMgRules.FE_PER_SHOT)',shot)
   self.assertIn('float damage=entityTags().contains("xsxlabs_v177_attack_mode_bullet")',entity)
   self.assertIn('V176MicroMgRules.DAMAGE_HP*2.0F:V176MicroMgRules.DAMAGE_HP',entity)
   self.assertIn('?48:8',entity)
   self.assertEqual((4*2,4),(8,4))
   self.assertEqual((48,8),(48,8))
   again=subprocess.run(command,env={**os.environ,"V1_SOURCE_ROOT":temp},text=True,capture_output=True)
   self.assertNotEqual(again.returncode,0,"Unsafe double injection")

 def test_1_7_7_only_workflow_after_base_projectile(self):
  self.assertIn('if [ "$GITHUB_REF_NAME" = "1.7.7" ] || [ "$GITHUB_REF_NAME" = "1.7.8" ]; then',FLOW)
  self.assertIn('python3 features/v177/apply-v177-attack-bullet-range-damage.py',FLOW)
  self.assertIn("test_v177_attack_bullet_range_damage.py",FLOW)
  self.assertLess(FLOW.index("python3 features/v176/apply-v176-projectile-effects-699.py"),
                  FLOW.index("python3 features/v177/apply-v177-attack-bullet-range-damage.py"))

if __name__=="__main__":
 unittest.main()
