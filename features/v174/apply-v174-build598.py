#!/usr/bin/env python3
"""B598: authoritative cable capability modes, live Nutrinator paste GUI, clear glass.
Apply after B597; preserve other FE, reactor, multiblock and tooltip behavior.
"""
import os,re
from pathlib import Path
from PIL import Image
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])
A=R/"assets/obsidiannetwork"
T=Path(__file__).resolve().parents[2]/"tests"
def read(p): return p.read_text(encoding="utf-8")
def write(p,s): p.write_text(s,encoding="utf-8")
def one(s,old,new,tag):
 n=s.count(old)
 assert n==1,("B598_ANCHOR",tag,n,old[:110])
 return s.replace(old,new,1)
# Cable: the B591 BFS only checked intermediate edges. Actual consumer/producer
# capability access begins inside CableEnergyHandler, where B597 never checked
# exposedSide on insert/extract. OFF was visibly cut but still accepted FE.
p=J/"blockentity/EnergyCableBlockEntity.java";s=read(p)
assert "B591_ENERGY_DIRECTED_WALK" in s
class_match=re.search(r"\bclass\s+CableEnergyHandler\b[^{]*\{",s)
assert class_match, "B598_CABLE_REAL_HANDLER_NOT_FOUND"
start=class_match.end()
depth=1;end=None
for i in range(start,len(s)):
 if s[i]=="{":depth+=1
 elif s[i]=="}":
  depth-=1
  if depth==0:
   end=i;break
assert end is not None
body=s[start:end]
for meth,allowed in (("insert","true"),("extract","false"),("getAmountAsLong","false")):
 m=re.search(r"\bpublic\s+(?:int|long)\s+"+meth+r"\s*\([^)]*\)\s*\{",body)
 assert m,("B598_CAPABILITY_METHOD_NOT_FOUND",meth)
 inject="\n    // B598_REAL_SIDE_GATE: no capability bypass of INPUT/OUTPUT/OFF.\n    if(!EnergyCableBlockEntity.this.b598BoundaryAllows(this.exposedSide,"+allowed+"))return 0;\n"
 # Each method gets its own guard. extract() and getAmountAsLong()
 # intentionally use the same OUTPUT-side rule.
 assert "B598_REAL_SIDE_GATE" not in body[m.end():m.end()+80],("B598_DOUBLE_METHOD_GATE",meth)
 body=body[:m.end()]+inject+body[m.end():]
s=s[:start]+body+s[end:]
anchor=" // B591_ENERGY_DIRECTED_WALK:"
assert s.count(anchor)==1
s=s.replace(anchor,''' // B598_REAL_SIDE_GATE: authoritative live direction check on FE capabilities.
 // INPUT: insert only, OUTPUT: extract only, BOTH: both, OFF: neither.
 // No cached mode, no graph traversal, no allocation on the hot path.
 private boolean b598BoundaryAllows(Direction face,boolean inserting){
  if(face==null)return true; // Internal unsided access; never exposed as a face.
  int mode=energySideMode(face);
  return mode==3 || mode==(inserting?1:2);
 }
'''+anchor,1)
write(p,s)
# Nutrinator: sync the *new* values, not the previous values every 40 ticks.
# Production itself is still 1x / 20 ticks. Only delta values trigger a packet,
# also covering asynchronous fluid extraction through transaction commits.
p=J/"nutrition/NutrinatorBlockEntity.java";s=read(p)
old='  if(!(level instanceof ServerLevel world)||world.getGameTime()%20L!=0L)return;'
new='''  if(!(level instanceof ServerLevel world))return;
  if(world.getGameTime()%20L!=0L){
   if(world.getGameTime()%5L==0L)be.b598SyncPaste(world,pos,state);
   return;
  }'''
s=one(s,old,new,"nutrinator_tick_cadence")
old='''  // B461_NUTRINATOR_PACED_GUI: at most one synced BE update / 2 seconds.
  if(world.getGameTime()%40L==0L)
   world.sendBlockUpdated(pos,state,state,3);'''
assert s.count(old)==1,("B598_NUTRI_OLD_SYNC",s.count(old))
s=s.replace(old,"  // B598_LIVE_NUTRINATOR_GUI: updates after actual change, never stale data.",1)
# The end of the 20-tick worker is the correct point for GUI sync.
old='  if(dirty)be.setChanged();'
s=one(s,old,'''  if(dirty)be.setChanged();
  be.b598SyncPaste(world,pos,state);''',"nutrinator_production_completion")
marker=' public static void tick(Level level,BlockPos pos,BlockState state,NutrinatorBlockEntity be){'
assert s.count(marker)==1
s=s.replace(marker,''' // B598_LIVE_PASTE_VALUE: no repeated NBT/packet when tank is unchanged.
 private long b598ClientSyncedPaste=Long.MIN_VALUE;
 private void b598SyncPaste(ServerLevel world,BlockPos pos,BlockState state){
  if(b598ClientSyncedPaste==paste)return;
  b598ClientSyncedPaste=paste;
  world.sendBlockUpdated(pos,state,state,3);
 }
'''+marker,1)
write(p,s)
# Glass: neutral white/clear glass, no turquoise or blue color overlay.
# Keep already-proven model structure, render layer and connected blockstates.
formed=("reactor_glass_formed","reactor_glass_formed_lit",
 "powerbank_glass_formed","powerbank_glass_formed_lit_detail0",
 "powerbank_glass_formed_lit_detail1","powerbank_glass_formed_lit_detail2")
for name in formed:
 p=A/"textures/block"/(name+".png")
 with Image.open(p) as source:
  im=source.convert("RGBA")
  assert im.size==(32,32),("B598_GLASS_SIZE",name,im.size)
  assert len(set(im.getdata()))==1,("B598_GLASS_UNIFORM",name)
  im.putdata([(250,250,250,20)]*(32*32))
  im.save(p,optimize=True)
# Loose (unassembled) glass has a thin neutral frame rather than any blue tint.
for kind in ("reactor","powerbank"):
 for face in ("front","side","top"):
  p=A/"textures/block"/(kind+"_glass_"+face+".png")
  with Image.open(p) as source:
   im=source.convert("RGBA")
   assert im.size==(16,16),("B598_LOOSE_GLASS_SIZE",p)
   src=list(im.getdata())
   assert all(0<=a<=255 for r,g,b,a in src)
   # Preserve subtle frame geometry but make the whole pane neutral and clear.
   im.putdata([(250,250,250,12 if a<35 else 25) for r,g,b,a in src])
   im.save(p,optimize=True)
# The earlier strict gates had old tinted RGBA expectations; update EXACT
# expected colors (do not disable the validation).
p=T/"verify_v174_build591_contract.py";s=read(p)
for name,old in (("reactor_glass_formed","(43,104,148,56)"),
                 ("reactor_glass_formed_lit","(49,160,232,74)"),
                 ("powerbank_glass_formed","(34,100,139,28)"),
                 ("powerbank_glass_formed_lit_detail0","(29,220,243,40)"),
                 ("powerbank_glass_formed_lit_detail1","(29,220,243,40)"),
                 ("powerbank_glass_formed_lit_detail2","(29,220,243,40)")):
 assert old in s,("B598_GLASS_GATE_DRIFT",name,old)
# 6 slots expected; matching tint can appear 3x.
s=s.replace("(43,104,148,56)","(250,250,250,20)")
s=s.replace("(49,160,232,74)","(250,250,250,20)")
s=s.replace("(34,100,139,28)","(250,250,250,20)")
assert s.count("(29,220,243,40)")==3
s=s.replace("(29,220,243,40)","(250,250,250,20)")
write(p,s)
p=T/"verify_v174_ingame_regression_575.py";s=read(p)
s=one(s,'("reactor_glass_formed",(43,104,148,56))',
        '("reactor_glass_formed",(250,250,250,20))',"B575_glass")
s=one(s,'("reactor_glass_formed_lit",(49,160,232,74))',
        '("reactor_glass_formed_lit",(250,250,250,20))',"B575_glass_lit")
write(p,s)
# B558 reference gate checks alpha >=20 and tinted turquoise; the new neutral
# glass must stay transparent while meeting its contrast and lighting rules.
assert all((Image.open(A/"textures/block"/(n+".png")).convert("RGBA").getpixel((12,12))
            ==(250,250,250,20)) for n in formed)
assert "b598BoundaryAllows(this.exposedSide,true)" in read(J/"blockentity/EnergyCableBlockEntity.java")
assert "b598BoundaryAllows(this.exposedSide,false)" in read(J/"blockentity/EnergyCableBlockEntity.java")
assert "B598_LIVE_PASTE_VALUE" in read(J/"nutrition/NutrinatorBlockEntity.java")
print("B598_REAL_CABLE_INPUT_OUTPUT_OFF_LIVE_NUTRINATOR_NEUTRAL_CLEAR_GLASS_PASS")
