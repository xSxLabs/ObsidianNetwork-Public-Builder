#!/usr/bin/env python3
"""B1234 global non-OP spam/tick audit on actual reconstructed Java.

No gameplay changes: list mod-originated client command emission and warn
about command packets inside tick/scroll/key paths; fail only if the
Backpack's already-fixed high-frequency command loop regresses.
Never suppress vanilla server spam protection or forge non-OP permissions.
"""
import os
import re
from pathlib import Path

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
assert root.is_dir(),("B1234_MOD_AUDIT_MISSING_SOURCE_ROOT",root)
tracked=0
warnings=[]
for f in sorted(root.rglob("*.java")):
 src=f.read_text("utf-8")
 for match in re.finditer(r"\.sendCommand\s*\(",src):
  # Only our own mod Java sources; do not scan player chat/other mods.
  tracked+=1
  lineno=src.count("\n",0,match.start())+1
  start=max(0,src.rfind("\n",0,match.start()-1000))
  frame=src[start:match.end()]
  if any(word in frame for word in (
      "ClientTickEvent", "mouseScrolled(", "mouseDragged(",
      "for(", "while(", "for (", "while (")):
   warnings.append((str(f.relative_to(root)),lineno))
  print("B1234_MOD_COMMAND_CALLSITE",f.relative_to(root),lineno)
print("B1234_MOD_COMMAND_CALLSITES",tracked,"POTENTIAL_HOTPATHS",len(warnings))
for path,line in warnings[:40]:
 print("B1234_MOD_COMMAND_REVIEW",path,line)
screen=root/"client/V176BackpackScreen.java"
bag=root/"backpack/NetworkBackpackBlockEntity.java"
mag=root/"backpack/V176BackpackMagnetEvents.java"
assert screen.exists() and bag.exists() and mag.exists()
s=screen.read_text("utf-8")
b=bag.read_text("utf-8")
m=mag.read_text("utf-8")
assert "xsxLastScrollPacketTick" in s and "wheelCooldown=5" not in s
assert "xsxPendingScroll" in s and "xsxDraggingScrollbar" in s
assert 'command(scrollY>0?"networkbackpack previous":"networkbackpack next")' not in s
assert "xsxCableCacheContainer==container" in b
assert "xsxCableCommitRevision++;" in b
assert "V176BackpackEquipped.activeMagnet(player)" in m
assert m.index("location.persist(player,updated);")<m.index("remainder.shrink(")
print("B1234_GLOBAL_COMMAND_AUDIT_BACKPACK_ANTISPAM_AND_TICK_GATES_PASS")
