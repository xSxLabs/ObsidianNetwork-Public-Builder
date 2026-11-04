#!/usr/bin/env python3
"""Resolve ONLY crafting collisions caused by replacing tinted glass with glass.

Run after replace-tinted-glass-crafting-recipes.py. The existing B659
collision auditor is authoritative. If two distinct recipes now overlap,
use an exact stained-glass ingredient in ONE ObsidianNetwork recipe; never
reintroduce tinted glass, never mutate outputs, and never alter foreign mods.
"""
import argparse
import copy
import json
import subprocess
import sys
from pathlib import Path

COLORS=("blue","light_blue","gray","white","black","red","green","yellow",
        "purple","cyan","orange","magenta","lime","pink","light_gray","brown")
GLASS="minecraft:glass"

def collisions(root,auditor):
    proc=subprocess.run([sys.executable,str(auditor),str(root)],
                        capture_output=True,text=True,check=False)
    if proc.returncode==0:
        return []
    output=proc.stdout+"\n"+proc.stderr
    result=[]
    for line in output.splitlines():
        if line.startswith("COLLISION "):
            values=line.split(maxsplit=2)
            if len(values)!=3:
                raise RuntimeError("Malformed B659 collision report: "+line)
            left=(root/values[1]).resolve()
            right=(root/values[2]).resolve()
            result.append((left,right))
    if not result:
        raise RuntimeError("B659 audit error (not a recipe collision): "+output[-3000:])
    return result

def options(doc):
    """Coordinates for a real ingredient only, never an output or pattern."""
    found=[]
    def visit(node,path):
        if isinstance(node,str):
            if node==GLASS:found.append(path)
        elif isinstance(node,list):
            for idx,value in enumerate(node):visit(value,path+(idx,))
        elif isinstance(node,dict):
            for key,value in node.items():
                if key not in ("result","output"):
                    visit(value,path+(key,))
    for rootkey in ("key","ingredients"):
        if rootkey in doc:visit(doc[rootkey],(rootkey,))
    return found

def recolor(doc,path,color):
    newer=copy.deepcopy(doc)
    where=newer
    for node in path[:-1]:where=where[node]
    assert where[path[-1]]==GLASS,("GLASS_SELECTION_DRIFT",path)
    where[path[-1]]="minecraft:"+color+"_stained_glass"
    assert doc.get("result")==newer.get("result")
    assert doc.get("output")==newer.get("output")
    return newer

def allowed(path,root):
    try:
        parts=path.relative_to(root).parts
    except ValueError:
        return False
    return (len(parts)>=4 and parts[:2]==("data","obsidiannetwork")
            and parts[2] in ("recipe","recipes") and path.suffix==".json")

def resolve(root,auditor,apply=False):
    root=Path(root).resolve()
    auditor=Path(auditor).resolve()
    current=collisions(root,auditor)
    if not current:
        print("NORMAL_AND_STAINED_GLASS_NO_COLLISIONS");return 0
    if not apply:
        raise AssertionError(f"Crafting conflicts remaining: {len(current)}")
    altered=0
    for attempt in range(len(current)+512):
        if not current:break
        before=len(current)
        improved=False
        # Only a recipe involved in a reported collision may be modified.
        for left,right in current:
            for file in (right,left):
                if not allowed(file,root):continue
                original=file.read_bytes()
                doc=json.loads(original)
                if doc.get("type") not in ("minecraft:crafting_shaped",
                                            "minecraft:crafting_shapeless"):
                    continue
                for position in options(doc):
                    for color in COLORS:
                        candidate=recolor(doc,position,color)
                        file.write_text(json.dumps(candidate,indent=2,ensure_ascii=False)+"\n",
                                        encoding="utf-8")
                        try:
                            after=collisions(root,auditor)
                        except BaseException:
                            file.write_bytes(original)
                            raise
                        if len(after)<before:
                            altered+=1
                            current=after
                            improved=True
                            print("RECIPE_GLASS_CONFLICT_RESOLVED",file.relative_to(root),
                                  "color="+color,"remaining="+str(len(current)))
                            break
                        file.write_bytes(original)
                    if improved:break
                if improved:break
            if improved:break
        if not improved:
            raise RuntimeError("Unable to resolve existing recipe collisions using "
                               "ONLY normal/stained glass without changing outputs. "
                               "Remaining pairs: "+repr(current[:8]))
    else:
        raise RuntimeError("Glass conflict resolver exceeded iteration budget")
    assert not current
    print("NORMAL_AND_STAINED_GLASS_COLLISIONS_RESOLVED count="+str(altered))
    return altered

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("resources",type=Path)
    parser.add_argument("--auditor",type=Path,default=Path(__file__).resolve().parents[2]/
                        "v175/apply-v175-recipe-collisions-659.py")
    parser.add_argument("--apply",action="store_true")
    args=parser.parse_args()
    resolve(args.resources,args.auditor,apply=args.apply)
