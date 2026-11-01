#!/usr/bin/env python3
"""Build 659 compiled-source and resource gates. Run after all overlays."""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
world=(J/"powerarmor/PowerArmorSuitWorld.java").read_text()
visual=(J/"powerarmor/PowerArmorVisualEntity.java").read_text()
client=(J/"client/PowerArmorExitInputLock654.java").read_text()
guard=(J/"client/PowerArmorExitRender659.java").read_text()
exitlogic=(J/"powerarmor/PowerArmorExitSequence650.java").read_text()
assert world.count("new Animation(stand,entering?40:80,entering,")==3
assert "int t=(animation.entering()?41:81)-animation.ticks();" in world
assert "isExitOpening659" in visual and "isClosingFor659" in visual
assert "tickCount>(entityData.get(V175_PHASE)==9?43:83)" in visual
assert "PowerArmorRuntime.full(p)" in client
assert "registerAvatarEntityModifier" in guard
assert "RenderPlayerEvent.Pre" in guard and "e.setCanceled(true)" in guard
assert "p.setInvisible(true)" in exitlogic and "showAfterExit(p)" in exitlogic
assert "p.tickCount+64" in exitlogic and "PowerArmorSuitWorld.exit(p)" in exitlogic
assert "PowerArmorRecall" not in guard and "PowerArmorRecall" not in client
print("B659_CLIENT_EXIT_CONCEALMENT_40T_ENTRY_SOURCE_GATE PASS")
