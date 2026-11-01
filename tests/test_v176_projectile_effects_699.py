#!/usr/bin/env python3
"""B699 tracer + impact particles on actual finite-lifetime bullet."""
import os,subprocess,sys,tempfile,unittest
from pathlib import Path
SCRIPT=Path(__file__).resolve().parents[1]/"features/v176/apply-v176-projectile-effects-699.py"
class BulletEffectsTest(unittest.TestCase):
 def test_real_bullet_tracer_and_impact_sparks(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/"dev/obsidiannetwork/powerarmor/V176MicroMgProjectile.java"
   path.parent.mkdir(parents=True)
   path.write_text('''import net.minecraft.server.level.ServerLevel;
   discard();
  }
 }
 @Override protected void onHitBlock(BlockHitResult hit){
  if(!level().isClientSide())discard();
 }
 @Override public void tick(){
  super.tick();
  if(!level().isClientSide()&&tickCount>8)discard(); // 3 blocks/tick, max ~24 blocks
 }
''')
   env={**os.environ,"V1_SOURCE_ROOT":tmp}
   p=subprocess.run([sys.executable,str(SCRIPT)],env=env,capture_output=True,text=True)
   self.assertEqual(p.returncode,0,p.stdout+p.stderr)
   s=path.read_text()
   self.assertEqual(s.count("sendParticles(ParticleTypes.CRIT"),2)
   self.assertIn("level().addParticle(ParticleTypes.END_ROD,getX()",s)
   self.assertIn("else if(tickCount>8)discard()",s)
   self.assertNotIn("if(!level().isClientSide())discard()",s)
   p=subprocess.run([sys.executable,str(SCRIPT)],env=env,capture_output=True,text=True)
   self.assertNotEqual(p.returncode,0)
if __name__=="__main__":unittest.main()
