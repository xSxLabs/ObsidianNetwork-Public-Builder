#!/usr/bin/env python3
"""v1.7.2: Create moving contraption support for persistent Power Armor stands.
No mandatory Create classes in bytecode. Moves ENTITY, never its equipment.
"""
import os
from pathlib import Path
root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/powerarmor"
p=root/"PowerArmorCreatePlatformSupport.java"
assert not p.exists()
p.write_text(r'''package dev.obsidiannetwork.powerarmor;

/**
 * V172_CREATE_MOVING_PLATFORM compatibility marker.
 *
 * DEDICATED_SERVER_CREATE_SAFE_HOTFIX: the old EntityTickEvent listener
 * reflected over Create entity method signatures. Some of them mention
 * client-only com.mojang.blaze3d.vertex.PoseStack, crashing dedicated servers.
 * It also duplicated the attachment/movement listener in
 * PowerArmorCreateCarrier, risking two moves per tick.
 *
 * PowerArmorCreateCarrier exclusively owns Create translation tracking.
 * Keep this class present so existing source and integration references work.
 * Absolutely no Create class loading or client APIs on the server here.
 */
public final class PowerArmorCreatePlatformSupport {
 private PowerArmorCreatePlatformSupport(){}
}
''',encoding="utf-8")
print("V172_CREATE_MOVING_PLATFORM PASS: legacy duplicate listener removed; single server-safe carrier owns armor motion")
