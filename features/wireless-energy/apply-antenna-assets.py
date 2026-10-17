#!/usr/bin/env python3
"""Create antenna-based models/textures for Network Transmitter and Receiver.

Uses the already-shipped wireless antenna as the geometric reference.
No new Java behavior is implied by these resource additions.
"""
from pathlib import Path
import os, json, struct, zlib

root=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
source=root/"models/block/wireless_antenna.json"
original=json.loads(source.read_text())
assert len(original.get("elements",[]))==4, "Existing antenna model changed"
assert original["textures"]["base"]=="obsidiannetwork:block/wireless_antenna"
assert (root/"textures/block/wireless_antenna.png").is_file()

def quad(frm,to):
    assert all(0<=a<b<=16 for a,b in zip(frm,to))
    return {"from":frm,"to":to,
            "faces":{d:{"texture":"#signal"} for d in ("up","down","north","south","east","west")}}

def chunk(tag,raw):
    return struct.pack(">I",len(raw))+tag+raw+struct.pack(">I",zlib.crc32(tag+raw)&0xffffffff)

def signal_png(rgb):
    scan=[]
    for y in range(16):
        line=b"\x00"
        for x in range(16):
            dx,dy=abs(x-7.5),abs(y-7.5)
            c=rgb if dx<=5 and dy<=5 else (39,37,43)
            if dx>=4.0 or dy>=4.0:c=tuple(round(v*.6) for v in c)
            line+=bytes((*c,255))
        scan.append(line)
    return (b"\x89PNG\r\n\x1a\n"+
            chunk(b"IHDR",struct.pack(">IIBBBBB",16,16,8,6,0,0,0))+
            chunk(b"IDAT",zlib.compress(b"".join(scan),9))+
            chunk(b"IEND",b""))

configs=(
 ("network_transmitter","Network Transmitter",(240,136,49),[
    quad([5.5,15,6.5],[10.5,16,9.5]),
    quad([3.5,12.5,7.3],[4.5,15.7,8.7]),
    quad([11.5,12.5,7.3],[12.5,15.7,8.7])]),
 ("network_receiver","Network Receiver",(63,186,247),[
    quad([5.5,15,6.5],[10.5,16,9.5]),
    quad([2.7,11,7.3],[3.7,14.7,8.7]),
    quad([12.3,11,7.3],[13.3,14.7,8.7])])
)
rotations={"facing=north":{},"facing=east":{"y":90},"facing=south":{"y":180},"facing=west":{"y":270}}
langpath=root/"lang/en_us.json"
lang=json.loads(langpath.read_text())
for slug,label,color,details in configs:
    model=json.loads(json.dumps(original))
    model["textures"]["signal"]=f"obsidiannetwork:block/{slug}_signal"
    model["elements"].extend(details)
    (root/f"models/block/{slug}.json").write_text(json.dumps(model,indent=2)+"\n")
    states={"variants":{k:dict(v,model=f"obsidiannetwork:block/{slug}") for k,v in rotations.items()}}
    (root/f"blockstates/{slug}.json").write_text(json.dumps(states,indent=2)+"\n")
    (root/f"models/item/{slug}.json").write_text(json.dumps({"parent":f"obsidiannetwork:block/{slug}"},indent=2)+"\n")
    item={"model":{"type":"minecraft:model","model":f"obsidiannetwork:item/{slug}"}}
    (root/f"items/{slug}.json").write_text(json.dumps(item,indent=2)+"\n")
    (root/f"textures/block/{slug}_signal.png").write_bytes(signal_png(color))
    # Every new block is obtainable and drops itself.
    lootdir=root.parent.parent/"data/obsidiannetwork/loot_table/blocks"
    recipedir=root.parent.parent/"data/obsidiannetwork/recipe"
    lootdir.mkdir(parents=True,exist_ok=True)
    recipedir.mkdir(parents=True,exist_ok=True)
    (lootdir/f"{slug}.json").write_text(json.dumps({
        "type":"minecraft:block",
        "pools":[{"rolls":1,"entries":[{"type":"minecraft:item","name":f"obsidiannetwork:{slug}"}],
          "conditions":[{"condition":"minecraft:survives_explosion"}]}]
    },indent=2)+"\n")
    (recipedir/f"{slug}.json").write_text(json.dumps({
        "type":"minecraft:crafting_shaped",
        "pattern":["IRI","RCR","IEI"],
        "key":{"I":"minecraft:iron_ingot","R":"minecraft:redstone",
               "C":"obsidiannetwork:wireless_antenna","E":"obsidiannetwork:energy_cable"},
        "result":{"id":f"obsidiannetwork:{slug}","count":1}
    },indent=2)+"\n")
    lang[f"block.obsidiannetwork.{slug}"]=label
    lang[f"item.obsidiannetwork.{slug}"]=label
langpath.write_text(json.dumps(lang,ensure_ascii=False,indent=2)+"\n")
print("WIRELESS_ANTENNA_MODELS_V1 PASS; two antenna models/blockstates/item models/textures/labels")
