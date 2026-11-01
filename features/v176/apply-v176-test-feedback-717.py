#!/usr/bin/env python3
"""B717: FakePlayer-safe feedback for real-server Micro-MG GameTests.

A real player always has a network connection; a FakePlayer intentionally
does not. Never weaken weapon authentication or FE checks.
Runs after v176 B699; no changes to animations, rendering or actionbar text.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def edit(rel, old, new):
 p=J/rel
 s=p.read_text(encoding="utf-8")
 assert "if(p.connection!=null)" not in s,("V176_B717_ALREADY_APPLIED",rel)
 assert s.count(old)==1,("V176_B717_SOURCE_DRIFT",rel,s.count(old))
 p.write_text(s.replace(old,new,1),encoding="utf-8")

edit("powerarmor/V176AttackModeServer.java",
 '''  p.connection.send(new ClientboundSetActionBarTextPacket(
    Component.literal(V176MicroMgRules.actionbar(active))));''',
 '''  if(p.connection!=null)
   p.connection.send(new ClientboundSetActionBarTextPacket(
    Component.literal(V176MicroMgRules.actionbar(active))));''')
edit("powerarmor/V176CompanionMode.java",
 '''  p.connection.send(new ClientboundSetActionBarTextPacket(Component.literal(message)));''',
 '''  if(p.connection!=null)
   p.connection.send(new ClientboundSetActionBarTextPacket(Component.literal(message)));''')
print("V176_B717_FAKEPLAYER_SAFE_ACTIONBAR_GAME_TEST_PASS")
