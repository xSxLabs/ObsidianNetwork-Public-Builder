#!/usr/bin/env python3
"""B531: add all formed/LIT model variants after B530's glass lighting."""
import json
import os
from pathlib import Path

ASSETS=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
SKINS=("reactor_casing","reactor_glass","powerbank_casing","powerbank_glass")

def patch():
    for name in SKINS:
        path=ASSETS/"blockstates"/(name+".json")
        data=json.loads(path.read_text(encoding="utf-8"))
        originals={
            "formed=false":{"model":"obsidiannetwork:block/"+name},
            "formed=true":{"model":"obsidiannetwork:block/"+name+"_formed"},
        }
        assert data.get("variants")==originals,("B531_UNEXPECTED_PRE_LIGHT_SKIN",name,data.get("variants"))
        for formed in (False,True):
            model=name+("_formed" if formed else "")
            assert (ASSETS/"models/block"/(model+".json")).is_file(),("B531_MISSING_SKIN_MODEL",model)
        data["variants"]={
            "formed="+str(formed).lower()+",lit="+str(lit).lower():dict(originals["formed="+str(formed).lower()])
            for formed in (False,True) for lit in (False,True)
        }
        path.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
    print("B531_COMPLETE_FORMED_AND_LIT_BLOCKSTATES_PASS")

if __name__=="__main__":
    patch()
