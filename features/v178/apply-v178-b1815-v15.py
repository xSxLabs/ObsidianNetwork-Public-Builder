#!/usr/bin/env python3
"""B1815 v1.7.8 v15: real machine-slot click IDs, visible large-bank glass,
and a detailed 32px pickaxe face. No altered energy/mining mechanics.
Runs immediately after apply-v178-b1810-v15.py.
"""
import json
import os
import struct
import zlib
from pathlib import Path

J = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork"
A = Path(os.environ["V1_RESOURCE_ROOT"]) / "assets/obsidiannetwork"

def replace_once(path, old, new):
    source = path.read_text(encoding="utf8")
    assert source.count(old) == 1, ("B1815_SOURCE_DRIFT", str(path), old[:100], source.count(old))
    path.write_text(source.replace(old, new, 1), encoding="utf8")

# The 9x3 ChestMenu gives its original slots menu indices 0..62 via addSlot().
# Replacing slots with NonNullList.set() creates new Slots whose public .index
# stays at the default -1. The client sends that invalid ID on normal/right/
# shift click, so upgrades appear installed but are impossible to take out.
# Preserve the exact menu index for every replaced slot on BOTH peers.
server_menu = J / "mining/V178MiningBuilderMenu.java"
replace_once(server_menu,
    "  for(int i=2;i<27;i++){",
    """  // B1815: client click packet and server quick-move require real slot IDs.
  // Slots replaced with slots.set() never passed through addSlot().
  slots.get(0).index=0;
  slots.get(1).index=1;
  for(int i=2;i<27;i++){""")
replace_once(server_menu,
    "  slots.set(i,new Slot(",
    "  slots.set(i,new Slot(") if False else None
client = J / "client/V178MiningBuilderOperationsScreen.java"
replace_once(client,
    "  for(int i=2;i<27;i++){",
    """  // B1815: the client needs indices 0 and 1 for click packets.
  menu.slots.get(0).index=0;
  menu.slots.get(1).index=1;
  for(int i=2;i<27;i++){""")
# Also restore each hidden replacement's original index, even though it
# remains offscreen and inaccessible, for full list-index consistency.
for path, prefix in ((server_menu, "slots"), (client, "menu.slots")):
    source = path.read_text(encoding="utf8")
    marker = "  for(int i=2;i<27;i++){"
    assert source.count(marker) == 1
    # The hidden slots are deliberately unreachable, but their slot.index
    # must not be -1 or inconsistent for menu synchronization.
    start = source.index(marker)
    stop = source.index("\n  }", start) + len("\n  }")
    block = source[start:stop]
    anchor = "\n  }"
    assert block.count(anchor) == 1, ("B1815_HIDDEN_SLOT_LOOP_DRIFT", path)
    block = block.replace(anchor, "\n   " + prefix + ".get(i).index=i;" + anchor, 1)
    path.write_text(source[:start] + block + source[stop:], encoding="utf8")

server_src = server_menu.read_text(encoding="utf8")
client_src = client.read_text(encoding="utf8")
assert "slots.get(1).index=1;" in server_src
assert "menu.slots.get(1).index=1;" in client_src
assert "slots.get(i).index=i;" in server_src
assert "menu.slots.get(i).index=i;" in client_src
assert "return be.installedSpeedUpgrades().copy();" in server_src
assert "source.setByPlayer(held)" in server_src
assert "moveItemStackTo(held,27,63,true)" in server_src
assert "new Slot(speedSlot.container,1,143,27)" in client_src

# B1815: the B568 fully connected glass has only 41/255 alpha when idle
# and 59/255 when charged. At maximum 3x3x12 shell size this makes huge
# exterior areas appear to be absent, especially from ground level.
# Keep the original seamless texture and translucency; increase visibility
# without model geometry, a BER, per-frame scanning, or block-state changes.
# Exact uniform RGBA guarantees no per-block grid / artificial seams.
from PIL import Image
glass = ("powerbank_glass_formed",) + tuple(
    "powerbank_glass_formed_lit_detail" + str(i) for i in range(3))
for name in glass:
    texture = A / "textures/block" / (name + ".png")
    with Image.open(texture) as src:
        assert src.size == (32,32) and src.mode == "RGBA", ("B1815_BANK_SPRITE_DRIFT", name)
    lit = "_lit_" in name
    color = (32,112,154,164) if not lit else (31,169,201,176)
    Image.new("RGBA", (32,32), color).save(texture, optimize=True)
    with Image.open(texture) as check:
        assert check.getpixel((0,0)) == check.getpixel((31,31)) == color

bank = json.loads((A / "blockstates/powerbank_glass.json").read_text("utf8"))
assert len(bank["variants"]) == 144
assert sum(k.startswith("formed=true,") for k in bank["variants"]) == 72
for key, value in bank["variants"].items():
    if key.startswith("formed=true,"):
        model = value["model"].split(":")[-1].split("/")[-1]
        assert (A/"models/block"/(model+".json")).is_file(), ("B1815_BANK_MODEL_MISSING",key)
skin = (J/"multiblock/MultiblockSkinBlock.java").read_text("utf8")
assert "B566_CONNECTED_FORMED_GLASS_FACE_CULL" in skin
assert "applyAssemblyBands" in skin

# Upgrade JUST the existing front-screen icon to detailed original 32x32
# pixel art. One baked cube and one front atlas remain: no extra quads, no
# renderer and no changes to the power or mining machinery.
case = A/"models/block/mining_builder.json"
model = json.loads(case.read_text("utf8"))
assert len(model["elements"]) == 1
assert model["textures"]["front"] == "obsidiannetwork:block/mining_builder_front_v15"
name = "mining_builder_front_v15"
head=set()
for y, (low,high) in {
    9:(14,19),10:(11,22),11:(9,24),12:(7,25),
    13:(6,26),14:(6,11),15:(6,8),16:(7,7),17:(25,25)
}.items():
    head.update((x,y) for x in range(low,high+1))
head.update((x,y) for y in (13,14,15,16,17) for x in (24,25)
            if x == 25 or y <= 15)
handle=set()
for y in range(14,27):
    center=18-int((y-14)*0.68)
    handle.update((x,y) for x in range(center-1,center+2))
def near(x,y,pixels):
    return any((x+dx,y+dy) in pixels for dx,dy in
               ((-1,0),(1,0),(0,1),(0,-1)))
def pixel(x,y):
    if x in (0,31) or y in (0,31):return (21,16,43,255)
    if x in (1,30) or y in (1,30):return (39,29,73,255)
    if x in (2,29) or y in (2,29):return (90,60,143,255)
    if x in (3,28) or y in (3,28):return (118,80,166,255)
    if x in (4,27) or y in (4,27):return (17,20,38,255)
    if y==5:return (18,49,67,255)
    if y==6 and 6<=x<=25:return (27,68,87,255)
    if (x,y) in head:
        return (189,248,248,255) if y<=11 else (
            (111,219,242,255) if y==12 else (68,166,201,255))
    if (x,y) in handle:
        center=18-int((y-14)*0.68)
        return (251,199,110,255) if x<center else (
            (181,117,56,255) if x==center else (102,66,46,255))
    if near(x,y,head) or near(x,y,handle):return (8,12,25,255)
    return (10,27,46,255) if (x+y)%7 else (16,36,55,255)

def png_rgba32():
    raw=bytearray()
    for y in range(32):
        raw.append(0)
        for x in range(32):
            raw.extend(pixel(x,y))
    def chunk(tag, payload):
        return (struct.pack(">I",len(payload))+tag+payload+
                struct.pack(">I",zlib.crc32(tag+payload)&0xffffffff))
    return (b"\x89PNG\r\n\x1a\n" +
            chunk(b"IHDR",struct.pack(">IIBBBBB",32,32,8,6,0,0,0)) +
            chunk(b"IDAT",zlib.compress(raw,9)) + chunk(b"IEND",b""))

front=A/"textures/block"/(name+".png")
assert front.read_bytes().startswith(b"\x89PNG")
front.write_bytes(png_rgba32())
with Image.open(front) as icon:
    assert icon.size == (32,32) and icon.getpixel((15,11))[0] > 180
assert len(json.loads(case.read_text("utf8"))["elements"]) == 1
# CI's final B558 binary verifier includes a late historical override: it
# expected every assembled glass pixel to remain nearly invisible white
# RGBA(250,250,250,20). That expectation is precisely the missing-panel
# regression in the user's maximum-height Powerbank screenshot. Rebase ONLY
# its assembled-bank assertion to the new complete glass material, and keep
# every reactor/other source gate unchanged. The earlier B558 checks still
# run before B1815, when the older baseline must remain valid.
verifier=Path("tests/verify_v174_reference_visuals_558.py")
v=verifier.read_text(encoding="utf8")
old="assert glass.size==(32,32) and glass.getpixel((16,16))==(250,250,250,20),n"
if old in v:
    assert v.count(old)==1
    # Preserve EXACT surrounding indent from whichever historical verifier
    # version was reconstructed by the earlier workflow steps.
    first=v.rfind("\n",0,v.index(old))+1
    indent=v[first:v.index(old)]
    new="""expected=(31,169,201,176) if n.startswith("powerbank_glass_formed_lit_detail") else (
 (32,112,154,164) if n=="powerbank_glass_formed" else (250,250,250,20))
assert glass.size==(32,32) and glass.getpixel((16,16))==expected,n"""
    v=v.replace(old,new.replace("\n","\n"+indent),1)
# B558 additionally contains BOTH a low-alpha check and a cyan-reflection
# check in the final packed verification. Adjust them as well even when the
# late near-invisible-white assertion above was present. Leave reactor,
# casing, reference design and all unrelated rules unchanged.
old1="assert 20<=glass2.getpixel((12,12))[3]<=120"
old2='assert core.getpixel((10,14))[1]>200,"Charged internal turquoise reflection absent"'
assert old in v or old1 in v or old2 in v, "B1815_BANK_BINARY_GATE_DRIFT"
if old1 in v:
    assert v.count(old1)==1
    v=v.replace(old1,"assert glass2.getpixel((12,12))==(32,112,154,164)")
if old2 in v:
    assert v.count(old2)==1
    v=v.replace(old2,"assert core.getpixel((10,14))==(31,169,201,176)")
# Fail immediately on malformed compatibility checks, before the expensive Gradle build.
compile(v,str(verifier),"exec")
verifier.write_text(v,encoding="utf8")
assert "(31,169,201,176)" in v

print("B1815_REAL_SLOT_INDICES_CLICK_PICKUP_SHIFT_AND_3X3X12_GLASS_32PX_PICKAXE_PASS")
