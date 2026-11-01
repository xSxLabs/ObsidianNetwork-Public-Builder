#!/usr/bin/env python3
"""B696/B697 fast preflight: fail-closed anchors, client sync, 24 3D barrels."""
import os,subprocess,sys,tempfile,unittest
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
SAFE=ROOT/"features/v176/apply-v176-safety-696.py"
VISUAL=ROOT/"features/v176/apply-v176-visual-697.py"

class ArmorGunsFinalTests(unittest.TestCase):
 def test_runtime_and_24_variant_visuals(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);j=root/"src/dev/obsidiannetwork";a=root/"resources/assets/obsidiannetwork"
   for tier in range(1,25):
    stem="power_armor" if tier==1 else f"power_armor_mk{tier}"
    dest=a/"textures/entity/equipment/humanoid"/(stem+".png")
    dest.parent.mkdir(parents=True,exist_ok=True)
    Image.new("RGBA",(64,32),(45+tier*4%150,85+tier*3%100,100+tier*2%70,255)).save(dest)
   fixtures={
     "powerarmor/PowerArmorSuitWorld.java":
       '   stand.setInvisible(false);\n   pose(stand,0,false);\n',
     "client/V176CompanionClient.java":
       '    new AABB(mc.player.blockPosition()).inflate(16.0D),s->{\n'
       '      int tier=PowerArmorRuntime.tier(s.getItemBySlot(EquipmentSlot.HEAD),0);\n',
     "powerarmor/V176MicroMgProjectile.java":
       '      &&!(target instanceof Player && !(owner instanceof Player))){\n'
       '    living.hurtServer(server,damageSources().thrown(this,owner),V176MicroMgRules.DAMAGE_HP);\n'
       'if(!level().isClientSide()&&tickCount>12)discard(); // never unbounded',
     "powerarmor/V176MicroMgFire.java":
       '  long previous=LAST.getOrDefault(p.getUUID(),-1L);',
     "powerarmor/V176CompanionMode.java":
       '  ArmorStand suit=find(player,72.0D);\n'
       '  if(suit==null||suit.isInvisible())return;\n'
       '  if(!was)suit.addTag(requested);\n'
       '  display(player,(turret?"Turret":"Follow")+" Mode: "+(was?"OFF":"ON"));\n'
       '  if(!turret||!hasModule(suit))return;\n'
       '  ItemStack chest=suit.getItemBySlot(EquipmentSlot.CHEST);\n'
       '   shot.setOwner(player);\n'
       '   shot.setPos(start.x,start.y,start.z);\n'
       '  long now=world.getGameTime(),last=LAST_SHOT.getOrDefault(suit,-1L);'
   }
   for rel,body in fixtures.items():
    p=j/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(body)
   env={**os.environ,"V1_SOURCE_ROOT":str(root/"src"),
                     "V1_RESOURCE_ROOT":str(root/"resources")}
   for path in (SAFE,VISUAL):
    proc=subprocess.run([sys.executable,str(path)],env=env,
        capture_output=True,text=True)
    self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
   companion=(j/"powerarmor/V176CompanionMode.java").read_text()
   shot=(j/"powerarmor/V176MicroMgProjectile.java").read_text()
   owner=(j/"powerarmor/PowerArmorSuitWorld.java").read_text()
   client=(j/"client/V176CompanionClient.java").read_text()
   self.assertIn("micro_mg_turret_on",companion)
   # Follow/Turret: display ON/OFF only when a command toggles the mode.
   self.assertEqual(companion.count('display(player,(turret?"Turret":"Follow")+" Mode: "+(was?"OFF":"ON"));'),1)
   self.assertIn('shot.addTag("xsxlabs_v176_automatic_bullet")',companion)
   self.assertIn('target instanceof net.minecraft.world.entity.monster.Monster',shot)
   self.assertIn('stand.setCustomNameVisible(false)',owner)
   self.assertIn("getCustomName().getString()",client)
   self.assertNotIn("s.entityTags().contains",client)
   renderer=(j/"client/V176MicroMgVisualClient.java").read_text()
   for kind in ("RenderPlayerEvent.Post","RenderArmEvent","RenderLivingEvent.Post",
                "submitModelPart","micro_mg_turret_on","micro_mg_on"):
    self.assertIn(kind,renderer)
   for tier in range(1,25):
    asset=a/"textures/entity"/(f"micro_mg_mk{tier}.png")
    self.assertTrue(asset.exists(),tier)
    with Image.open(asset) as image:self.assertEqual(image.size,(32,32))
   proc=subprocess.run([sys.executable,str(VISUAL)],env=env,capture_output=True,text=True)
   self.assertNotEqual(proc.returncode,0,"visual overlay must fail closed on duplicate")

if __name__=="__main__":unittest.main()
