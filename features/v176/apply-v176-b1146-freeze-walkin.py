#!/usr/bin/env python3
"""B1146: preserve 1.7.5 transfer, repair unreachable physical walk-in trigger."""
import os,re
from pathlib import Path
root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
p=root/"powerarmor/PowerArmorEntrySequence655.java"
def patch(s):
    pattern=r'private\s+static\s+boolean\s+inside\s*\(\s*ServerPlayer\s+p\s*,\s*ArmorStand\s+stand\s*\)\s*\{[^}]*\}'
    matches=list(re.finditer(pattern,s))
    assert len(matches)==1,("B1146_INSIDE_SIGNATURE",len(matches))
    old=matches[0].group()
    assert ".22D" in old and ".65D" in old, "B1146_UNEXPECTED_FREEZE_GEOMETRY"
    new="""private static boolean inside(ServerPlayer p,ArmorStand stand){
   double dx=p.getX()-stand.getX(), dz=p.getZ()-stand.getZ();
   double dy=p.getY()-stand.getY();
   // A real player's collision box cannot reach the old 0.469 block center.
   return dx*dx+dz*dz<=.81D && dy>=-.40D && dy<=1.30D;
  }"""
    s=s[:matches[0].start()]+new+s[matches[0].end():]
    # Do not hide the item-owning world stand while the player approaches.
    old="""  stand.addTag(OPEN_TAG);
  stand.addTag(HIDE_TAG);
  stand.setInvisible(true);
  stand.noPhysics=true;  // vanilla ArmorStand passes through player while open"""
    assert s.count(old)==1,"B1146_FREEZE_OPEN_STATE_DRIFT"
    s=s.replace(old,"""  stand.addTag(OPEN_TAG);
  stand.removeTag(HIDE_TAG);
  stand.setInvisible(false);
  stand.noPhysics=true;  // pass-through original suit while awaiting entry""",1)
    # Make the cosmetic visual non-colliding on both logical sides.
    old="""  view.addTag("xsxlabs_b655_entry_hold_visual");
  view.begin(true);view.beginPhase(8);"""
    assert s.count(old)==1,"B1146_FREEZE_VISUAL_DRIFT"
    s=s.replace(old,"""  view.addTag("xsxlabs_b655_entry_hold_visual");
  view.noPhysics=true;
  view.begin(true);view.beginPhase(8);""",1)
    assert "PowerArmorSuitWorld.tryEnter(p,stand.getId());" in s
    return s
p.write_text(patch(p.read_text()),encoding="utf-8")
visual=root/"powerarmor/PowerArmorVisualEntity.java"
s=visual.read_text()
pattern=r'(public\s+PowerArmorVisualEntity\s*\([^{}]*\)\s*\{\s*super\([^;{}]*\);)'
m=list(re.finditer(pattern,s))
assert len(m)==1,("B1146_VISUAL_CONSTRUCTOR_DRIFT",len(m))
s=s[:m[0].end()]+"\n  this.noPhysics=true;"+s[m[0].end():]
visual.write_text(s)
print("B1146_FREEZE_TRANSFER_PRESERVED_REAL_PLAYER_WALKIN_RADIUS_AND_NO_COLLISION_PASS")
