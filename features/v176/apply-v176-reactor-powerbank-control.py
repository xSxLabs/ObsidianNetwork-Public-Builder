#!/usr/bin/env python3
"""Authoritative Reactor/Powerbank ON/OFF + live 20-tick FE input/output.

Apply after ALL existing reactor and powerbank code corrections, immediately
before the full v1.7.6 Java compile. This is a source integration patch,
not a replacement of the existing multiblock or existing energy ports.
"""
import os
import re
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def change(rel, old, new, expected=1):
 p=J/rel
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==expected,("V176_POWER_CONTROL_SOURCE_DRIFT",rel,s.count(old),expected,old[:140])
 p.write_text(s.replace(old,new,expected),encoding="utf-8")


def inject_commit(rel, journal_name, quantity, code):
 """Patch a reconstructed energy SnapshotJournal without changing its original
 commit/rollback body; new v1.7.4 patches can legally grow the callback."""
 file=J/rel
 source=file.read_text(encoding="utf-8")
 journal=source.find(journal_name)
 assert journal>=0,("V176_JOURNAL_NOT_FOUND",rel,journal_name)
 m=re.search(r"(?:@Override\s+)?protected\s+void\s+onRootCommit\s*\(\s*Long\s+(\w+)\s*\)\s*\{",
             source[journal:journal+2500])
 assert m is not None,("V176_ENERGY_COMMIT_NOT_FOUND",rel,journal_name)
 start=journal+m.end()
 depth=1
 end=start
 while end<len(source) and depth:
  if source[end]=="{":depth+=1
  elif source[end]=="}":depth-=1
  end+=1
 assert depth==0 and quantity in source[start:end],(
     "V176_ENERGY_COMMIT_SOURCE_CHANGED",rel,quantity)
 name=m.group(1)
 replacement=code.replace("before",name)
 assert "xsxRates.committed" not in source[start:end],("V176_DUPLICATE_ENERGY_METER",rel)
 source=source[:start]+"\n    "+replacement+"\n"+source[start:]
 file.write_text(source,encoding="utf-8")

r="reactor/ReactorControllerBlockEntity.java"
change(r,
''' private String status="UNFORMED";''',
''' private boolean xsxNetworkEnabled=true;
 private final dev.obsidiannetwork.power.V176PowerRateMeter xsxRates=
     new dev.obsidiannetwork.power.V176PowerRateMeter();
 public boolean xsxNetworkEnabled(){return xsxNetworkEnabled;}
 public boolean xsxNetworkFormed(){return formed;}
 public long xsxNetworkStoredFe(){return storedFe;}
 public long xsxNetworkCapacityFe(){return FE_CAPACITY;}
 public long xsxNetworkInputFePerTick(){return 0L;}
 public long xsxNetworkOutputFePerTick(){
  return xsxNetworkEnabled&&level!=null?xsxRates.outputPerTick(level.getGameTime()):0L;
 }
 public void xsxNetworkSetEnabled(boolean on){
  if(xsxNetworkEnabled!=on){
   xsxNetworkEnabled=on;
   if(!on)status="NETWORK OFF";
   setChanged();
  }
 }
 private String status="UNFORMED";''')
# Existing v1.7.4 patches may expand the energy journal callback. Inject
# telemetry without replacing or dropping any previous transaction semantics.
inject_commit(r,"energyJournal","storedFe",
 """if(level!=null&&before>storedFe)
      xsxRates.committed(level.getGameTime(),0L,before-storedFe);""")
change(r,
'''    if(demand<=0||!formed)return 0;''',
'''    if(demand<=0||!formed||!xsxNetworkEnabled)return 0;''')
change(r,
'''  if(!be.formed)return;
  if(be.waterMb<=WATER_CAPACITY-1000''',
'''  if(!be.formed)return;
  if(!be.xsxNetworkEnabled){be.status="NETWORK OFF";return;}
  if(be.waterMb<=WATER_CAPACITY-1000''')
change(r,
'''  out.putBoolean("reactorFormed",formed);''',
'''  out.putBoolean("reactorFormed",formed);
  out.putBoolean("xsxNetworkEnabled",xsxNetworkEnabled);''')
change(r,
'''  rodAssemblies=Math.max(0,in.getIntOr("reactorAssemblies",0));''',
'''  rodAssemblies=Math.max(0,in.getIntOr("reactorAssemblies",0));
  xsxNetworkEnabled=in.getBooleanOr("xsxNetworkEnabled",true);''')

p="powerbank/PowerbankBlockEntity.java"
change(p,
''' private boolean formed=false;
 public PowerbankBlockEntity(BlockPos p,BlockState s)''',
''' private boolean formed=false;
 private boolean xsxNetworkEnabled=true;
 private final dev.obsidiannetwork.power.V176PowerRateMeter xsxRates=
     new dev.obsidiannetwork.power.V176PowerRateMeter();
 public boolean xsxNetworkEnabled(){return mode()==PowerbankBlock.Mode.CONTROLLER&&xsxNetworkEnabled;}
 public boolean xsxNetworkFormed(){return formed;}
 public long xsxNetworkStoredFe(){return amount;}
 public long xsxNetworkCapacityFe(){return capacity;}
 public long xsxNetworkInputFePerTick(){
  return xsxNetworkEnabled&&level!=null?xsxRates.inputPerTick(level.getGameTime()):0L;
 }
 public long xsxNetworkOutputFePerTick(){
  return xsxNetworkEnabled&&level!=null?xsxRates.outputPerTick(level.getGameTime()):0L;
 }
 public void xsxNetworkSetEnabled(boolean on){
  if(mode()!=PowerbankBlock.Mode.CONTROLLER)return;
  if(xsxNetworkEnabled!=on){xsxNetworkEnabled=on;setChanged();}
 }
 public PowerbankBlockEntity(BlockPos p,BlockState s)''')
# Same callback-preserving approach for current powerbank journaling.
inject_commit(p,"journal","amount",
 """if(level!=null)xsxRates.committed(level.getGameTime(),
      Math.max(0L,amount-before),Math.max(0L,before-amount));""")
change(p,
'''     if(b==null||!b.formed)return 0;''',
'''     if(b==null||!b.formed||!b.xsxNetworkEnabled)return 0;''',2)
change(p,
'''   out.putLong("bankAmount",amount);out.putLong("bankCapacity",capacity);''',
'''   out.putLong("bankAmount",amount);out.putLong("bankCapacity",capacity);
   out.putBoolean("xsxNetworkEnabled",xsxNetworkEnabled);''')
change(p,
'''  capacity=Math.max(0L,Math.min(PowerbankGeometry.MAX_FE,in.getLongOr("bankCapacity",0L)));''',
'''  capacity=Math.max(0L,Math.min(PowerbankGeometry.MAX_FE,in.getLongOr("bankCapacity",0L)));
  xsxNetworkEnabled=in.getBooleanOr("xsxNetworkEnabled",true);''')

print("V176_REACTOR_POWERBANK_REAL_ON_OFF_IO_TELEMETRY_INSTALLED")
