#!/usr/bin/env python3
"""Authoritative Reactor/Powerbank ON/OFF + live 20-tick FE input/output.

Apply after ALL existing reactor and powerbank code corrections, immediately
before the full v1.7.6 Java compile. This is a source integration patch,
not a replacement of the existing multiblock or existing energy ports.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def change(rel, old, new, expected=1):
 p=J/rel
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==expected,("V176_POWER_CONTROL_SOURCE_DRIFT",rel,s.count(old),expected,old[:140])
 p.write_text(s.replace(old,new,expected),encoding="utf-8")

r="reactor/ReactorControllerBlockEntity.java"
change(r,
''' private boolean formed=false;
 private String status="UNFORMED";''',
''' private boolean formed=false;
 private boolean xsxNetworkEnabled=true;
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
change(r,
'''   @Override protected void onRootCommit(Long before){if(before!=storedFe)setChanged();}''',
'''   @Override protected void onRootCommit(Long before){
    if(before!=storedFe){
     if(level!=null&&before>storedFe)
      xsxRates.committed(level.getGameTime(),0L,before-storedFe);
     setChanged();
    }
   }''')
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
change(p,
'''    @Override protected void onRootCommit(Long before){if(amount!=before)setChanged();}''',
'''    @Override protected void onRootCommit(Long before){
     if(amount!=before){
      if(level!=null)xsxRates.committed(level.getGameTime(),
        Math.max(0L,amount-before),Math.max(0L,before-amount));
      setChanged();
     }
    }''')
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
