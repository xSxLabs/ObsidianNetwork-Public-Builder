#!/usr/bin/env python3
"""B1234 magnet repair: default installed upgrade ON; target the enabled bag.

Previously active() returned the first chest/Curios/held bag even if its
magnet was OFF, so a second enabled bag was never considered. A newly
installed Magnet also defaulted OFF without a user toggle. Leave explicit
stored OFF intact; preserve order chest, Curios, main hand, offhand.
No placed-world vacuum and no item/entity change before successful persist.
"""
import os
from pathlib import Path

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def update(rel,old,new):
 p=root/rel
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("B1234_MAGNET_DRIFT",rel,s.count(old),old[:130])
 p.write_text(s.replace(old,new,1),encoding="utf-8")

update("backpack/V176BackpackCells.java",
'''  return !magnet.isEmpty()&&magnetData(magnet).getBooleanOr(MAG_ON,false);''',
'''  // Installed upgrade is ON by default; an explicit OFF is preserved.
  return !magnet.isEmpty()&&magnetData(magnet).getBooleanOr(MAG_ON,true);''')

update("backpack/V176BackpackCuriosCompat.java",
''' public static void save(ServerPlayer player,int index,ItemStack expected,ItemStack bag){''',
''' /** Magnet lookup is independent from the first Curios back slot.
  * Never select a disabled bag when another back slot has an enabled magnet.
  */
 public static Found firstEnabledMagnet(ServerPlayer player){
  var opt=CuriosApi.getCuriosInventory(player);
  if(opt.isEmpty())return null;
  var handler=opt.get().getStacksHandler("back");
  if(handler.isEmpty())return null;
  var slots=handler.get().getStacks();
  for(int i=0;i<slots.getSlots();i++){
   ItemStack candidate=slots.getStackInSlot(i);
   if(candidate.getItem() instanceof NetworkBackpackItem
      &&V176BackpackCells.magnetEnabled(candidate))
    return new Found(i,candidate);
  }
  return null;
 }
 public static void save(ServerPlayer player,int index,ItemStack expected,ItemStack bag){''')

update("backpack/V176BackpackEquipped.java",
''' public static Located active(ServerPlayer player){''',
''' /** Only for magnet pickup; never changes normal GUI/activation order. */
 public static Located activeMagnet(ServerPlayer player){
  ItemStack chest=player.getItemBySlot(EquipmentSlot.CHEST);
  if(chest.getItem() instanceof NetworkBackpackItem
       &&V176BackpackCells.magnetEnabled(chest))
   return new Located(Where.CHEST,-1,chest);
  if(ModList.get().isLoaded("curios")){
   try{
    Class<?> cls=Class.forName("dev.obsidiannetwork.backpack.V176BackpackCuriosCompat");
    Object found=cls.getMethod("firstEnabledMagnet",ServerPlayer.class)
        .invoke(null,player);
    if(found!=null){
     ItemStack stack=(ItemStack)found.getClass().getMethod("stack").invoke(found);
     int index=(Integer)found.getClass().getMethod("index").invoke(found);
     if(stack.getItem() instanceof NetworkBackpackItem
        &&V176BackpackCells.magnetEnabled(stack))
      return new Located(Where.CURIOS_BACK,index,stack);
    }
   }catch(ReflectiveOperationException ignored){
    // Missing/broken optional Curios does not disable hand magnet pickup.
   }
  }
  ItemStack main=player.getItemInHand(InteractionHand.MAIN_HAND);
  if(main.getItem() instanceof NetworkBackpackItem
      &&V176BackpackCells.magnetEnabled(main))
   return new Located(Where.MAIN_HAND,-1,main);
  ItemStack off=player.getItemInHand(InteractionHand.OFF_HAND);
  if(off.getItem() instanceof NetworkBackpackItem
      &&V176BackpackCells.magnetEnabled(off))
   return new Located(Where.OFF_HAND,-1,off);
  return null;
 }
 public static Located active(ServerPlayer player){''')

update("backpack/V176BackpackMagnetEvents.java",
'''  try{location=V176BackpackEquipped.active(player);}''',
'''  try{location=V176BackpackEquipped.activeMagnet(player);}''')

update("backpack/V176BackpackMagnetEvents.java",
'''  if(location==null||!V176BackpackCells.magnetEnabled(location.stack()))return;
  ItemStack original=location.stack();''',
'''  if(location==null||!V176BackpackCells.magnetEnabled(location.stack()))return;
  ItemStack original=location.stack();
  // Empty backpacks with no real Cell capacity never scan world entities.
  if(V176BackpackCells.capacity(original)<=0L)return;''')

result=(root/"backpack/V176BackpackMagnetEvents.java").read_text(encoding="utf-8")
assert "location.persist(player,updated);" in result
assert result.index("location.persist(player,updated);")<result.index("remainder.shrink(")
assert "RANGE=12.0D" in result
assert "V176BackpackEquipped.activeMagnet(player)" in result
print("B1234_MAGNET_DEFAULT_ON_ENABLED_BAG_PICKUP_CURIOS_AND_LOSSLESS_PERSIST_PASS")
