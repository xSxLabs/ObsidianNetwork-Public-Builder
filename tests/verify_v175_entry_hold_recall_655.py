#!/usr/bin/env python3
"""B655 integration gate: all skins, recall mask untouched and real enter state."""
import json,hashlib,os
from pathlib import Path
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
for mk in range(1,25):
 stem=f"power_armor_visual_mk{mk}"
 a=json.loads((A/"geckolib/animations/entity"/(stem+".animation.json")).read_text())["animations"]
 for mode in ("recall_brake","recall_dock"):
  c=a["animation.power_armor."+mode]["bones"]
  for side in ("helmet_left","helmet_right"):
   assert all(x["vector"]==[0,0,0] for x in c[side]["rotation"].values()),(mk,mode,side)
  assert "faceplate" in c and any(abs(x["vector"][0])>=89 for x in c["faceplate"]["rotation"].values()),(mk,mode)
 for mode in ("equip","unequip"):
  c=a["animation.power_armor."+mode]["bones"]
  assert max(abs(x["vector"][1]) for x in c["helmet_left"]["rotation"].values())>100,(mk,mode,"normal helmet rear must still open")
 op=a["animation.power_armor.entry_open"]
 cl=a["animation.power_armor.entry_close"]
 assert op["animation_length"]==3 and cl["animation_length"]==2
 assert op==a["animation.power_armor.exit_open"]
 assert cl==a["animation.power_armor.exit_close"]
 for bone,channels in op["bones"].items():
  for kind,fr in channels.items():
   assert list(fr.values())[-1]["vector"]==next(iter(cl["bones"][bone][kind].values()))["vector"],(mk,bone,kind)
s=(J/"powerarmor/PowerArmorEntrySequence655.java").read_text()
w=(J/"powerarmor/PowerArmorSuitWorld.java").read_text()
ex=(J/"powerarmor/PowerArmorExitSequence650.java").read_text()
v=(J/"powerarmor/PowerArmorVisualEntity.java").read_text()
assert "setMarker(true)" in s and "stand.setMarker(o.marker())" in s
assert "if(!inside(p,stand))return;" in s
assert "PowerArmorSuitWorld.tryEnter(p,stand.getId())" in s
assert "OPEN.put(id,new Open" in s
assert "PowerArmorEntrySequence655.request(stand,player)" in w
assert "PowerArmorEntrySequence655.waiting(e)" in w
assert "visual.beginPhase(9)" in w
assert "visual.setExitOwner654(player.getUUID())" in w
assert "tickCount>83&&!entityTags().contains" in v
assert 'case 8 -> "animation.power_armor.entry_open";' in v
assert 'case 9 -> "animation.power_armor.entry_close";' in v
assert "p.setInvisible(true);" in ex and "showAfterExit(p)" in ex
assert "PowerArmorSuitWorld.exit(p)" in ex
assert "p.tickCount+64" in ex
assert "BEFORE_HIDE_655.remove(id);" in ex
print("B655_24_MK_RECALL_MASK_ONLY_ENTRY_HOLD_UNTIL_WALK_IN_AND_EXIT_VISIBLE_AFTER_OPEN_PASS")
