#!/usr/bin/env python3
"""B698 fast and fail-closed: player/suit transfer and alternating turret muzzle."""
import os,sys,subprocess,tempfile,unittest
from pathlib import Path
PATCH=Path(__file__).resolve().parents[1]/"features/v176/apply-v176-muzzle-state-698.py"

class MuzzleStateTests(unittest.TestCase):
 def test_muzzle_and_disarm_on_equip(self):
  with tempfile.TemporaryDirectory() as tmp:
   j=Path(tmp)/"dev/obsidiannetwork"
   files={
    "powerarmor/V176CompanionMode.java":'''
 private static final Map<ArmorStand,Long> LAST_SHOT=new WeakHashMap<>();
  if(turret&&!hasModule(suit)){
   suit.removeTag(TURRET);
   return;
  }
   Vec3 dir=end.subtract(start).normalize();
   var shot=new V176MicroMgProjectile(
   shot.setPos(start.x,start.y,start.z);
   shot.shoot(dir.x,dir.y,dir.z,3.0F,0.7F);
   world.sendParticles(ParticleTypes.END_ROD,start.x,start.y,start.z,
     2,0.05,0.05,0.05,0.02);
  display(player,(turret?"Turret":"Follow")+" Mode: "+(was?"OFF":"ON"));
   shot.addTag("xsxlabs_v176_automatic_bullet");
''',
    "powerarmor/V176AttackModeServer.java":'''
  ItemStack chest=p.getItemBySlot(EquipmentSlot.CHEST);
  if(!PowerArmorRuntime.full(p)||!PowerArmorRuntime.hasCard(p,"micro_mg")){
''',
    "powerarmor/PowerArmorSuitWorld.java":'''
   V176AttackModeServer.clearFromChest(worn.get(1));
'''
   }
   for name,body in files.items():
    p=j/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(body)
   env={**os.environ,"V1_SOURCE_ROOT":tmp}
   r=subprocess.run([sys.executable,str(PATCH)],env=env,capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stdout+r.stderr)
   mode=(j/"powerarmor/V176CompanionMode.java").read_text()
   self.assertIn('((now/5L)&1L)==0L?0.27D:-0.27D',mode)
   self.assertIn('Vec3 muzzle=start.add(right.scale(barrelSide))',mode)
   self.assertIn('shot.setPos(muzzle.x,muzzle.y,muzzle.z)',mode)
   self.assertIn('world.clip(new ClipContext(muzzle,end',mode)
   self.assertIn('V176CompanionMode.clearTurretToken(chest);',
                 (j/"powerarmor/V176AttackModeServer.java").read_text())
   self.assertIn('V176CompanionMode.clearTurretToken(worn.get(1));',
                 (j/"powerarmor/PowerArmorSuitWorld.java").read_text())
   self.assertEqual(mode.count('display(player,(turret?"Turret":"Follow")+" Mode: "+(was?"OFF":"ON"));'),1)
   second=subprocess.run([sys.executable,str(PATCH)],env=env,capture_output=True,text=True)
   self.assertNotEqual(second.returncode,0)
if __name__=="__main__":unittest.main()
