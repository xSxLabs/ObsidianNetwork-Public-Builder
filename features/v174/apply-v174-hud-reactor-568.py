#!/usr/bin/env python3
"""B568 GUI alignment and multiblock-size-dependent reactor MAX FE/t."""
import os
from pathlib import Path
root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
p=root/"client/PowerArmorBuild98Client.java"
s=p.read_text(encoding="utf-8")
assert "B552_HALF_SIZE_FE_TEXT" in s and "B552_HALF_SIZE_PASTE_TEXT" in s
assert "B568_UNIFIED_HUD_LABELS" not in s
assert s.count('g.pose().scale(.5f,.5f);')==3
s=s.replace('g.pose().scale(.5f,.5f);','g.pose().scale(.6f,.6f);')
# Same anchor and separation for both rows; labels sit immediately above
# their own bars (bar geometry itself unchanged).
for old,new in [('translate(x+2f,y-1f)','translate(x+2f,y+4f)'),
 ('translate(x+width-percentWidth*.5f-1f,y-1f)',
  'translate(x+width-percentWidth*.6f-1f,y+4f)'),
 ('translate((float)px,(float)py)','translate((float)px,(float)(py+4))')]:
 assert s.count(old)==1,(old,s.count(old))
 s=s.replace(old,new,1)
# Paste number is right aligned exactly as ARMOR FE percentage.
assert s.count('String pasteLabel="PASTE "+pastePct+"%";')==1
s=s.replace('String pasteLabel="PASTE "+pastePct+"%";',
 '''// B568_UNIFIED_HUD_LABELS: matching left label/right percent.
   String pasteLabel="PASTE";
   String pastePercent=pastePct+"%";''',1)
needle='g.text(mc.font,pasteLabel,0,0,pasteColor);'
assert s.count(needle)==1
s=s.replace(needle,needle+'''
   g.pose().popMatrix();
   g.pose().pushMatrix();
   g.pose().translate(px+pasteWidth-mc.font.width(pastePercent)*.6f-1f,py+4f);
   g.pose().scale(.6f,.6f);
   g.text(mc.font,pastePercent,0,0,pasteColor);''',1)
assert s.count('g.pose().pushMatrix();')==4
assert s.count('g.pose().popMatrix();')==4
p.write_text(s,encoding="utf-8")
# B572: The B514b panel moves ROD INSERT up to y=21 and already draws
# live OUTPUT at y=150. Use a separate MAX line at 161 (inside 168px
# panel), never overlap control buttons or the measured FE output.
# Capacity is computed from synced assembly count rather than fuel status.
be=root/"reactor/ReactorControllerBlockEntity.java"
src=be.read_text(encoding="utf-8")
getter='public int guiRodInsertion(){return controlRodInsertion;}'
assert src.count(getter)==1,("B572_REACTOR_GETTER_DRIFT",src.count(getter))
assert 'public int guiRodAssemblies()' not in src
src=src.replace(getter,getter+'\n public int guiRodAssemblies(){return rodAssemblies;}',1)
assert 'out.putInt("reactorAssemblies",rodAssemblies);' in src
be.write_text(src,encoding="utf-8")
p=root/"client/V174MachineScreen.java"
s=p.read_text(encoding="utf-8")
assert "B568_REACTOR_MAX_DESIGN_FE_PER_TICK" not in s
needle='g.text(font,"ROD INSERT "+ctrl.guiRodInsertion()+"%",185,21,0xffb2d8f1);'
assert s.count(needle)==1,("B572_REACTOR_GUI_SHAPE",s.count(needle))
assert s.count('g.text(font,"OUTPUT "+compact(ctrl.guiActualOutputFePerTick())+" FE/t"')==1
s=s.replace(needle,needle+'''
    // B568_REACTOR_MAX_DESIGN_FE_PER_TICK: max generation per tick
    // of the actual formed rod assembly count, even with controls inserted.
    long b568Maximum=ctrl.guiFormed()?120L*ctrl.guiRodAssemblies():0L;
    String b568MaximumLabel="MAX "+b568Maximum+" FE/t";
    g.pose().pushMatrix();
    g.pose().translate(185f,161f);
    g.pose().scale(.65f,.65f);
    g.text(font,b568MaximumLabel,0,0,0xff83e4ef);
    g.pose().popMatrix();''',1)
p.write_text(s,encoding="utf-8")
print("B568_HUD_MATCHED_PERCENT_REACTOR_DYNAMIC_MAX_FE_PASS")
