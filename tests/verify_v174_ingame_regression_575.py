#!/usr/bin/env python3
"""B575 assets and uncompromised source/cable/solar contract."""
import argparse,io,json
from pathlib import Path
from zipfile import ZipFile
from PIL import Image
p=argparse.ArgumentParser()
p.add_argument("--source",type=Path)
p.add_argument("--assets",type=Path)
p.add_argument("--jar",type=Path)
a=p.parse_args()
assert (a.jar is not None) != (a.source is not None and a.assets is not None)
def verify(read):
 for n,pix in (("reactor_glass_formed",(43,104,148,81)),
               ("reactor_glass_formed_lit",(49,160,232,103))):
  im=Image.open(io.BytesIO(read("textures/block/"+n+".png"))).convert("RGBA")
  assert im.size==(32,32) and set(im.getdata())=={pix},n
  model=json.loads(read("models/block/"+n+".json"))
  assert model["ambientocclusion"] is False
  assert model["parent"] in ("minecraft:block/cube","minecraft:block/cube_all")
 # B584: exact visual parity uses the real blue-black cable texture,
 # not a cosmetic cyan tile; red collar shape stays a separate strict gate.
 assert read("textures/block/xsx_energy_input_collar.png")==read("textures/block/energy_cable.png")
 im=Image.open(io.BytesIO(read("textures/block/xsx_energy_input_collar.png"))).convert("RGBA")
 assert im.size==(16,16)
 assert len(read("textures/block/powerbank_casing_formed_design4_top_lit.png"))>140
if a.jar:
 with ZipFile(a.jar) as z:verify(lambda n:z.read("assets/obsidiannetwork/"+n))
else:
 verify(lambda n:(a.assets/n).read_bytes())
 hud=(a.source/"client/V174MachineScreen.java").read_text()
 cable=(a.source/"blockentity/EnergyCableBlockEntity.java").read_text()
 renderer=(a.source/"client/EnergyCableInputRenderer.java").read_text()
 solar=(a.source/"blockentity/SolarGeneratorBlockEntity.java").read_text()
 skin=(a.source/"multiblock/MultiblockSkinBlock.java").read_text()
 assert "long b568Maximum=600L*Math.max(0,ctrl.guiRodAssemblies()); // B577_REACTOR_MAX_GUI_X5 B575_REACTOR_MAX_SYNCED_RODS" in hud
 assert "guiFormed()?120L*ctrl.guiRodAssemblies()" not in hud
 assert "B575_SLIM_BLUE_INPUT_SOCKET" in renderer
 assert "B584_ITEM_CABLE_IDENTICAL_INPUT" in renderer
 assert renderer.count("cap(state,pose,collector,")==6
 assert "Blocks.BLACK_CONCRETE" not in renderer
 assert "B575_LOCK_FREE_CUT_MASK_READ" in cable
 assert "synchronizedMap(new java.util.IdentityHashMap" not in cable
 assert "new java.util.concurrent.ConcurrentHashMap<>()" in cable
 assert "B568_SOLAR_AUTO_IMPORT_NEIGHBOR" in solar
 assert "long budget = be.energy.stored();" in solar
 assert "B566_CONNECTED_FORMED_GLASS_FACE_CULL" in skin
 assert "TransactionContext transaction" in cable and "target.insert(" in cable and "source.extract(" in cable
print("B575_RENDER_ENERGY_AND_PERFORMANCE_REGRESSION_PASS")
