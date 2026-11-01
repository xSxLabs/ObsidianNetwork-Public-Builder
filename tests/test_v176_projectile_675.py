#!/usr/bin/env python3
"""B675 test of unique anchors and physical entity/C2S authoritative gates."""
import os,subprocess,sys,tempfile,unittest
from pathlib import Path
PATCH=Path(__file__).resolve().parents[1]/"features/v176/apply-v176-projectile-675.py"
class ProjectileTest(unittest.TestCase):
 def test_bullet_and_fire_gates(self):
  with tempfile.TemporaryDirectory() as tmp:
   j=Path(tmp)/"dev/obsidiannetwork"; (j/"powerarmor").mkdir(parents=True)
   (j/"ObsidianNetwork.java").write_text('''   public static final net.neoforged.neoforge.registries.DeferredHolder<
      net.minecraft.world.entity.EntityType<?>,
      net.minecraft.world.entity.EntityType<dev.obsidiannetwork.powerarmor.PowerArmorStand>> POWER_ARMOR_WORLD_MK1 =''')
   (j/"powerarmor/PowerArmorCommands.java").write_text(
    '   .then(Commands.literal("attack").executes(c->V176AttackModeServer.toggle(c.getSource().getPlayerOrException()))));')
   cp=subprocess.run([sys.executable,str(PATCH)],env={**os.environ,"V1_SOURCE_ROOT":tmp},capture_output=True,text=True)
   self.assertEqual(cp.returncode,0,cp.stdout+cp.stderr)
   projectile=(j/"powerarmor/V176MicroMgProjectile.java").read_text()
   fire=(j/"powerarmor/V176MicroMgFire.java").read_text()
   client=(j/"client/V176MicroMgFireClient.java").read_text()
   self.assertIn('extends ThrowableItemProjectile',projectile)
   self.assertIn('damageSources().thrown(this,owner)',projectile)
   self.assertIn('EnergyTool.consume(chest,V176MicroMgRules.FE_PER_SHOT)',fire)
   self.assertIn('V176LootingEvents.mark(shot,V176LootingSupport.level(upgrades))',fire)
   self.assertIn('if(!world.addFreshEntity(shot))return 0;',fire)
   self.assertIn('e.setCanceled(true)',client)
   self.assertIn('glfwGetMouseButton',client)
   cp2=subprocess.run([sys.executable,str(PATCH)],env={**os.environ,"V1_SOURCE_ROOT":tmp},capture_output=True,text=True)
   self.assertNotEqual(cp2.returncode,0)
if __name__=="__main__":unittest.main()
