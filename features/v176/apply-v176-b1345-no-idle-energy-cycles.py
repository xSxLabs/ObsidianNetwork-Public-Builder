#!/usr/bin/env python3
"""B1345: stop FE storage ping-pong and recover Powerbank input links on reload.

Regression from user server (B1343): Energy Cell reports simultaneous 5M
in/out with full machines; Powerbank input stays idle even though Energy Cell
on the same cable can fill. Source/target can be the same energy reservoir
through opposite cable-facing port capabilities, or can be two bidirectional
Energy Cells endlessly pumping into each other; Powerbank output can recycle
its stored FE back into an upstream OUTPUT-configured Energy Cell INPUT.

Fix:
  1. Every Energy Cell serverTick auto-export has a scoped origin marker.
     A cell cannot accept its own push through a different face; other
     OUTPUT-configured cells are sources, not auto-push storage sinks.
     Input-only storage cells can still be charged by legitimate output.
  2. During Powerbank auto-export, an Energy Cell with any OUTPUT mode
     cannot be treated as a load. Real consuming machines and input-only
     receiving cells still accept their actual demand.
  3. Incoming Energy Cell INPUT capabilities do not advertise exportable FE,
     and Powerbank INPUT ports do not report their entire controller reserve
     as extractable endpoint FE.
  4. On chunk load/restart the Powerbank controller automatically revalidates
     the formed shell and restores INPUT/OUTPUT port links if missing.
     Retry limited to once per 80 ticks on unformed banks; no per-tick BFS.
All modifications are guarded and source-drift-safe.
"""
import os,re
from pathlib import Path
root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
bank=root/"powerbank/PowerbankBlockEntity.java"
cell=root/"blockentity/EnergyCellBlockEntity.java"
b=bank.read_text("utf-8")
e=cell.read_text("utf-8")

def one(src,old,new,label):
 n=src.count(old)
 assert n==1,("B1345_ANCHOR",label,n,old[:120])
 return src.replace(old,new,1)

def method_span(src,pattern,label):
 matches=list(re.finditer(pattern,src,re.S))
 assert len(matches)==1,("B1345_METHOD",label,len(matches))
 mt=matches[0]
 start=src.find("{",mt.start(),mt.end()+3)
 assert start>=0,("B1345_NO_BODY",label)
 nesting=0
 for k in range(start,len(src)):
  if src[k]=="{":nesting+=1
  if src[k]=="}":
   nesting-=1
   if nesting==0:return start,k
 raise AssertionError(("B1345_BRACES",label))

for m in ("B1320_POWERBANK_DEMAND_INPUT","b1320PullInput(sl);",
          "b1300ActiveExport.set(this);","b1300SelfCharge(tx,b)",
          "SnapshotJournal<long[]>","activePorts"):
 assert m in b,("B1345_BANK_DRIFT",m)
for m in ("class EnergyCellBlockEntity","class Handler implements EnergyHandler",
          "SideMode.INPUT","SideMode.OUTPUT","serverTick(",
          "journal.updateSnapshots(tx)"):
 assert m in e,("B1345_CELL_DRIFT",m)

# Revalidate only on unloaded / broken links. The initial construction and
# genuine normal tick path remain untouched. Crucial: loadAdditional() resets
# formed=false and activePorts is empty, but the existing controller tick had
# no repair.
guard="  if(!(world instanceof ServerLevel sl)||be.mode()!=PowerbankBlock.Mode.CONTROLLER)return;"
b=one(b,guard,guard+"""
  // B1345_RECOVER_PORT_LINKS: loadAdditional resets formed/activePorts.
  // Without this pass, the Powerbank input stays UNLINKED until manually
  // placing/breaking a block. Initial retry is immediate; invalid structures
  // are throttled for at least 80 server ticks to protect MSPT.
  if((!be.formed||be.activePorts.isEmpty())
      && sl.getGameTime()>=be.b1345NextLinkCheck){
   be.b1345NextLinkCheck=sl.getGameTime()+80L;
   be.revalidate(sl);
  }""","controller_load_autorepair")
anchor=" // B1320_INPUT_PULL_CONTEXT:"
b=one(b,anchor,
""" private long b1345NextLinkCheck=Long.MIN_VALUE;
 // B1345_TRUE_OUTPUT_CONTEXT: other BEs can refuse to act as a source
 // when the same FE reservoir is connected both upstream and downstream.
 public static boolean b1345AutoExporting(){
  return b1300ActiveExport.get()!=null;
 }
"""+anchor,"bank_export_context")
# A Powerbank INPUT port has no extractable FE. Returning controller.amount
# from INPUT caused cable "source" scans to see 2 billion duplicate FE.
start=b.index("private final net.neoforged.neoforge.transfer.energy.EnergyHandler energyPort")
end=b.index("public net.neoforged.neoforge.transfer.energy.EnergyHandler energyPort()",start)
segment=b[start:end]
pattern=r"(public long getAmountAsLong\(\)\s*\{\s*)"
n=len(re.findall(pattern,segment))
assert n==1,("B1345_GET_AMOUNT",n)
segment=re.sub(pattern,r"\1if(mode()!=PowerbankBlock.Mode.OUTPUT)return 0L;\n    ",segment,count=1)
b=b[:start]+segment+b[end:]

# Prevent same-cell pass-through and multi-cell storage ping-pong while a
# source cell is auto-exporting. On INPUT-only destination cells, storage
# transfers are still legal; all true consuming machines are untouched.
decl=r"public final class EnergyCellBlockEntity extends BlockEntity {"
e=one(e,decl,decl+"""
 // B1345_STORAGE_CYCLE_GUARD: only scoped to source's active serverTick push.
 private static final ThreadLocal<EnergyCellBlockEntity> b1345ActiveAutoPush=
     new ThreadLocal<>();
 private boolean b1345CanAutoReceiveStorage(){
  for(net.minecraft.core.Direction direction:net.minecraft.core.Direction.values()){
   if(sideMode(direction)==SideMode.OUTPUT)return false;
  }
  return true;
 }
""","cell_origin_context")
# Wrap the entire method body to protect all output paths including cable
# endpoints; try/finally resets context even on an early return/exception.
a,z=method_span(e,r"public\s+static\s+void\s+serverTick\s*\(\s*(?:[\w.]+\.)?Level\s+\w+\s*,\s*(?:[\w.]+\.)?BlockPos\s+\w+\s*,\s*(?:[\w.]+\.)?BlockState\s+\w+\s*,\s*(?:[\w.]+\.)?EnergyCellBlockEntity\s+(\w+)\s*\)\s*\{","cell_server_tick")
match=re.search(r"public\s+static\s+void\s+serverTick\s*\([^)]*EnergyCellBlockEntity\s+(\w+)\s*\)",e[:a])
assert match,("B1345_NO_TICK_VAR",e[a-120:a])
be=match.group(1)
original=e[a+1:z]
guarded=r"""
  // B1345: Never auto-push stored FE back into this or another
  // output-configured Energy Cell through a cable loop.
  EnergyCellBlockEntity previous=b1345ActiveAutoPush.get();
  b1345ActiveAutoPush.set("""+be+r""");
  try{
"""+original+r"""
  }finally{
   if(previous==null)b1345ActiveAutoPush.remove();
   else b1345ActiveAutoPush.set(previous);
  }
 """
e=e[:a+1]+guarded+e[z:]

start=e.index("class Handler implements EnergyHandler")
a,z=method_span(e[start:],r"public\s+int\s+insert\s*\(\s*int\s+\w+\s*,\s*(?:[\w.]+\.)?TransactionContext\s+\w+\s*\)\s*\{","cell_port_insert")
a+=start;z+=start
inject="""
   // B1345_CYCLE_SINK: if a storage BE is auto-pushing into a network,
   // only input-only cells can be its destination. Prevents both self-
   // roundtrips (same BE, different side handlers) and two-cell ping-pong.
   var activeCell=b1345ActiveAutoPush.get();
   if(activeCell!=null
       && (activeCell==EnergyCellBlockEntity.this
           || !b1345CanAutoReceiveStorage()))return 0;
   // Powerbank auto-export is for actual demand. A cell configured with
   // any OUTPUT face is a supply/relay, never a storage sink in that cycle.
   if(dev.obsidiannetwork.powerbank.PowerbankBlockEntity.b1345AutoExporting()
       && !b1345CanAutoReceiveStorage())return 0;
"""
e=e[:a+1]+inject+e[a+1:]
# Accurate FE availability: INPUT faces are not energy sources. Do not
# change actual insert/extract semantics or reported storage in GUI.
start=e.index("class Handler implements EnergyHandler")
a,z=method_span(e[start:],r"public\s+long\s+getAmountAsLong\s*\(\s*\)\s*\{","cell_port_source_visibility")
a+=start;z+=start
e=e[:a+1]+"\n   if(!canExtract())return 0L;"+e[a+1:]

# Fail closed: no silent transformations to energy quantities or rates.
assert "b1345ActiveAutoPush.set("+be+")" in e
assert e.count("b1345ActiveAutoPush.remove()")==1
assert e.count("!b1345CanAutoReceiveStorage()")==2
assert e.count("if(!canExtract())return 0L;")==1
assert "b1345NextLinkCheck=sl.getGameTime()+80L;" in b
assert "if(mode()!=PowerbankBlock.Mode.OUTPUT)return 0L;" in b
assert "b1320PullInput(sl);" in b and "b591PushOutput(sl);" in b
assert "b1300SelfCharge(tx,b)" in b
# Write only after all source-specific guards succeeded.
bank.write_text(b,encoding="utf-8")
cell.write_text(e,encoding="utf-8")
print("B1345_CELL_STORAGE_NO_CYCLE_POWERBANK_RELINK_DIRECT_FE_CONSERVATION_PASS")
