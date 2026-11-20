#!/usr/bin/env python3
"""B1711: make the 4M item Storage Cell a genuine endgame crafting tier.

Only the existing 4M Cell crafting recipe changes. The output, registration,
saved cells, 1M recipe, all other recipes, item data and runtime are untouched.
"""
import argparse
import json
import re
from pathlib import Path

PATTERN=["NCN","CSC","NCN"]
NETHERITE="minecraft:netherite_block"
STAR="minecraft:nether_star"
TIER4=("4m","4096k")
TIER1=("1m","1024k")

def tier_in(name, aliases):
    return any(re.search(r"(?<![a-z0-9])"+re.escape(token)+r"(?![a-z0-9])",
                         name.lower()) for token in aliases)

def output_id(doc):
    value=doc.get("result")
    if isinstance(value,dict):
        value=value.get("id",value.get("item"))
    return value if isinstance(value,str) else None

def is_storage_cell(name, aliases):
    if not name or not name.startswith("obsidiannetwork:"):
        return False
    ident=name.partition(":")[2].lower()
    return ("cell" in ident and "energy" not in ident
            and "fluid" not in ident and tier_in(ident,aliases))

def load_recipes(resources):
    base=Path(resources)/"data/obsidiannetwork"
    paths=sorted(set(base.glob("recipe/**/*.json"))|
                 set(base.glob("recipes/**/*.json")))
    if not paths:
        raise ValueError("B1711_NO_OBSIDIAN_RECIPES")
    return {path:json.loads(path.read_text(encoding="utf-8")) for path in paths}

def select_cell(recipes, aliases, target=False):
    choices=[(p,d) for p,d in recipes.items()
             if is_storage_cell(output_id(d),aliases)]
    if target:
        preferred=[v for v in choices if "storage" in output_id(v[1]).lower()]
        if preferred:
            choices=preferred
    if len(choices)!=1:
        raise ValueError("B1711_CELL_TIER_AMBIGUOUS_OR_MISSING "
                         +str(aliases)+" found="+str(
                             [(str(p),output_id(d)) for p,d in choices]))
    return choices[0]

def corresponding_1m(recipes, four_m_id):
    candidates=[(p,d) for p,d in recipes.items()
                if is_storage_cell(output_id(d),TIER1)]
    # Require the same cell family. Prefer exact tier-name replacement
    # rather than accidentally selecting an unrelated Cell.
    name=four_m_id.lower()
    expected=set()
    for source,target in (("4m","1m"),("4096k","1024k")):
        expected.add(re.sub(r"(?<![a-z0-9])"+source+r"(?![a-z0-9])",
                            target,name))
    exact=[entry for entry in candidates if output_id(entry[1]).lower() in expected]
    if len(exact)==1:
        return output_id(exact[0][1])
    if len(exact)>1 or len(candidates)!=1:
        raise ValueError("B1711_1M_FAMILY_AMBIGUOUS "
                         +str([(str(p),output_id(d)) for p,d in candidates]))
    return output_id(candidates[0][1])

def apply(resources):
    recipes=load_recipes(resources)
    path,original=select_cell(recipes,TIER4,target=True)
    cell4=output_id(original)
    cell1=corresponding_1m(recipes,cell4)
    if original.get("type") not in ("minecraft:crafting_shaped",
                                   "minecraft:crafting_shapeless"):
        raise ValueError("B1711_UNSUPPORTED_4M_CRAFTING_TYPE: "+
                         str(original.get("type")))
    result=original.get("result")
    count=result.get("count",1) if isinstance(result,dict) else 1
    if count!=1:
        raise ValueError("B1711_EXPECTED_SINGLE_4M_RESULT")
    updated=dict(original)
    updated["type"]="minecraft:crafting_shaped"
    updated.pop("ingredients",None)
    updated["pattern"]=PATTERN[:]
    updated["key"]={"N":NETHERITE,"C":cell1,"S":STAR}
    assert output_id(updated)==cell4
    assert updated["result"]==original["result"]
    assert sum(row.count("C") for row in PATTERN)==4
    assert sum(row.count("N") for row in PATTERN)==4
    assert sum(row.count("S") for row in PATTERN)==1
    if updated!=original:
        path.write_text(json.dumps(updated,ensure_ascii=False,indent=2,
                                   sort_keys=True)+"\n",encoding="utf-8")
    verify=json.loads(path.read_text(encoding="utf-8"))
    if verify!=updated:
        raise AssertionError("B1711_4M_RECIPE_WRITE_MISMATCH")
    print("B1711_4M_STORAGE_CELL_ENDGAME_RECIPE_PASS",
          "target="+cell4,"requires=4x"+cell1+
          "+4x"+NETHERITE+"+1x"+STAR,
          "file="+str(path))
    return path

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("resources",type=Path)
    apply(parser.parse_args().resources)
