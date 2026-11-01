#!/usr/bin/env python3
"""B757 26.1 patch fixture and complete 16/20 tick fire-cycle regression."""
import ast,os,subprocess,sys,tempfile,unittest,json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v176/apply-v176-ingame-feedback-757.py"
RULES=ROOT/"features/v176/java/V176MicroMgRules.java"

class Ingame757(unittest.TestCase):
 def test_staged_java_overlay_icon_and_idempotence(self):
  tree=ast.parse(PATCH.read_text(encoding="utf-8"))
  calls=[x.value for x in tree.body if isinstance(x,ast.Expr)
    and isinstance(x.value,ast.Call) and isinstance(x.value.func,ast.Name)
    and x.value.func.id=="edit"]
  self.assertGreaterEqual(len(calls),15)
  per={}
  for x in calls:
   rel,old=[ast.literal_eval(z) for z in x.args[:2]]
   per.setdefault(rel,[]).append(old)
  with tempfile.TemporaryDirectory() as td:
   j=Path(td)/"dev/obsidiannetwork"
   for rel,olds in per.items():
    p=j/rel;p.parent.mkdir(parents=True,exist_ok=True)
    self.assertEqual(len(olds),len(set(olds)),rel)
    p.write_text("\n".join(olds),encoding="utf-8")
   r=Path(td)/"assets/obsidiannetwork"
   icon=r/"textures/item/power_card_micro_mg.png"
   icon.parent.mkdir(parents=True)
   Image.new("RGBA",(32,32),(255,255,255,255)).save(icon)
   model=r/"models/item/power_card_micro_mg.json"
   model.parent.mkdir(parents=True)
   model.write_text(json.dumps({"textures":{"layer0":"obsidiannetwork:item/power_card_micro_mg"}}))
   env={**os.environ,"V1_SOURCE_ROOT":td,"V1_RESOURCE_ROOT":td}
   run=subprocess.run([sys.executable,str(PATCH)],env=env,capture_output=True,text=True)
   self.assertEqual(run.returncode,0,run.stdout+run.stderr)
   self.assertIn("V176_B757_16RPS_PLAYER_FIRSTPERSON_TURRET_FOLLOW_GLASS_ICE_ICON_PASS",run.stdout)
   v=(j/"client/V176MicroMgVisualClient.java").read_text()
   m=(j/"powerarmor/V176CompanionMode.java").read_text()
   p=(j/"powerarmor/V176MicroMgProjectile.java").read_text()
   fire=(j/"client/V176MicroMgFireClient.java").read_text()
   self.assertIn("rightArmPose=HumanoidModel.ArmPose.BLOCK",v)
   self.assertNotIn("submitModelPart(model.rightArm,",v)
   self.assertIn("getRightArmPose().x()<-45F",v)
   self.assertIn("setYBodyRot(yaw)",m)
   self.assertIn("setYHeadRot(yaw)",m)
   self.assertIn("destroyBlock(position,false,shooter)",p)
   self.assertIn("blockId.equals(\"packed_ice\")",p)
   self.assertIn('blockId.endsWith("_stained_glass_pane")',p)
   self.assertIn('next=tick+1L;',fire)
   self.assertEqual(json.loads(model.read_text())["textures"]["layer0"],"minecraft:item/nether_star")
   with Image.open(icon) as im:
    self.assertEqual(im.size,(32,32))
    self.assertEqual(im.getpixel((0,0))[3],0)
   again=subprocess.run([sys.executable,str(PATCH)],env=env,capture_output=True,text=True)
   self.assertNotEqual(again.returncode,0)

 def test_authority_exact_16_shots(self):
  rules=RULES.read_text()
  self.assertIn("COOLDOWN_TICKS=1",rules)
  self.assertIn("tick%5L!=4L",rules)
  last=-1;shots=[]
  for tick in range(20):
   if last<0 or (tick-last>=1 and tick%5!=4):
    shots.append(tick);last=tick
  self.assertEqual(shots,[0,1,2,3,5,6,7,8,10,11,12,13,15,16,17,18])
  self.assertEqual(len(shots)*3000,48000)
if __name__=="__main__":unittest.main()
