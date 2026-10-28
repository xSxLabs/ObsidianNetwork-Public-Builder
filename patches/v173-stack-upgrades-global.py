#!/usr/bin/env python3
"""v1.7.3: Stack upgrade throughput across standalone ITEM cable, bundled
conduits and network Importer/Exporter. Applied after final ITEM tick patches.
Fail closed on source drift; no change to fluid/FE transports.
"""
import os
from pathlib import Path
ROOT=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def patch(rel, old, new):
    path=ROOT/rel
    src=path.read_text(encoding="utf8")
    matches=src.count(old)
    assert matches==1,("STACK_THROUGHPUT_SOURCE_DRIFT",rel,matches,old[:140])
    path.write_text(src.replace(old,new,1),encoding="utf8")

def edit_file(rel,fn):
    path=ROOT/rel
    s=path.read_text(encoding="utf8")
    v=fn(s)
    assert v!=s,("STACK_THROUGHPUT_NOOP",rel)
    path.write_text(v,encoding="utf8")

# Standalone ITEM cables: one full stack attempt for each installed upgrade,
# maximum sixteen. A pass is never consumed if all destinations are blocked.
# A per-input output cursor prevents the first of seven machines monopolizing
# the flow. Fluid throughput is deliberately not touched.
standalone=r''' private final int[] xsxItemOutputCursor=new int[6],xsxItemInputCursor=new int[6];
 private void transferItem(Direction in){
  var sourceRaw=level.getCapability(Capabilities.Item.BLOCK,
       worldPosition.relative(in),in.getOpposite());
  IItemHandler src=sourceRaw==null?null:IItemHandler.of(sourceRaw);
  if(src==null||src.getSlots()<=0)return;
  java.util.List<Endpoint> destinations=exports();
  if(destinations.isEmpty())return;
  int side=in.ordinal(),operations=Math.max(1,Math.min(16,stacks(in)));
  for(int op=0;op<operations;op++){
   boolean progressed=false;
   int nslots=src.getSlots(),offset=Math.floorMod(xsxItemInputCursor[side],nslots);
   for(int j=0;j<nslots&&!progressed;j++){
    int si=(offset+j)%nslots;
    ItemStack sample=src.extractItem(si,64,true);
    if(sample.isEmpty())continue;
    int start=Math.floorMod(xsxItemOutputCursor[side],destinations.size());
    for(int k=0;k<destinations.size();k++){
     Endpoint e=destinations.get((start+k)%destinations.size());
     var targetRaw=level.getCapability(Capabilities.Item.BLOCK,
         e.pos.relative(e.side),e.side.getOpposite());
     IItemHandler dst=targetRaw==null?null:IItemHandler.of(targetRaw);
     if(dst==null)continue;
     ItemStack probe=sample.copy();
     for(int di=0;di<dst.getSlots()&&!probe.isEmpty();di++)
      probe=dst.insertItem(di,probe,true);
     int accepted=sample.getCount()-probe.getCount();
     if(accepted<=0)continue;
     ItemStack taken=src.extractItem(si,accepted,false);
     if(taken.isEmpty())continue;
     ItemStack rest=taken;
     for(int di=0;di<dst.getSlots()&&!rest.isEmpty();di++)
      rest=dst.insertItem(di,rest,false);
     int delivered=taken.getCount()-rest.getCount();
     if(!rest.isEmpty()){
      for(int ri=0;ri<src.getSlots()&&!rest.isEmpty();ri++)
       rest=src.insertItem(ri,rest,false);
      // A modded target can reject between SIMULATE and EXECUTE.
      // The source is the first rollback destination. If that fails,
      // return the remainder to the world rather than deleting it.
      if(!rest.isEmpty())net.minecraft.world.Containers.dropItemStack(
          level,worldPosition.getX()+.5,worldPosition.getY()+.5,
          worldPosition.getZ()+.5,rest.copy());
     }
     if(delivered>0){
      xsxItemInputCursor[side]=(si+1)%nslots;
      xsxItemOutputCursor[side]=(start+k+1)%destinations.size();
      progressed=true;
      break;
     }
    }
   }
   if(!progressed)break;
  }
 }
'''
def modify_standalone(s):
    anchor=' private void transferItem(Direction in){'
    stop=' private void transferFluid(Direction in){'
    assert s.count(anchor)==1 and s.count(stop)==1
    a=s.index(anchor)
    b=s.index(stop,a)
    return s[:a]+standalone+s[b:]
edit_file("blockentity/LogisticsCableBlockEntity.java",modify_standalone)

# Mixed/bundled ITEM transport runs through the centralized ticker.
# Previously it returned after one successful move, regardless of upgrades.
# Use the source-side upgrade count on either physical cable type.
network=r'''   for(var src:sources){
    var raw=level.getCapability(Capabilities.Item.BLOCK,
        src.pos().relative(src.side()),src.side().getOpposite());
    IItemHandler from=raw==null?null:IItemHandler.of(raw);
    if(from==null||from.getSlots()<=0)continue;
    int operations=1;
    var cable=level.getBlockEntity(src.pos());
    if(cable instanceof dev.obsidiannetwork.blockentity.LogisticsCableBlockEntity standalone)
     operations=Math.max(1,Math.min(16,standalone.stacks(src.side())));
    else if(cable instanceof dev.obsidiannetwork.blockentity.ConduitBundleBlockEntity bundle)
     operations=Math.max(1,Math.min(16,bundle.logisticsStack(
        dev.obsidiannetwork.blockentity.ConduitBundleBlockEntity.Layer.ITEM,src.side())));
    long slotKey=src.pos().asLong()^(long)(src.side().ordinal()+1)*0x9E3779B97F4A7C15L;
    for(int op=0;op<operations;op++){
     boolean progressed=false;
     int nslots=from.getSlots();
     int firstSlot=Math.floorMod(sourceSlotCursor.getOrDefault(slotKey,0),nslots);
     for(int offset=0;offset<nslots&&!progressed;offset++){
      int si=(firstSlot+offset)%nslots;
      ItemStack sample=from.extractItem(si,64,true);
      if(sample.isEmpty())continue;
      int start=Math.floorMod(rr.getOrDefault(slotKey,0),targets.size());
      for(int k=0;k<targets.size();k++){
       var dst=targets.get((start+k)%targets.size());
       if(!src.config().selfFeed()&&dst.pos().equals(src.pos())
          &&dst.side()==src.side())continue;
       var dr=level.getCapability(Capabilities.Item.BLOCK,
           dst.pos().relative(dst.side()),dst.side().getOpposite());
       IItemHandler to=dr==null?null:IItemHandler.of(dr);
       if(to==null)continue;
       ItemStack probe=sample.copy();
       for(int di=0;di<to.getSlots()&&!probe.isEmpty();di++)
        probe=to.insertItem(di,probe,true);
       int accepted=sample.getCount()-probe.getCount();
       if(accepted<=0)continue;
       ItemStack taken=from.extractItem(si,accepted,false);
       if(taken.isEmpty())continue;
       ItemStack remainder=taken;
       for(int di=0;di<to.getSlots()&&!remainder.isEmpty();di++)
        remainder=to.insertItem(di,remainder,false);
       int delivered=taken.getCount()-remainder.getCount();
       if(!remainder.isEmpty()){
        for(int ri=0;ri<from.getSlots()&&!remainder.isEmpty();ri++)
         remainder=from.insertItem(ri,remainder,false);
        if(!remainder.isEmpty())net.minecraft.world.Containers.dropItemStack(
            level,src.pos().getX()+.5,src.pos().getY()+.5,
            src.pos().getZ()+.5,remainder.copy());
       }
       if(delivered>0){
        sourceSlotCursor.put(slotKey,(si+1)%nslots);
        rr.put(slotKey,(start+k+1)%targets.size());
        progressed=true;
        break;
       }
      }
     }
     if(!progressed)break;
    }
   }
'''
def modify_ticker(s):
    anchor='for(var src:sources){'
    assert s.count(anchor)==1,("ITEM_TICKER_ANCHOR_DRIFT",s.count(anchor))
    i=s.index(anchor)
    a=s.rfind('\n',0,i)+1  # preserve generated indentation changes
    # Locate the matching for-loop brace; decompilation/CI may alter
    # method indentation, so never rely on text at the end of the class.
    opening=s.index('{',i)
    depth=0
    end=-1
    for cursor in range(opening,len(s)):
        if s[cursor]=='{':
            depth+=1
        elif s[cursor]=='}':
            depth-=1
            if depth==0:
                end=cursor+1
                break
    assert end>a and depth==0 and 'sourceSlotCursor.put' in s[a:end], "ITEM_TICKER_FOR_LOOP_DRIFT"
    return s[:a]+network.rstrip('\n')+s[end:]
edit_file("conduit/ItemConduitTicker.java",modify_ticker)

# Bundle ITEM upgrades also accept sixteen (formerly silently clipped to 8).
# Do not change energy or fluid layer upgrade limits.
patch("blockentity/ConduitBundleBlockEntity.java",
  "if(q.getCount()>8)q.setCount(8);",
  "if(q.getCount()>16)q.setCount(16);")
patch("blockentity/ConduitBundleBlockEntity.java",
  'copyRaw(in.getIntArray("mc_item_stack").orElse(new int[0]),logisticsStack[0],8);',
  'copyRaw(in.getIntArray("mc_item_stack").orElse(new int[0]),logisticsStack[0],16);')

# Importer and Exporter: previous cap 4 and 256 items did not mean 4 stacks,
# and the runtime's slot attempt limit was tighter still.
for rel in ("blockentity/ImporterBlockEntity.java",
            "blockentity/ExporterBlockEntity.java"):
    patch(rel,
      "this.stackUpgrades = Math.max(0, Math.min(4, c));",
      "this.stackUpgrades = Math.max(0, Math.min(16, c));")
    patch(rel,
      "this.stackUpgrades < 4",
      "this.stackUpgrades < 16")
    patch(rel,
      "int itemBudget = (int)Math.min(256L, 64L << Math.min(2, be.stackUpgrades));",
      "int itemBudget = 64*Math.max(1,Math.min(16,be.stackUpgrades));")
    def broaden_ops(s):
        import re
        old=re.findall(r'be.runtime.runCycle\(new MinecraftExternalItemPort\(handler, new MinecraftItemStackCodec\(server.registryAccess\(\)\)\), (?:8|4), itemBudget\);',s)
        assert len(old)==1,("TRANSFER_NODE_RUNTIME_ANCHOR_DRIFT",rel,len(old))
        return s.replace(old[0],old[0].replace(", 8, itemBudget)",", 16, itemBudget)").replace(", 4, itemBudget)",", 16, itemBudget)"),1)
    edit_file(rel,broaden_ops)

# Transfer Node GUI and backed upgrade container must agree with runtime.
gui="menu/TransferNodeMenu.java"
patch(gui,
   "return s == 1 && this.stack() > 0 ? new ItemStack((ItemLike)ObsidianNetwork.STACK_UPGRADE.get(), this.stack()) : ItemStack.EMPTY;",
   "return s == 1 && this.stack() > 0 ? new ItemStack((ItemLike)ObsidianNetwork.STACK_UPGRADE.get(), this.stack()) : ItemStack.EMPTY; // XSXLABS_STACK_16_IMPORT_EXPORT")
def upgrade_gui(s):
    marker="return s.is((Item)ObsidianNetwork.STACK_UPGRADE.get());"
    # The upgrade slot contains a dedicated max-stack method, not a player slot.
    i=s.index(marker)
    j=s.index("public int getMaxStackSize()",i)
    section=s[j:j+100]
    assert "return 4;" in section,("STACK_SLOT_MAX_DRIFT",section)
    s=s[:j]+s[j:].replace("return 4;","return 16;",1)
    setslot="this.setStack(v.is((Item)ObsidianNetwork.STACK_UPGRADE.get()) ? Math.min(4, v.getCount()) : 0);"
    assert s.count(setslot)==1
    s=s.replace(setslot,
      "this.setStack(v.is((Item)ObsidianNetwork.STACK_UPGRADE.get()) ? Math.min(16, v.getCount()) : 0);",1)
    rm="return this.removeItem(s, 4);"
    assert s.count(rm)==1
    s=s.replace(rm,"return this.removeItem(s, s == 1 ? 16 : 4);",1)
    return s
edit_file(gui,upgrade_gui)

# Safety/source contract checks before full Gradle and real server GameTests.
ticker=(ROOT/"conduit/ItemConduitTicker.java").read_text()
cable=(ROOT/"blockentity/LogisticsCableBlockEntity.java").read_text()
assert "XSXLABS_BUNDLE_TPS_CACHE_V1" in ticker
assert "if(network.type()!=ConduitType.ITEM||level.getGameTime()%5!=0)return;" in ticker
assert "rr.put(slotKey,(start+k+1)%targets.size())" in ticker
assert "MAX" not in "stacks(in)" or "Math.min(16,stacks(in))" in cable
assert "if(!progressed)break;" in ticker and "if(!progressed)break;" in cable
assert "Math.min(16,be.stackUpgrades)" in (ROOT/"blockentity/ExporterBlockEntity.java").read_text()
print("V173_STACK_THROUGHPUT_16_GLOBAL_PASS")
