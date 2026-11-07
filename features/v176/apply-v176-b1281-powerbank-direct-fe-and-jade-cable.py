#!/usr/bin/env python3
"""B1281: remove the REAL 1m FE/t autonomous Powerbank output cap.

Build 1229 removed the Powerbank energy CAPABILITY per-call MAX_IO cap,
but the B591 server-ticker push still offered only 1,000,000 FE to each
adjacent machine/cable every tick. Each NeoForge EnergyHandler call accepts
a signed int; now offer up to Integer.MAX_VALUE, bounded by actual stored FE,
and perform EXACTLY ONE receiver-first, source-second journalled transaction
per output face per tick. No artificial pauses, no item or FE storage in cable.

The EnergyCableBlockEntity uses a pass-through EnergyHandler. Its
getAmountAsLong() reports accessible energy of external endpoints (for machine
routing), so Jade mistakes accessible energy for energy stored in the cable.
DO NOT return zero from that handler: doing so can break compatibility with
machines relying on the energy visibility. Instead, install an optional Jade
client plugin hiding only the misleading universal energy-storage row for
EnergyCableBlock, reporting 'No internal FE buffer' without changing
capabilities, node traversal, configured side modes or transfer quantities.

All strict guards finish before any Java source is written.
"""
# B1288 explicit release candidate: remove Powerbank active 1m output limit,
# preserve direct cable transport and correct Jade's misleading storage meter.
import os,re
from pathlib import Path
root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
bank=root/"powerbank/PowerbankBlockEntity.java"
cable=root/"blockentity/EnergyCableBlockEntity.java"
jade=root/"compat/EnergyCableJadePlugin.java"
bank_src=bank.read_text("utf-8")
cable_src=cable.read_text("utf-8")
assert not jade.exists(),("B1281_JADE_ALREADY_INSTALLED",str(jade))
marker="B591_POWERBANK_OUTPUT_PUSH"
assert bank_src.count(marker)==1,("B1281_AUTONOMOUS_EXPORT_MISSING",bank_src.count(marker))
start=bank_src.index(" private void b591PushOutput(ServerLevel server){")
depth=1
begin=bank_src.index("{",start)+1
end=begin
while depth and end<len(bank_src):
 if bank_src[end]=="{":depth+=1
 if bank_src[end]=="}":depth-=1
 end+=1
assert depth==0,("B1281_PUSH_BRACE_DRIFT",depth)
method=bank_src[start:end]
old="int offer=(int)Math.min(1_000_000L,amount);"
assert method.count(old)==1,("B1281_POWERBANK_1M_PUSH_DRIFT",method.count(old))
assert method.count("target.insert(offer,tx)")==1, "B1281_SINK_TRANSACTION_DRIFT"
assert method.count("source.extract(accepted,tx)==accepted")==1, "B1281_SOURCE_TRANSACTION_DRIFT"
assert method.count("tx.commit();")==1,"B1281_COMMIT_DRIFT"
assert "try(var tx=net.neoforged.neoforge.transfer.transaction.Transaction.openRoot())" in method
assert "activePorts" in method and "POWERBANK_OUTPUT" in method
method=method.replace(old,
'''// B1281_UNCAPPED_POWERBANK_AUTO_EXPORT: NO artificial 1m FE/t throttle.
    // Native EnergyHandler uses int per transfer. One full-int request per
    // face per tick avoids an unbounded BFS/transaction loop that harms MSPT.
    int offer=(int)Math.min((long)Integer.MAX_VALUE,amount);''')
bank_src=bank_src[:start]+method+bank_src[end:]
assert "B1281_UNCAPPED_POWERBANK_AUTO_EXPORT" in bank_src
assert "1_000_000L,amount" not in method
assert "SnapshotJournal<long[]>" in bank_src
assert "xsxCommittedTransfer(" in bank_src

# Prove the pass-through cable does not have its own persistent FE balance.
# Neither capacity nor getAmountAsLong() may be changed by this patch.
for required in ("class CableEnergyHandler implements EnergyHandler",
                 "getAmountAsLong()","getCapacityAsLong()",
                 "public int extract(","public int insert("):
 assert required in cable_src,("B1281_DIRECT_CABLE_API_DRIFT",required)
assert "B591_ENERGY_DIRECTED_WALK" in cable_src
assert "XSXLABS_CROSSMOD_ENERGY_REENTRY_GUARD_V1" in cable_src

plugin=r'''package dev.obsidiannetwork.compat;

import dev.obsidiannetwork.block.EnergyCableBlock;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import snownee.jade.api.BlockAccessor;
import snownee.jade.api.IComponentProvider;
import snownee.jade.api.ITooltip;
import snownee.jade.api.IWailaClientRegistration;
import snownee.jade.api.IWailaPlugin;
import snownee.jade.api.JadeIds;
import snownee.jade.api.TooltipPosition;
import snownee.jade.api.WailaPlugin;
import snownee.jade.api.config.IPluginConfig;

/** B1281: cable transports FE, it does NOT own an FE buffer.
 * Jade's built-in universal energy row inspects the cable proxy and shows
 * neighboring machine storage as though it belonged to the cable.
 * Hide that row ONLY for our dedicated EnergyCableBlock, never for devices,
 * Energy Cells, reactor ports, or the Powerbank controller/ports.
 * Jade is optional/compileOnly; this class is not a mod event subscriber.
 */
@WailaPlugin
public final class EnergyCableJadePlugin implements IWailaPlugin {
 @Override public void registerClient(IWailaClientRegistration registration){
  registration.registerBlockComponent(NoCableEnergyBuffer.INSTANCE,EnergyCableBlock.class);
 }
 private enum NoCableEnergyBuffer implements IComponentProvider<BlockAccessor> {
  INSTANCE;
  private static final Identifier UID=Identifier.fromNamespaceAndPath(
      "obsidiannetwork","energy_cable_no_buffer");
  @Override public Identifier getUid(){return UID;}
  // Jade's built-in universal EnergyStorageProvider is BODY+1000. Run AFTER
  // its tooltip contribution and suppress only its misleading storage bar.
  @Override public int getDefaultPriority(){return TooltipPosition.BODY+2000;}
  @Override public void appendTooltip(ITooltip tooltip,BlockAccessor accessor,
                                      IPluginConfig config){
   tooltip.remove(JadeIds.UNIVERSAL_ENERGY_STORAGE);
   tooltip.add(Component.literal("Energy cable: no internal FE storage"));
  }
 }
}
'''
assert "registerBlockComponent(NoCableEnergyBuffer.INSTANCE,EnergyCableBlock.class)" in plugin
assert "tooltip.remove(JadeIds.UNIVERSAL_ENERGY_STORAGE)" in plugin
assert "getDefaultPriority(){return TooltipPosition.BODY+2000;}" in plugin
assert "@WailaPlugin" in plugin
assert "new EnergyHandler()" not in plugin
# Both output and Jade compile-optional source changes are atomic.
jade.parent.mkdir(parents=True,exist_ok=True)
bank.write_text(bank_src,"utf-8")
jade.write_text(plugin,encoding="utf-8")
print("B1281_POWERBANK_1M_AUTO_PUSH_REMOVED_FE_CONSERVATION_JADE_CABLE_PROXY_NO_BUFFER_PASS")
