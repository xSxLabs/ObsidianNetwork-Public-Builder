#!/usr/bin/env python3
"""Build345: visible server TextDisplay holograms even inside opaque blocks.

Applied after B337/B340 and B338. Changes only render attributes of hologram
TextDisplays; does not touch blockstate, saved format, IO, world topology or FE.
"""
import os
from pathlib import Path

J = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork"
R = Path(os.environ["V1_RESOURCE_ROOT"])
target = J / "blockentity/NetworkDeviceBlockEntity.java"
source = target.read_text(encoding="utf-8")

# Render through solid blocks underneath the holo table; TextDisplay defaults
# may have a zero culling box and hide before a client sees the text.
anchor = "   entity.setBillboardConstraints(net.minecraft.world.entity.Display.BillboardConstraints.CENTER);"
assert source.count(anchor) == 1, ("V173_B345_DISPLAY_DRIFT", source.count(anchor))
new = """   // V173_B345_HOLO_VISIBLE: see-through + nonzero frustum box + view range.
   // TextDisplay FLAG_SEE_THROUGH = 0x02. It is client-rendered, not a wall edit.
   entity.setFlags((byte)2);
   entity.setWidth(Math.max(2F,Math.min(16F,(float)holoWidth)));
   entity.setHeight(Math.max(1F,Math.min(4F,(float)holoWidth/3F)));
   entity.setViewRange(4F);"""
target.write_text(source.replace(anchor, anchor + "\n" + new, 1), encoding="utf-8")

# These mutators are private in MC 26.1.2. Use the existing NeoForge AT path.
at = R / "META-INF/accesstransformer.cfg"
assert at.exists(), "V173_B345_ACCESS_TRANSFORMER_MISSING"
existing = at.read_text(encoding="utf-8")
entries = [
    "public net.minecraft.world.entity.Display$TextDisplay setFlags(B)V",
    "public net.minecraft.world.entity.Display setWidth(F)V",
    "public net.minecraft.world.entity.Display setHeight(F)V",
    "public net.minecraft.world.entity.Display setViewRange(F)V",
]
assert "public net.minecraft.world.entity.Display$TextDisplay setText(" in existing
assert "public net.minecraft.world.entity.Display setTransformation(" in existing
if existing and not existing.endswith("\n"):
    existing += "\n"
at.write_text(existing + "".join(e + "\n" for e in entries if e not in existing), encoding="utf-8")

assert "V173_B345_HOLO_VISIBLE" in target.read_text(encoding="utf-8")
print("V173_B345_HOLO_TEXT_CULLING_SEETHROUGH_PASS")
