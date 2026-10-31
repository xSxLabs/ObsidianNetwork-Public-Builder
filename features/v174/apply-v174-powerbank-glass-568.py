#!/usr/bin/env python3
"""B568: make formed bank glazing visually continuous; do not touch casings.

The old assembled lit sprites still had a repeated vertical turquoise line.
Adjacent faces are already culled in B566; replace only those six GLASS
textures with uniformly tinted transparent material, no per-block stripe.
"""
import os
from pathlib import Path
from PIL import Image
root=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork/textures/block"
names=["powerbank_glass_formed"]+[f"powerbank_glass_formed_lit_detail{x}" for x in range(3)]
for name in names:
 p=root/(name+".png")
 with Image.open(p) as im: assert im.size==(32,32) and im.mode=="RGBA",name
 lit="_lit_" in name
 # Same color at every pixel, including edges: no inner 3x3 grid or panel
 # stripe. Dark glass with preserved cyan light when bank is charged.
 rgba=(29,220,243,59) if lit else (34,100,139,41)
 Image.new("RGBA",(32,32),rgba).save(p,optimize=True)
print("B568_POWERBANK_CONNECTED_GLASS_UNIFORM_TINT_PASS")
