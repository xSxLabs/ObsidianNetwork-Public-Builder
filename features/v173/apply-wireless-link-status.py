#!/usr/bin/env python3
"""v1.7.3: report a wireless receiver CONNECTED only if its actual paired
transmitter has a live, powered NETWORK runtime.

A local controller near an RX must never produce a false-positive status.
Matching transmitter owner+channel and its true source runtime are authoritative.
A ThreadLocal resolution guard preserves the no-recursion storage contract.
"""
import os
from pathlib import Path

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
relay=root/"blockentity/NetworkSignalRelayBlockEntity.java"
bridge=root/"network/NetworkSignalRelayBridge.java"
s=relay.read_text(encoding="utf-8")
b=bridge.read_text(encoding="utf-8")

old="""   var rt=dev.obsidiannetwork.network.WorldTopologyBridge.runtimeForAccessory(world,next);
   if(rt!=null&&rt.powered())return transmitter()?"SOURCE ONLINE":"CONNECTED";
  }
  if(!cable)return "NO NETWORK CABLE";
  return transmitter()?"SOURCE CONTROLLER OFFLINE":"NO LIVE TRANSMITTER / SOURCE OFFLINE";"""
new="""   if(transmitter()){
    var rt=dev.obsidiannetwork.network.WorldTopologyBridge.runtimeForAccessory(world,next);
    if(rt!=null&&rt.powered())return "SOURCE ONLINE";
   }
  }
  if(!cable)return "NO NETWORK CABLE";
  // V173_REAL_WIRELESS_LINK_STATUS: a local controller at the RX does NOT
  // prove that its paired TX is loaded, matched or connected to a source.
  if(!transmitter())return dev.obsidiannetwork.network.NetworkSignalRelayBridge.sourceOnline(world,this)
      ?"CONNECTED":"NO LIVE TRANSMITTER / SOURCE OFFLINE";
  return "SOURCE CONTROLLER OFFLINE";"""
assert s.count(old)==1,("unexpected relay diagnostics API",s.count(old))
s=s.replace(old,new,1)
relay.write_text(s,encoding="utf-8")

needle=" private static NetworkRuntime transmitterRuntime(ServerLevel receiverLevel,NetworkSignalRelayBlockEntity rx){"
method=""" /** V173_REAL_WIRELESS_LINK_STATUS: only the live, owner/channel-matched
  * source NETWORK counts. Never derive RX health from its local controller.
  * Guard source lookups so TX cable checks cannot bridge recursively. */
 public static boolean sourceOnline(ServerLevel receiverLevel,NetworkSignalRelayBlockEntity rx){
  if(rx==null||rx.transmitter()||!rx.paired()||RESOLVING.get())return false;
  RESOLVING.set(true);
  try{
   NetworkRuntime source=transmitterRuntime(receiverLevel,rx);
   return source!=null&&source.powered();
  }finally{RESOLVING.set(false);}
 }
"""
assert b.count(needle)==1,("unexpected bridge source resolver",b.count(needle))
b=b.replace(needle,method+needle,1)
bridge.write_text(b,encoding="utf-8")
assert s.count("V173_REAL_WIRELESS_LINK_STATUS")==1
assert b.count("V173_REAL_WIRELESS_LINK_STATUS")==1
print("V173_REAL_WIRELESS_LINK_STATUS_PASS: RX status needs matching live powered TX, not local network")
