#!/usr/bin/env python3
"""B1807 1.7.8 v14: live-first map region updates, independent GUI slots,
correct shift-click routing, and bounded high-throughput transactional output.
No forced chunk loading, no client render-frame sampling or output duplication.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def replace_once(rel, old, new):
    path=J/rel
    source=path.read_text(encoding="utf-8")
    assert source.count(old)==1, ("B1807_SOURCE_DRIFT",rel,old[:130],source.count(old))
    path.write_text(source.replace(old,new,1),encoding="utf-8")

terrain="client/V178TerrainMap.java"
# B1657 archiveLookup() was returning the old snapshot before the loaded
# chunk's live block states were ever sampled. RefreshSurface() therefore
# repeatedly removed and immediately restored the same stale old tile.
# Archived tiles are appropriate only for unloaded chunks (map browsing).
replace_once(terrain,
    "  int[] explored=archiveLookup(cx,cz);",
    "  int[] explored=world.hasChunk(cx,cz)?null:archiveLookup(cx,cz);")
# B1657 putIfAbsent made the archive a permanent first-visit snapshot.
# Replace only changed 16x16 tiles, preserving no-op cheap updates and
# existing file format/atomic flush path; no forced chunk loads.
replace_once(terrain,
    "  if(r!=null&&r.tiles.putIfAbsent(pos(cx,cz),colors)==null)r.dirty=true;",
    """  if(r!=null){
   long key=pos(cx,cz);
   int[] previous=r.tiles.get(key);
   if(!java.util.Arrays.equals(previous,colors)){
    r.tiles.put(key,colors);
    r.dirty=true;
   }
  }""")
# RefreshSurface already detects true color changes and bumps atlasRevision,
# triggering both the minimap texture and fullscreen map texture refresh.
source=(J/terrain).read_text(encoding="utf-8")
for token in (
    "world.hasChunk(cx,cz)?null:archiveLookup(cx,cz)",
    "!java.util.Arrays.equals(previous,colors)",
    "java.util.Arrays.equals(before,after)",
    "V178MiniRaster.tick(world);", "updateAtlas(world,cx,cz);",
    "private static final int ATLAS_UPDATE_TICKS=1;",
    "if(!world.hasChunk(cx,cz))return;",
):
    assert token in source,("B1807_MAP_CONTRACT",token)

# Client ChestMenu's card+speed items share one 27-slot SimpleContainer,
# so client slot 1 MUST use item index 1. The server's special 1-slot
# SpeedStorage container correctly uses item index 0, but copying that
# server index into the client duplicated the visual and drag/drop slots.
replace_once("client/V178MiningBuilderOperationsScreen.java",
    "new Slot(speedSlot.container,0,143,27){",
    "new Slot(speedSlot.container,1,143,27){")

# Vanilla shift-click for both dedicated input slots. Exclude the 25 hidden
# machine slots so shape cards and speed items cannot land in outputs.
menu="mining/V178MiningBuilderMenu.java"
path=J/menu
source=path.read_text(encoding="utf-8")
first="  if(slot<0||slot>=slots.size()||!stillValid(player))return ItemStack.EMPTY;"
last="  return original;"
assert source.count(first)==1 and source.count(last)==1, "B1807_QUICKMOVE_METHOD_DRIFT"
a=source.index(first)
b=source.index(last,a)+len(last)
original=source[a:b]
assert "if(slot==0||(slot>1&&slot<27))return ItemStack.EMPTY;" in original
assert "moveItemStackTo(held,1,2,false)" in original
replacement="""  if(slot<0||slot>=slots.size()||!stillValid(player))return ItemStack.EMPTY;
  if(slot>1&&slot<27)return ItemStack.EMPTY; // hidden, never shift-transfer
  Slot source=slots.get(slot);
  if(!source.hasItem()||!source.mayPickup(player))return ItemStack.EMPTY;
  ItemStack held=source.getItem();
  ItemStack original=held.copy();
  boolean moved;
  if(slot==0||slot==1){
   moved=moveItemStackTo(held,27,63,true);
  }else if(slot>=27&&slot<63){
   if(held.getItem() instanceof V178MiningShapeCard){
    moved=moveItemStackTo(held,0,1,false);
   }else if(V178MiningBuilderBE.isSpeedUpgrade(held)){
    moved=moveItemStackTo(held,1,2,false);
   }else return ItemStack.EMPTY;
  }else return ItemStack.EMPTY;
  if(!moved)return ItemStack.EMPTY;
  if(held.isEmpty())source.setByPlayer(ItemStack.EMPTY);
  else source.setChanged();
  return original;"""
path.write_text(source[:a]+replacement+source[b:],encoding="utf-8")

# The old output removed at most ONE stack every FIVE ticks. Batch up to
# 32 successful, atomic transfers per tick, reusing each neighbor capability
# for all 27 output slots (maximum six loaded neighbors; no chunk loads).
# A failed/partial extract rolls back both sides of the transaction.
be="mining/V178MiningBuilderBE.java"
path=J/be
source=path.read_text(encoding="utf-8")
first=" private void output(ServerLevel world){"
last="\n public static void serverTick("
assert source.count(first)==1 and source.count(last)==1,"B1807_EXPORT_METHOD_DRIFT"
a=source.index(first)
b=source.index(last,a)
old=source[a:b]
assert "if(world.getGameTime()%5!=0)return;" in old
assert "tx.commit();" in old and "output.extract(slot,what,accepted,tx)==accepted" in old
replacement=""" private void output(ServerLevel world){
  // B1807_BATCHED_OUTPUT: at most 32 committed full/partial stacks each tick.
  // Empty machine avoids all 6 expensive neighbor capability lookups.
  boolean hasOutput=false;
  for(int slot=0;slot<27;slot++)if(output.getAmountAsInt(slot)>0){
   hasOutput=true;break;
  }
  if(!hasOutput)return;
  int movedStacks=0;
  int firstSlot=nextOutputSlot;
  for(Direction side:SIDES){
   if(movedStacks>=32)break;
   BlockPos at=worldPosition.relative(side);
   if(!world.hasChunkAt(at))continue;
   ResourceHandler<ItemResource> destination=world.getCapability(
        Capabilities.Item.BLOCK,at,side.getOpposite());
   if(destination==null||destination==output)continue;
   for(int step=0;step<27&&movedStacks<32;step++){
    int slot=(firstSlot+step)%27;
    int count=output.getAmountAsInt(slot);
    if(count<=0)continue;
    ItemResource what=output.getResource(slot);
    if(what.isEmpty())continue;
    try(Transaction tx=Transaction.openRoot()){
     int accepted=destination.insert(what,count,tx);
     if(accepted>0&&output.extract(slot,what,accepted,tx)==accepted){
      tx.commit();
      movedStacks++;
      nextOutputSlot=(slot+1)%27;
     }
    }
   }
  }
 }"""
path.write_text(source[:a]+replacement+source[b:],encoding="utf-8")

assert "new Slot(speedSlot.container,1,143,27){" in (J/"client/V178MiningBuilderOperationsScreen.java").read_text()
menu=(J/menu).read_text()
assert "moveItemStackTo(held,0,1,false)" in menu and "moveItemStackTo(held,1,2,false)" in menu
assert "if(slot>1&&slot<27)return ItemStack.EMPTY" in menu
miner=(J/be).read_text()
assert "B1807_BATCHED_OUTPUT" in miner and "tx.commit()" in miner
print("B1807_V14_LIVE_MAP_ARCHIVE_REWRITE_INDEPENDENT_SLOTS_SHIFT_ROUTING_BATCHED_OUTPUT_PASS")
