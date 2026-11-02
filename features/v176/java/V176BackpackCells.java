package dev.obsidiannetwork.backpack;

import dev.obsidiannetwork.ObsidianNetwork;
import dev.obsidiannetwork.core.ExactStackDescriptor;
import dev.obsidiannetwork.core.ItemKey;
import dev.obsidiannetwork.core.StorageCellStore;
import dev.obsidiannetwork.item.StorageCellItem;
import dev.obsidiannetwork.platform.MinecraftItemStackCodec;
import net.minecraft.core.NonNullList;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.component.ItemContainerContents;
import net.minecraft.world.level.Level;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 * REAL 26.1 StorageCellItem backing store for all 24 backpack colors.
 *
 * CONTAINER slots: index 0 = craftable Magnet Upgrade;
 *                  index 1,2,3 = existing StorageCellItem (with its own
 *                  native CELL_CONTENTS data component and exact descriptors).
 *
 * No other "backpack inventory" exists. The installed StorageCellItems hold
 * the items and remain individually transferable to/from a normal Drive.
 * All writes prepare detached copies and then atomically replace the bag's
 * immutable CONTAINER component. No writing to other players' inventories.
 */
public final class V176BackpackCells {
 public static final int SLOT_MAGNET=0;
 public static final int SLOT_CELL_FIRST=1;
 public static final int SLOT_CELL_LAST=3;
 public static final int TOTAL_SLOTS=4;
 public static final int FILTER_SLOTS=54;
 private static final String MAG_ON="xsx_v176_magnet_on";
 private static final String MAG_WHITELIST="xsx_v176_magnet_whitelist";
 private V176BackpackCells(){}

 public static NonNullList<ItemStack> slots(ItemStack bag){
  if(!(bag.getItem() instanceof NetworkBackpackItem))
   throw new IllegalArgumentException("expected Network Backpack");
  var list=NonNullList.withSize(TOTAL_SLOTS,ItemStack.EMPTY);
  bag.getOrDefault(DataComponents.CONTAINER,ItemContainerContents.EMPTY).copyInto(list);
  if(!list.get(0).isEmpty()&&!list.get(0).is(ObsidianNetwork.NETWORK_BACKPACK_MAGNET_UPGRADE.get()))
   throw new IllegalStateException("invalid magnet slot contents");
  for(int i=1;i<4;i++)
   if(!list.get(i).isEmpty()&&!(list.get(i).getItem() instanceof StorageCellItem))
    throw new IllegalStateException("invalid Storage Cell slot "+i);
  return list;
 }

 public static void writeSlots(ItemStack bag,List<ItemStack> entries){
  if(entries.size()!=TOTAL_SLOTS)throw new IllegalArgumentException("exactly four slots");
  if(!(bag.getItem() instanceof NetworkBackpackItem))
   throw new IllegalArgumentException("not a Network Backpack");
  for(int i=0;i<TOTAL_SLOTS;i++){
   ItemStack stack=entries.get(i);
   if(stack==null||stack.getCount()>1)throw new IllegalArgumentException("invalid slot stack");
   if(i==0&&!stack.isEmpty()&&!stack.is(ObsidianNetwork.NETWORK_BACKPACK_MAGNET_UPGRADE.get()))
    throw new IllegalArgumentException("invalid magnet");
   if(i>=1&&!stack.isEmpty()&&!(stack.getItem() instanceof StorageCellItem))
    throw new IllegalArgumentException("invalid Storage Cell");
  }
  bag.set(DataComponents.CONTAINER,ItemContainerContents.fromItems(entries));
 }

 public static long capacity(ItemStack bag){
  long total=0L;
  var entries=slots(bag);
  for(int i=1;i<4;i++)
   if(entries.get(i).getItem() instanceof StorageCellItem cell)
    total=Math.addExact(total,cell.tier().capacity());
  return total;
 }

 public static long used(ItemStack bag){
  long total=0L;
  var entries=slots(bag);
  for(int i=1;i<4;i++)
   if(entries.get(i).getItem() instanceof StorageCellItem cell)
    total=Math.addExact(total,cell.readStore(entries.get(i)).used());
  return total;
 }

 public static boolean putUpgrade(ItemStack bag,int slot,ItemStack toInstall){
  var old=slots(bag);
  if(slot<0||slot>=TOTAL_SLOTS)throw new IndexOutOfBoundsException(slot);
  if(!old.get(slot).isEmpty()||toInstall.isEmpty()||toInstall.getCount()!=1)return false;
  var next=new ArrayList<>(old);
  next.set(slot,toInstall.copy());
  try {writeSlots(bag,next);return true;}
  catch(IllegalArgumentException invalid){return false;}
 }

 /** Extracting a filled cell returns that original cell ItemStack and all its
  * CELL_CONTENTS; remaining cells retain their own independent capacities.
  */
 public static ItemStack takeUpgrade(ItemStack bag,int slot){
  var old=slots(bag);
  if(slot<0||slot>=TOTAL_SLOTS)throw new IndexOutOfBoundsException(slot);
  ItemStack taken=old.get(slot);
  if(taken.isEmpty())return ItemStack.EMPTY;
  var next=new ArrayList<>(old);
  next.set(slot,ItemStack.EMPTY);
  writeSlots(bag,next);
  return taken.copy();
 }

 public record Transfer(long accepted,long remainder){}
 public record Entry(ExactStackDescriptor descriptor,long count) {
  public Entry {
   Objects.requireNonNull(descriptor);
   if(count<=0)throw new IllegalArgumentException("entry count");
  }
 }
 public static Transfer insert(Level world,ItemStack bag,ItemStack incoming,long requested){
  if(requested<0)throw new IllegalArgumentException("negative insertion");
  if(requested==0||incoming.isEmpty()||incoming.getItem() instanceof NetworkBackpackItem)
   return new Transfer(0,requested);
  MinecraftItemStackCodec codec=new MinecraftItemStackCodec(world.registryAccess());
  ExactStackDescriptor d=codec.describe(incoming);
  var items=slots(bag);
  var replacements=new ArrayList<>(items);
  long left=requested;
  // Prefer cells already holding the item key; then empty cell-space.
  for(int phase=0;phase<2&&left>0;phase++){
   for(int i=1;i<=3&&left>0;i++){
    ItemStack cellStack=replacements.get(i);
    if(!(cellStack.getItem() instanceof StorageCellItem cell))continue;
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
  if(left<requested)writeSlots(bag,replacements);
  return new Transfer(requested-left,left);
 }

 public static List<Entry> entries(ItemStack bag){
  Map<ItemKey,Entry> data=new HashMap<>();
  var items=slots(bag);
  for(int i=1;i<=3;i++){
   ItemStack stack=items.get(i);
   if(!(stack.getItem() instanceof StorageCellItem cell))continue;
   var store=cell.readStore(stack);
   for(var entry:store.snapshot().entrySet()){
    byte[] exact=store.descriptor(entry.getKey());
    if(exact==null||entry.getValue()<=0)continue;
    var desc=new ExactStackDescriptor(entry.getKey().itemId(),exact);
    var previous=data.get(entry.getKey());
    data.put(entry.getKey(),new Entry(desc,
      Math.addExact(entry.getValue(),previous==null?0L:previous.count())));
   }
  }
  return List.copyOf(data.values());
 }

 public static long count(ItemStack bag,ItemKey key){
  long count=0;
  for(int i=1;i<=3;i++){
   ItemStack cellStack=slots(bag).get(i);
   if(cellStack.getItem() instanceof StorageCellItem cell)
    count=Math.addExact(count,cell.readStore(cellStack).amount(key));
  }
  return count;
 }

 public static Transfer extract(Level world,ItemStack bag,ExactStackDescriptor d,long wanted){
  if(wanted<0)throw new IllegalArgumentException("negative extraction");
  if(wanted==0)return new Transfer(0,0);
  var items=slots(bag);
  var next=new ArrayList<>(items);
  long left=wanted;
  for(int i=1;i<=3&&left>0;i++){
   ItemStack cellStack=next.get(i);
   if(!(cellStack.getItem() instanceof StorageCellItem cell))continue;
   var store=cell.readStore(cellStack);
   byte[] contents=store.descriptor(d.key());
   if(contents==null||!java.util.Arrays.equals(contents,d.canonicalPayload()))continue;
   long n=store.extract(d.key(),left);
   if(n==0)continue;
   ItemStack updated=cellStack.copy();
   cell.writeStore(updated,store);
   next.set(i,updated);
   left-=n;
  }
  if(left<wanted)writeSlots(bag,next);
  return new Transfer(wanted-left,left);
 }

 public static ItemStack magnet(ItemStack bag){return slots(bag).get(SLOT_MAGNET);}
 private static CompoundTag magnetData(ItemStack magnet){
  return magnet.getOrDefault(DataComponents.CUSTOM_DATA,CustomData.EMPTY).copyTag();
 }
 public static boolean magnetEnabled(ItemStack bag){
  ItemStack magnet=magnet(bag);
  return !magnet.isEmpty()&&magnetData(magnet).getBooleanOr(MAG_ON,false);
 }
 public static boolean magnetWhitelist(ItemStack bag){
  ItemStack magnet=magnet(bag);
  return !magnet.isEmpty()&&magnetData(magnet).getBooleanOr(MAG_WHITELIST,false);
 }
 public static void magnetSettings(ItemStack bag,boolean enabled,boolean whitelist){
  var items=slots(bag);
  if(items.get(0).isEmpty())throw new IllegalStateException("magnet module absent");
  ItemStack upgrade=items.get(0).copy();
  var tag=magnetData(upgrade);
  tag.putBoolean(MAG_ON,enabled);
  tag.putBoolean(MAG_WHITELIST,whitelist);
  upgrade.set(DataComponents.CUSTOM_DATA,CustomData.of(tag));
  items.set(0,upgrade);
  writeSlots(bag,items);
 }
 public static boolean magnetAccepts(Level world,ItemStack bag,ItemStack incoming){
  if(!magnetEnabled(bag)||incoming.isEmpty())return false;
  ItemStack upgrade=magnet(bag);
  var templates=upgrade.getOrDefault(DataComponents.CONTAINER,ItemContainerContents.EMPTY);
  MinecraftItemStackCodec codec=new MinecraftItemStackCodec(world.registryAccess());
  ItemKey k=codec.describe(incoming).key();
  boolean listed=false;
  for(int i=0;i<FILTER_SLOTS;i++){
   ItemStack sample=templates.getStackInSlot(i);
   if(!sample.isEmpty()&&codec.describe(sample).key().equals(k)){listed=true;break;}
  }
  return magnetWhitelist(bag)?listed:!listed;
 }
 public static boolean setMagnetFilter(ItemStack bag,int filterSlot,ItemStack sample){
  if(filterSlot<0||filterSlot>=FILTER_SLOTS)return false;
  var items=slots(bag);
  if(items.get(0).isEmpty())return false;
  ItemStack upgrade=items.get(0).copy();
  var filters=NonNullList.withSize(FILTER_SLOTS,ItemStack.EMPTY);
  upgrade.getOrDefault(DataComponents.CONTAINER,ItemContainerContents.EMPTY).copyInto(filters);
  ItemStack ghost=sample.copy();
  if(!ghost.isEmpty())ghost.setCount(1);
  filters.set(filterSlot,ghost);
  upgrade.set(DataComponents.CONTAINER,ItemContainerContents.fromItems(filters));
  items.set(0,upgrade);
  writeSlots(bag,items);
  return true;
 }
}
