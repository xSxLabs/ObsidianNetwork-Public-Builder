#!/usr/bin/env python3
"""B532: source fixtures from B503+B530, 8 valid asset combinations."""
import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
SCRIPT=Path(__file__).resolve().parents[1]/"features/v174/apply-multiblock-lit-blockstates-531.py"
SKINS=("reactor_casing","reactor_glass","powerbank_casing","powerbank_glass")
class ModelGateTest(unittest.TestCase):
 def setUp(self):
  tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
  self.root=Path(tmp.name)
  a=self.root/"resources/assets/obsidiannetwork"
  (a/"blockstates").mkdir(parents=True);(a/"models/block").mkdir(parents=True)
  self.java=self.root/"java/dev/obsidiannetwork/multiblock/MultiblockSkinBlock.java"
  self.java.parent.mkdir(parents=True)
  self.java.write_text("""BooleanProperty ACTIVE=BooleanProperty.create("active");
BooleanProperty LIT=BooleanProperty.create("lit");
registerDefaultState(defaultBlockState().setValue(FORMED,false).setValue(ACTIVE,false));
builder.add(FORMED,ACTIVE);""")
  for name in SKINS:
   v={f"formed={str(f).lower()},active={str(ac).lower()}":{"model":"obsidiannetwork:block/"+name+("_formed" if f else "")} for f in (False,True) for ac in (False,True)}
   (a/"blockstates"/(name+".json")).write_text(json.dumps({"variants":v}))
   for suffix in ("","_formed"):(a/"models/block"/(name+suffix+".json")).write_text("{}")
 def run_patch(self):
  env=dict(os.environ,V1_RESOURCE_ROOT=str(self.root/"resources"),V1_SOURCE_ROOT=str(self.root/"java"))
  return subprocess.run([sys.executable,str(SCRIPT)],env=env,capture_output=True,text=True)
 def test_eight_states(self):
  r=self.run_patch();self.assertEqual(r.returncode,0,r.stderr)
  s=self.java.read_text()
  self.assertIn("builder.add(FORMED,ACTIVE,LIT);",s)
  self.assertIn("setValue(ACTIVE,false).setValue(LIT,false)",s)
  for name in SKINS:
   v=json.loads((self.root/"resources/assets/obsidiannetwork/blockstates"/(name+".json")).read_text())["variants"]
   self.assertEqual(len(v),8)
   for f in ("false","true"):
    for a in ("false","true"):
     for l in ("false","true"):
      self.assertEqual(v[f"formed={f},active={a},lit={l}"]["model"],"obsidiannetwork:block/"+name+("_formed" if f=="true" else ""))
 def test_missing_model_fails(self):
  (self.root/"resources/assets/obsidiannetwork/models/block/reactor_glass_formed.json").unlink()
  r=self.run_patch();self.assertNotEqual(r.returncode,0);self.assertIn("B532_MISSING_MODEL",r.stderr)
 def test_missing_java_registration_fails(self):
  self.java.write_text(self.java.read_text().replace("builder.add(FORMED,ACTIVE);","builder.add(FORMED);"))
  r=self.run_patch();self.assertNotEqual(r.returncode,0);self.assertIn("B532_JAVA_ANCHOR",r.stderr)
if __name__=="__main__":unittest.main()
