#!/usr/bin/env python3
"""B857 staged v1.7.6: Equipment Cell in all backpack lanes, terminal-style transactions,
and dimensional 1x/2x Cobble / 1x Obsidian item models.

Runs AFTER B847 on reconstructed 26.1 sources. Fails closed if anchors drift.
No workflow build marker is granted by this source-only change.
"""
import json
import os
from pathlib import Path
from PIL import Image, ImageDraw

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"

def patch(rel,old,new,n=1):
    p=J/rel
    s=p.read_text(encoding="utf-8")
    assert s.count(old)==n, ("B857_DRIFT",rel,s.count(old),old[:110])
    p.write_text(s.replace(old,new,n),encoding="utf-8")

def replace_between(rel,start,end,content):
    p=J/rel
    s=p.read_text(encoding="utf-8")
    assert s.count(start)==1 and s.count(end)==1 and s.index(end)>s.index(start), ("B857_METHOD_DRIFT",rel,start,end)
    s=s[:s.index(start)]+content+s[s.index(end):]
    p.write_text(s,encoding="utf-8")

cells="backpack/V176BackpackCells.java"
patch(cells,"import dev.obsidiannetwork.item.StorageCellItem;",
            "import dev.obsidiannetwork.item.StorageCellItem;\nimport dev.obsidiannetwork.item.EquipmentCellItem;\nimport dev.obsidiannetwork.core.EquipmentCellStore;\nimport dev.obsidiannetwork.core.EquipmentEligibility;")
patch(cells,"if(!list.get(i).isEmpty()&&!(list.get(i).getItem() instanceof StorageCellItem))",
            "if(!list.get(i).isEmpty()&&!(list.get(i).getItem() instanceof StorageCellItem)\n       &&!(list.get(i).getItem() instanceof EquipmentCellItem))")
patch(cells,"if(i>=1&&!stack.isEmpty()&&!(stack.getItem() instanceof StorageCellItem))",
            "if(i>=1&&!stack.isEmpty()&&!(stack.getItem() instanceof StorageCellItem)\n       &&!(stack.getItem() instanceof EquipmentCellItem))")
patch(cells,"if(entries.get(i).getItem() instanceof StorageCellItem cell)\n    total=Math.addExact(total,cell.tier().capacity());",
            "if(entries.get(i).getItem() instanceof StorageCellItem cell)\n    total=Math.addExact(total,cell.tier().capacity());\n   else if(entries.get(i).getItem() instanceof EquipmentCellItem)\n    total=Math.addExact(total,EquipmentCellStore.CAPACITY);")
patch(cells,"if(entries.get(i).getItem() instanceof StorageCellItem cell)\n    total=Math.addExact(total,cell.readStore(entries.get(i)).used());",
            "if(entries.get(i).getItem() instanceof StorageCellItem cell)\n    total=Math.addExact(total,cell.readStore(entries.get(i)).used());\n   else if(entries.get(i).getItem() instanceof EquipmentCellItem eq)\n    total=Math.addExact(total,eq.readStore(entries.get(i)).used());")

replace_between(cells,
 " public static Transfer insert(Level world,ItemStack bag,ItemStack incoming,long requested){",
 " public static List<Entry> entries(ItemStack bag){",
 """ public static Transfer insert(Level world,ItemStack bag,ItemStack incoming,long requested){
  if(requested<0)throw new IllegalArgumentException("negative insertion");
  if(requested==0||incoming.isEmpty()||incoming.getItem() instanceof NetworkBackpackItem)
   return new Transfer(0,requested);
  MinecraftItemStackCodec codec=new MinecraftItemStackCodec(world.registryAccess());
  ExactStackDescriptor d=codec.describe(incoming);
  var installed=slots(bag);
  var replacements=new ArrayList<>(installed);
  long left=requested;
  boolean equipment=EquipmentEligibility.isEquipment(d.key());
  // Existing exact item types first. Equipment Cells get priority for gear.
  // Each native cell format remains intact: never reinterpret equipment data
  // as an ordinary StorageCellStore.
  for(int phase=0;phase<2&&left>0;phase++){
   for(int lane=0;lane<2&&left>0;lane++){
    for(int i=1;i<=3&&left>0;i++){
     ItemStack cellStack=replacements.get(i);
     if(equipment&&lane==0&&cellStack.getItem() instanceof EquipmentCellItem cell){
      EquipmentCellStore store=cell.readStore(cellStack);
      boolean present=store.amount(d.key())>0;
      if((phase==0)!=present)continue;
      long accepted=store.previewInsertExact(d.key(),d.canonicalPayload(),left);
      if(accepted<=0)continue;
      store.insertExact(d.key(),d.canonicalPayload(),accepted);
      ItemStack updated=cellStack.copy();
      cell.writeStore(updated,store);
      replacements.set(i,updated);
      left-=accepted;
     }else if(lane==1&&cellStack.getItem() instanceof StorageCellItem cell){
      StorageCellStore store=cell.readStore(cellStack);
      boolean present=store.amount(d.key())>0;
      if((phase==0)!=present)continue;
      long accepted=store.previewInsertExact(d.key(),d.canonicalPayload(),left);
      if(accepted<=0)continue;
      store.insertExact(d.key(),d.canonicalPayload(),accepted);
      ItemStack updated=cellStack.copy();
      cell.writeStore(updated,store);
      replacements.set(i,updated);
      left-=accepted;
     }
    }
   }
  }
  if(left<requested)writeSlots(bag,replacements);
  return new Transfer(requested-left,left);
 }

""")
replace_between(cells,
 " public static List<Entry> entries(ItemStack bag){",
 " public static long count(ItemStack bag,ItemKey key){",
 """ public static List<Entry> entries(ItemStack bag){
  Map<ItemKey,Entry> data=new HashMap<>();
  var items=slots(bag);
  for(int i=1;i<=3;i++){
   ItemStack stack=items.get(i);
   Map<ItemKey,Long> snapshot;
   java.util.function.Function<ItemKey,byte[]> descriptor;
   if(stack.getItem() instanceof StorageCellItem cell){
    var store=cell.readStore(stack);
    snapshot=store.snapshot(); descriptor=store::descriptor;
   }else if(stack.getItem() instanceof EquipmentCellItem eq){
    var store=eq.readStore(stack);
    snapshot=store.snapshot(); descriptor=store::descriptor;
   }else continue;
   for(var entry:snapshot.entrySet()){
    byte[] exact=descriptor.apply(entry.getKey());
    if(exact==null||entry.getValue()<=0)continue;
    var desc=new ExactStackDescriptor(entry.getKey().itemId(),exact);
    var previous=data.get(entry.getKey());
    data.put(entry.getKey(),new Entry(desc,
      Math.addExact(entry.getValue(),previous==null?0L:previous.count())));
   }
  }
  var sorted=new ArrayList<>(data.values());
  sorted.sort(java.util.Comparator
    .comparing((Entry e)->e.descriptor().key().itemId().toString())
    .thenComparing((a,b)->java.util.Arrays.compareUnsigned(
      a.descriptor().canonicalPayload(),b.descriptor().canonicalPayload())));
  return List.copyOf(sorted);
 }

""")
replace_between(cells,
 " public static long count(ItemStack bag,ItemKey key){",
 " public static ItemStack magnet(ItemStack bag){",
 """ public static long count(ItemStack bag,ItemKey key){
  long count=0;
  var cellSlots=slots(bag);
  for(int i=1;i<=3;i++){
   ItemStack stack=cellSlots.get(i);
   if(stack.getItem() instanceof StorageCellItem cell)
    count=Math.addExact(count,cell.readStore(stack).amount(key));
   else if(stack.getItem() instanceof EquipmentCellItem eq)
    count=Math.addExact(count,eq.readStore(stack).amount(key));
  }
  return count;
 }
 public static Transfer extract(Level world,ItemStack bag,ExactStackDescriptor d,long wanted){
  if(wanted<0)throw new IllegalArgumentException("negative extraction");
  if(wanted==0)return new Transfer(0,0);
  var next=new ArrayList<>(slots(bag));
  long left=wanted;
  for(int i=1;i<=3&&left>0;i++){
   ItemStack stack=next.get(i);
   if(stack.getItem() instanceof StorageCellItem cell){
    StorageCellStore store=cell.readStore(stack);
    byte[] existing=store.descriptor(d.key());
    if(existing==null||!java.util.Arrays.equals(existing,d.canonicalPayload()))continue;
    long n=store.extract(d.key(),left);
    if(n<=0)continue;
    ItemStack updated=stack.copy();
    cell.writeStore(updated,store);
    next.set(i,updated);
    left-=n;
   }else if(stack.getItem() instanceof EquipmentCellItem eq){
    EquipmentCellStore store=eq.readStore(stack);
    byte[] existing=store.descriptor(d.key());
    if(existing==null||!java.util.Arrays.equals(existing,d.canonicalPayload()))continue;
    long n=store.extract(d.key(),left);
    if(n<=0)continue;
    ItemStack updated=stack.copy();
    eq.writeStore(updated,store);
    next.set(i,updated);
    left-=n;
   }
  }
  if(left<wanted)writeSlots(bag,next);
  return new Transfer(wanted-left,left);
 }

""")
# The GUI accepts Equipment Cell exactly where ordinary cells are accepted.
menu="backpack/V176BackpackMenu.java"
patch(menu,"import dev.obsidiannetwork.item.StorageCellItem;",
          "import dev.obsidiannetwork.item.StorageCellItem;\nimport dev.obsidiannetwork.item.EquipmentCellItem;\nimport net.minecraft.world.inventory.ContainerInput;")
patch(menu,"return stack.getItem() instanceof StorageCellItem;\n  }",
          "return stack.getItem() instanceof StorageCellItem\n        ||stack.getItem() instanceof EquipmentCellItem;\n  }")
patch(menu,"return stack.getItem() instanceof StorageCellItem cell\n        &&cell.readStore(stack).used()==0;",
          "return stack.getItem() instanceof StorageCellItem cell\n        &&cell.readStore(stack).used()==0\n       ||stack.getItem() instanceof EquipmentCellItem eq\n        &&eq.readStore(stack).used()==0;")
# An empty magnet/cell slot is still a real module slot, but the item list is NOT.
replace_between(menu,
 " @Override public ItemStack quickMoveStack(Player p,int index){",
 " public boolean toggleFilterEditor(ServerPlayer player){",
 """ @Override public ItemStack quickMoveStack(Player p,int index){
  if(!(p instanceof ServerPlayer player)||!storage.source.valid())return ItemStack.EMPTY;
  // Player inventory is slots 54..89; the 45 previews are virtual.
  if(index>=4&&index<49){
   shiftWithdraw(player,index);
   return ItemStack.EMPTY;
  }
  if(index<54||index>=slots.size())return ItemStack.EMPTY;
  Slot slot=slots.get(index);
  ItemStack current=slot.getItem();
  if(current.isEmpty()||current.getItem() instanceof NetworkBackpackItem)
   return ItemStack.EMPTY;
  int moduleSlot=-1;
  if(current.is(ObsidianNetwork.NETWORK_BACKPACK_MAGNET_UPGRADE.get()))
   moduleSlot=0;
  else if(current.getItem() instanceof StorageCellItem
       ||current.getItem() instanceof EquipmentCellItem){
   var installed=V176BackpackCells.slots(storage.source.current());
   for(int i=1;i<=3;i++)if(installed.get(i).isEmpty()){moduleSlot=i;break;}
  }
  if(moduleSlot>=0){
   ItemStack single=current.copy();single.setCount(1);
   ItemStack bag=storage.source.current().copy();
   if(!V176BackpackCells.putUpgrade(bag,moduleSlot,single)
       ||!storage.source.save(bag))return ItemStack.EMPTY;
   current.shrink(1);
   slot.setChanged();broadcastChanges();
   return single;
  }
  // Never hide a spare Storage Cell/Magnet inside its own backpack storage.
  if(current.getItem() instanceof StorageCellItem
     ||current.getItem() instanceof EquipmentCellItem
     ||current.is(ObsidianNetwork.NETWORK_BACKPACK_MAGNET_UPGRADE.get()))
   return ItemStack.EMPTY;
  ItemStack candidate=storage.source.current().copy();
  var result=V176BackpackCells.insert(player.level(),candidate,current,current.getCount());
  if(result.accepted()<=0||!storage.source.save(candidate))return ItemStack.EMPTY;
  ItemStack moved=current.copy();moved.setCount((int)result.accepted());
  current.shrink((int)result.accepted());
  slot.setChanged();broadcastChanges();
  return moved;
 }
 /** Count matching empty slots and component-equal partial stacks BEFORE
  * committing a withdrawal. Full inventory never causes ghost drops.
  */
 private int freeInventorySpace(ServerPlayer player,ItemStack sample){
  int free=0;
  for(int i=0;i<36;i++){
   ItemStack slot=player.getInventory().getItem(i);
   if(slot.isEmpty())free+=sample.getMaxStackSize();
   else if(ItemStack.isSameItemSameComponents(slot,sample))
    free+=Math.max(0,Math.min(slot.getMaxStackSize(),sample.getMaxStackSize())-slot.getCount());
   if(free>=sample.getMaxStackSize())return sample.getMaxStackSize();
  }
  return free;
 }
 private boolean shiftWithdraw(ServerPlayer player,int slotId){
  if(storage.filterEditor||!storage.source.valid())return false;
  var entry=storage.viewed(slotId);
  if(entry==null)return false;
  var codec=new dev.obsidiannetwork.platform.MinecraftItemStackCodec(player.level().registryAccess());
  ItemStack output=codec.recreate(entry.descriptor(),1);
  int count=(int)Math.min(Math.min(entry.count(),output.getMaxStackSize()),
                          freeInventorySpace(player,output));
  if(count<=0)return false;
  output.setCount(count);
  ItemStack candidate=storage.source.current().copy();
  var extraction=V176BackpackCells.extract(player.level(),candidate,entry.descriptor(),count);
  if(extraction.accepted()!=count||!storage.source.save(candidate))return false;
  // The preflight guaranteed sufficient space. Preserve any unexpected remainder.
  ItemStack transfer=output.copy();
  player.getInventory().add(transfer);
  if(!transfer.isEmpty())player.drop(transfer,false);
  broadcastChanges();
  return true;
 }
 /** Server-authoritative terminal-style list clicks. No direct interaction
  * with magnet slot 0 occurs from clicking a blank/listing cell.
  */
 @Override public void clicked(int slotId,int button,ContainerInput type,Player player){
  if(slotId>=4&&slotId<49){
   if(!(player instanceof ServerPlayer server)||storage.filterEditor
       ||!storage.source.valid())return;
   if(type==ContainerInput.QUICK_MOVE){shiftWithdraw(server,slotId);return;}
   if(type!=ContainerInput.PICKUP||(button!=0&&button!=1))return;
   ItemStack carried=getCarried();
   if(!carried.isEmpty()){
    if(carried.getItem() instanceof NetworkBackpackItem
       ||carried.getItem() instanceof StorageCellItem
       ||carried.getItem() instanceof EquipmentCellItem
       ||carried.is(ObsidianNetwork.NETWORK_BACKPACK_MAGNET_UPGRADE.get()))return;
    int amount=button==1?1:carried.getCount();
    ItemStack candidate=storage.source.current().copy();
    var transfer=V176BackpackCells.insert(server.level(),candidate,carried,amount);
    if(transfer.accepted()<=0||!storage.source.save(candidate))return;
    ItemStack rest=carried.copy();
    rest.shrink((int)transfer.accepted());
    setCarried(rest);
    broadcastChanges();
    return;
   }
   var entry=storage.viewed(slotId);
   if(entry==null)return;
   var codec=new dev.obsidiannetwork.platform.MinecraftItemStackCodec(server.level().registryAccess());
   ItemStack output=codec.recreate(entry.descriptor(),1);
   int count=(int)Math.min(entry.count(),button==1?1:output.getMaxStackSize());
   if(count<=0)return;
   output.setCount(count);
   ItemStack candidate=storage.source.current().copy();
   var transfer=V176BackpackCells.extract(server.level(),candidate,entry.descriptor(),count);
   if(transfer.accepted()!=count||!storage.source.save(candidate))return;
   setCarried(output);
   broadcastChanges();
   return;
  }
  // Only actual detached side-slot clicks may touch module 0..3.
  super.clicked(slotId,button,type,player);
 }
""")
# ChestMenu provides virtual preview slots on the client. Clicking any position
# in the list, including empty positions, routes to that exact slot, NOT slot 0.
screen="client/V176BackpackScreen.java"
patch(screen,
'''    if(!menu.getSlot(4+entry).getItem().isEmpty()){
     command("networkbackpack take "+entry+" "+(button==1?1:64));
     return true;
    }''',
'''    var game=net.minecraft.client.Minecraft.getInstance();
    if(game.player!=null&&game.gameMode!=null){
     boolean shifting=net.minecraft.client.gui.screens.Screen.hasShiftDown();
     game.gameMode.handleContainerInput(menu.containerId,4+entry,button,
       shifting?net.minecraft.world.inventory.ContainerInput.QUICK_MOVE:
                net.minecraft.world.inventory.ContainerInput.PICKUP,game.player);
    }
    return true;''')
# Exact capacity of mixed cells in the existing status bar.
patch(screen,'''     if(stack.getItem() instanceof dev.obsidiannetwork.item.StorageCellItem cell){
      xsxMeterUsed+=cell.readStore(stack).used();
      xsxMeterCapacity+=cell.tier().capacity();
     }''',
'''     if(stack.getItem() instanceof dev.obsidiannetwork.item.StorageCellItem cell){
      xsxMeterUsed+=cell.readStore(stack).used();
      xsxMeterCapacity+=cell.tier().capacity();
     }else if(stack.getItem() instanceof dev.obsidiannetwork.item.EquipmentCellItem eq){
      xsxMeterUsed+=eq.readStore(stack).used();
      xsxMeterCapacity+=dev.obsidiannetwork.core.EquipmentCellStore.CAPACITY;
     }''')
# Keep the registered item IDs and recipe data untouched; only change item
# model geometry. 16x16 full cube with the number applied on every side face.
digits={
 "1":["010","110","010","010","111"],
 "2":["111","001","111","100","111"],
 "x":["000","101","010","101","000"],
}
for item,label in (("compressed_cobblestone_1x","1x"),
                   ("compressed_cobblestone_3x","2x"),
                   ("compressed_obsidian_1x","1x")):
    png=A/"textures/item"/(item+"_base.png")
    assert png.is_file(),("B857_MISSING_BASE_TEXTURE",item)
    with Image.open(png) as source:
        im=source.convert("RGBA")
    assert im.size==(32,32),("B857_TEXTURE_SIZE",item)
    draw=ImageDraw.Draw(im)
    draw.rectangle((13,18,31,31),fill=(17,21,26,235),outline=(240,240,240,255),width=1)
    for idx,c in enumerate(label):
        for y,row in enumerate(digits[c]):
            for x,pixel in enumerate(row):
                if pixel=="1":
                    x0=15+idx*8+x*2
                    y0=20+y*2
                    draw.rectangle((x0,y0,x0+1,y0+1),fill=(250,250,250,255))
    im.save(png,optimize=True)
    model=A/"models/item"/(item+".json")
    info=json.loads(model.read_text(encoding="utf-8"))
    assert info["parent"]=="minecraft:item/generated",("B857_MODEL_DRIFT",item)
    model.write_text(json.dumps({
       "parent":"minecraft:block/cube_all",
       "textures":{"all":"obsidiannetwork:item/"+item+"_base"}
     },indent=2)+"\n",encoding="utf-8")

print("B857_STAGED_EQUIPMENT_CELL_GUI_TERMINAL_TRANSACTIONS_3D_ITEMS_PASS_BUILDLOCK")
