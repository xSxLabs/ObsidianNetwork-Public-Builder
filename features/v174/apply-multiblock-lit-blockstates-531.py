#!/usr/bin/env python3
"""B532: B503 ACTIVE and B530 LIT must be registered and modeled together."""
import json,os
from pathlib import Path
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
JAVA=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/multiblock/MultiblockSkinBlock.java"
SKINS=("reactor_casing","reactor_glass","powerbank_casing","powerbank_glass")
def patch():
 s=JAVA.read_text()
 assert 'BooleanProperty ACTIVE=BooleanProperty.create("active")' in s
 assert 'BooleanProperty LIT=BooleanProperty.create("lit")' in s
 for before,after in (
  ('registerDefaultState(defaultBlockState().setValue(FORMED,false).setValue(ACTIVE,false));',
   'registerDefaultState(defaultBlockState().setValue(FORMED,false).setValue(ACTIVE,false).setValue(LIT,false));'),
  ('builder.add(FORMED,ACTIVE);','builder.add(FORMED,ACTIVE,LIT);')):
  assert s.count(before)==1,("B532_JAVA_ANCHOR",before,s.count(before))
  s=s.replace(before,after,1)
 JAVA.write_text(s)
 for name in SKINS:
  p=A/"blockstates"/(name+".json")
  data=json.loads(p.read_text())
  original={f"formed={str(f).lower()},active={str(a).lower()}":{"model":"obsidiannetwork:block/"+name+("_formed" if f else "")} for f in (False,True) for a in (False,True)}
  assert data.get("variants")==original,("B532_EXPECT_FOUR_OLD_STATES",name,data.get("variants"))
  for f in (False,True):
   model=name+("_formed" if f else "")
   assert (A/"models/block"/(model+".json")).is_file(),("B532_MISSING_MODEL",model)
  data["variants"]={f"formed={str(f).lower()},active={str(a).lower()},lit={str(l).lower()}":dict(original[f"formed={str(f).lower()},active={str(a).lower()}"]) for f in (False,True) for a in (False,True) for l in (False,True)}
  assert len(data["variants"])==8
  p.write_text(json.dumps(data,indent=2)+"\n")
 print("B532_EIGHT_STATES_JAVA_AND_MODEL_REGISTRATION_PASS")
if __name__=="__main__":patch()
