#!/usr/bin/env python3
"""v1.7.3: Create-style Schematic & Quill -> saved Blueprint -> powered Printer.

Distinct reusable design workflow. The finished blueprint is not the selector.
Network Printer accepts materials only from an attached NETWORK cable (including
a wireless receiver through WorldTopologyBridge) and draws its power only from
a wired FE energy-capability connection or a real charged energy cell.
"""
import json,os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
D=Path(os.environ["V1_RESOURCE_ROOT"])/"data/obsidiannetwork"
def change(rel,old,new):
 p=J/rel;text=p.read_text(encoding="utf-8")
 assert text.count(old)==1,(rel,old[:100],text.count(old))
 p.write_text(text.replace(old,new,1),encoding="utf-8")
def emit(rel,body):
 p=J/rel;p.parent.mkdir(parents=True,exist_ok=True)
 assert not p.exists(),str(p)
 p.write_text(body,encoding="utf-8")
def jsonfile(p,data):
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# The paper Blueprint stores only the saved design. The Quill marks the
# two corners; on the second click it becomes a printable Blueprint.
bp=J/"item/NetworkBlueprintItem.java"
source=bp.read_text(encoding="utf-8")
marker=" @Override public InteractionResult useOn(UseOnContext context){"
before,sep,tail=source.partition(marker)
assert sep and tail.endswith("\n }\n}\n"),"Blueprint UseOn parser drift"
method=marker+tail[:-3]  # leaves full method closing brace, not class ending
# Turn the hand-held quill into one completed design. No item duplication.
old='''  write(stack,"xsxlabs_blocks",String.join(",",out));
  write(stack,"xsxlabs_size",sx+","+sy+","+sz);
  write(stack,"xsxlabs_first","");
  user.displayClientMessage(Component.literal("Blueprint saved: "+sx+"x"+sy+"x"+sz+
       " ("+out.size()+" blocks). Insert into Network Printer."),true);'''
new='''  ItemStack finished=new ItemStack(ObsidianNetwork.NETWORK_BLUEPRINT.get());
  write(finished,"xsxlabs_blocks",String.join(",",out));
  write(finished,"xsxlabs_size",sx+","+sy+","+sz);
  user.setItemInHand(context.getHand(),finished);
  user.displayClientMessage(Component.literal("Blueprint saved: "+sx+"x"+sy+"x"+sz+
       " ("+out.size()+" blocks). Insert into Network Printer."),true);'''
assert method.count(old)==1
method=method.replace(old,new,1)
# Enforce already-loaded source chunks; no remote chunk loads during scan.
line='''   BlockPos where=new BlockPos(loX+x,loY+y,loZ+z);
   var state=level.getBlockState(where);'''
assert method.count(line)==1
method=method.replace(line,'''   BlockPos where=new BlockPos(loX+x,loY+y,loZ+z);
   if(!level.hasChunkAt(where)){
    user.displayClientMessage(Component.literal("Blueprint: all selected chunks must be loaded."),true);
    return InteractionResult.FAIL;
   }
   var state=level.getBlockState(where);''',1)
bp.write_text(before+"}\n",encoding="utf-8")
emit("item/NetworkSchematicQuillItem.java",'''package dev.obsidiannetwork.item;

import dev.obsidiannetwork.ObsidianNetwork;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import java.util.ArrayList;

/** V173_SCHEMATIC_QUILL: select two corners, transform into saved blueprint. */
public final class NetworkSchematicQuillItem extends NetworkBlueprintItem {
 public NetworkSchematicQuillItem(Properties p){super(p);}
'''+method+'''
}
''')
change("item/NetworkBlueprintItem.java",
 "public final class NetworkBlueprintItem extends Item {",
 "public class NetworkBlueprintItem extends Item {")
change("ObsidianNetwork.java",
 '''    public static final DeferredItem<dev.obsidiannetwork.item.NetworkBlueprintItem> NETWORK_BLUEPRINT =
        ITEMS.registerItem("network_blueprint",dev.obsidiannetwork.item.NetworkBlueprintItem::new);''',
 '''    public static final DeferredItem<dev.obsidiannetwork.item.NetworkBlueprintItem> NETWORK_BLUEPRINT =
        ITEMS.registerItem("network_blueprint",dev.obsidiannetwork.item.NetworkBlueprintItem::new);
    public static final DeferredItem<dev.obsidiannetwork.item.NetworkSchematicQuillItem> NETWORK_SCHEMATIC_QUILL =
        ITEMS.registerItem("network_schematic_quill",dev.obsidiannetwork.item.NetworkSchematicQuillItem::new);''')
change("ObsidianNetwork.java",
 '            output.accept((ItemLike)NETWORK_BLUEPRINT.get());',
 '            output.accept((ItemLike)NETWORK_BLUEPRINT.get());\n'+
 '            output.accept((ItemLike)NETWORK_SCHEMATIC_QUILL.get());')
# Require a completed Blueprint ID, never an unsaved quill.
change("menu/NetworkPrinterMenu.java",
 'return s.getItem() instanceof dev.obsidiannetwork.item.NetworkBlueprintItem;',
 'return s.is(dev.obsidiannetwork.ObsidianNetwork.NETWORK_BLUEPRINT.get());')
change("blockentity/NetworkDeviceBlockEntity.java",
 'if(slot==0&&(s.isEmpty()||s.getItem() instanceof NetworkBlueprintItem)){',
 'if(slot==0&&(s.isEmpty()||s.is(ObsidianNetwork.NETWORK_BLUEPRINT.get()))){')
# The last predicate occurs in the same file: canPlaceItem.
change("blockentity/NetworkDeviceBlockEntity.java",
 'return slot==0?s.getItem() instanceof NetworkBlueprintItem:',
 'return slot==0?s.is(ObsidianNetwork.NETWORK_BLUEPRINT.get()):')
# Battery is optional, but a real ENERGY cable has an actual block capability.
java=J/"blockentity/NetworkDeviceBlockEntity.java"
source=java.read_text(encoding="utf-8")
old=''' private ItemStack blueprint=ItemStack.EMPTY,energy=ItemStack.EMPTY;
 private int index=0,completed=0;'''
new=''' private ItemStack blueprint=ItemStack.EMPTY,energy=ItemStack.EMPTY;
 private long energyBuffer=0L;
 public static final long ENERGY_CAPACITY=250_000L;
 private final net.neoforged.neoforge.transfer.transaction.SnapshotJournal<Long> energyJournal=
     new net.neoforged.neoforge.transfer.transaction.SnapshotJournal<>() {
       @Override protected Long createSnapshot(){return energyBuffer;}
       @Override protected void revertToSnapshot(Long before){energyBuffer=before;}
       @Override protected void onRootCommit(Long before){
         if(before!=energyBuffer)setChanged();
       }
     };
 private final net.neoforged.neoforge.transfer.energy.EnergyHandler energyPort=
     new net.neoforged.neoforge.transfer.energy.EnergyHandler() {
       @Override public long getAmountAsLong(){return energyBuffer;}
       @Override public long getCapacityAsLong(){return ENERGY_CAPACITY;}
       @Override public int insert(int offered,
           net.neoforged.neoforge.transfer.transaction.TransactionContext tx){
         if(offered<=0||mode()!=NetworkDeviceBlock.Mode.PRINTER)return 0;
         int accepted=(int)Math.min((long)offered,ENERGY_CAPACITY-energyBuffer);
         if(accepted>0){energyJournal.updateSnapshots(tx);energyBuffer+=accepted;}
         return accepted;
       }
       @Override public int extract(int demand,
           net.neoforged.neoforge.transfer.transaction.TransactionContext tx){return 0;}
     };
 public net.neoforged.neoforge.transfer.energy.EnergyHandler energyPort(){return energyPort;}
 public long availableFE(){return energyBuffer+EnergyTool.energy(energy);}
 private boolean spendFE(long amount){
  if(energyBuffer>=amount){energyBuffer-=amount;setChanged();return true;}
  if(EnergyTool.energy(energy)>=amount){EnergyTool.consume(energy,amount);sync();return true;}
  return false;
 }
 private int index=0,completed=0;'''
assert source.count(old)==1
source=source.replace(old,new,1)
old='''  if(EnergyTool.energy(energy)<250L){setStatus("FE LOW: need 250 FE/block");return;}'''
new='''  if(availableFE()<250L){setStatus("NO POWER: connect ENERGY cable (250 FE/block)");return;}'''
assert source.count(old)==1
source=source.replace(old,new,1)
old='''  EnergyTool.consume(energy,250L);
  index++;completed++;'''
new='''  if(!spendFE(250L))throw new IllegalStateException("Printer FE preflight violated");
  index++;completed++;'''
assert source.count(old)==1
source=source.replace(old,new,1)
old='''  out.putInt("index",index);out.putInt("completed",completed);'''
new='''  out.putLong("energyBuffer",energyBuffer);
  out.putInt("index",index);out.putInt("completed",completed);'''
assert source.count(old)==1
source=source.replace(old,new,1)
old='''  index=Math.max(0,in.getIntOr("index",0));completed=Math.max(0,in.getIntOr("completed",0));'''
new='''  energyBuffer=Math.max(0L,Math.min(ENERGY_CAPACITY,in.getLongOr("energyBuffer",0L)));
  index=Math.max(0,in.getIntOr("index",0));completed=Math.max(0,in.getIntOr("completed",0));'''
assert source.count(old)==1
java.write_text(source.replace(old,new,1),encoding="utf-8")
emit("blockentity/NetworkPrinterEnergyCapabilities.java",r'''package dev.obsidiannetwork.blockentity;

import dev.obsidiannetwork.block.NetworkDeviceBlock;
import dev.obsidiannetwork.registry.ModBlockEntities;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.capabilities.RegisterCapabilitiesEvent;

/** V173_PRINTER_WIRED_FE: Energy Cable can charge the Printer. NOT wireless FE. */
@EventBusSubscriber(modid="obsidiannetwork")
public final class NetworkPrinterEnergyCapabilities {
 private NetworkPrinterEnergyCapabilities(){}
 @SubscribeEvent public static void register(RegisterCapabilitiesEvent event){
  event.registerBlockEntity(Capabilities.Energy.BLOCK,ModBlockEntities.NETWORK_DEVICE.get(),
    (device,side)->device.mode()==NetworkDeviceBlock.Mode.PRINTER?device.energyPort():null);
 }
}
''')
jsonfile(R/"models/item/network_schematic_quill.json",
  {"parent":"minecraft:item/generated","textures":{"layer0":"minecraft:item/writable_book"}})
jsonfile(R/"items/network_schematic_quill.json",
  {"model":{"type":"minecraft:model","model":"obsidiannetwork:item/network_schematic_quill"}})
jsonfile(D/"recipe/network_schematic_quill.json",
  {"type":"minecraft:crafting_shaped","pattern":["PFP","BIB","PFP"],
   "key":{"P":"minecraft:paper","F":"minecraft:feather","B":"minecraft:book","I":"minecraft:ink_sac"},
   "result":{"id":"obsidiannetwork:network_schematic_quill","count":1}})
# A completed Blueprint is created only by marking the two corners.
p=D/"recipe/network_blueprint.json"
if p.exists():p.unlink()
for language in ("de_de","en_us"):
 p=R/"lang"/(language+".json")
 languageData=json.loads(p.read_text(encoding="utf-8"))
 languageData["item.obsidiannetwork.network_blueprint"]="Saved Blueprint" if language=="en_us" else "Gespeicherter Bauplan"
 languageData["item.obsidiannetwork.network_schematic_quill"]="Schematic & Quill" if language=="en_us" else "Schematic & Quill (Bauplan-Stift)"
 jsonfile(p,languageData)
assert "NetworkBlueprintItem extends Item" in (J/"item/NetworkBlueprintItem.java").read_text()
assert "user.setItemInHand(context.getHand(),finished)" in (J/"item/NetworkSchematicQuillItem.java").read_text()
assert "Capabilities.Energy.BLOCK" in (J/"blockentity/NetworkPrinterEnergyCapabilities.java").read_text()
print("V173_PRINTER_QUILL_POWER_PASS: separate two-corner quill, genuine saved blueprint, 250k FE cable-backed Printer, never wireless FE")
