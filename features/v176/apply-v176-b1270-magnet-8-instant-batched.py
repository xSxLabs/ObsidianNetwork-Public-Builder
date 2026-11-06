#!/usr/bin/env python3
"""B1270: real 8-block instantaneous magnet pickup with lossless batching.

Keep the previous chest/Curios/hand enabled-Backpack selection, default ON,
whitelist/blacklist and the original storage-cell admission rules.
Process every tick. Group identical ItemResources before each native Cell
insert; the world entities change ONLY AFTER a single authoritative
equipped/held Backpack persist succeeds. No ITEM_BUDGET / ENTITY_BUDGET.
Every item within the EUCLIDEAN 8-block sphere is considered, not just AABB.

This patch runs after B1234/B1248, B1269 and B907. The 1269 runtime cache is
for *placed cable ingress only*; this magnet uses the original public insert()
for detached batch candidates and therefore cannot corrupt that cache.
"""
import os
from pathlib import Path

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
magnet=root/"backpack/V176BackpackMagnetEvents.java"
screen=root/"client/V176BackpackScreen.java"
java=magnet.read_text(encoding="utf-8")
ui=screen.read_text(encoding="utf-8")

def exactly_once(src,old,new,label):
 count=src.count(old)
 assert count==1,("B1270_MAGNET_SOURCE_DRIFT",label,count)
 return src.replace(old,new,1)

java=exactly_once(java,
''' private static final double RANGE=12.0D;''',
''' private static final double RANGE=8.0D;''',
"real 8 block range")

# B907 owns the SINGLE-commit implementation. B1234 later selects
# activeMagnet and validates capacity before scanning; keep both safety gates.
start=" @SubscribeEvent public static void onPlayerTick(PlayerTickEvent.Post event){"
assert java.count(start)==1,("B1270_MAGNET_TICK_METHOD_DRIFT",java.count(start))
assert java.rstrip().endswith("}\n}"),"B1270_MAGNET_CLASS_TAIL_DRIFT"
original=java[java.index(start):]
for required in (
 "V176BackpackEquipped.activeMagnet(player)",
 "V176BackpackCells.capacity(original)<=0L",
 "location.persist(player,updated);",
 "remainder.shrink(item.count())",
 "V176BackpackCells.magnetAccepts(",
 "player.level().getEntitiesOfClass(",
 "entity.distanceToSqr(player)>RANGE*RANGE"):
 assert required in original,("B1270_MAGNET_ORIGINAL_SAFETY_DRIFT",required)
assert "player.tickCount%" not in original
assert "ITEM_BUDGET" not in java and "ENTITY_BUDGET" not in java

replacement=''' /** Exact Resource grouping keeps the original full-speed, every-tick magnet
  * but writes the native Cell data once per unique item+components, instead of
  * once per nearby dropped entity. Nothing is taken before save succeeds.
  */
 private static final class XsxMagnetGroup {
  final ItemStack sample;
  long requested=0L;
  long accepted=0L;
  final java.util.ArrayList<ItemEntity> entities=new java.util.ArrayList<>();
  XsxMagnetGroup(ItemStack example){sample=example.copy();}
 }
 private record XsxMagnetPickup(ItemEntity entity,int amount){}

 @SubscribeEvent public static void onPlayerTick(PlayerTickEvent.Post event){
  // No artificial 5-tick pause: all already-dropped items can be picked up
  // on the very next SERVER tick, subject only to filters/cell capacity.
  if(!(event.getEntity() instanceof ServerPlayer player)||!player.isAlive())return;
  V176BackpackEquipped.Located location;
  try{location=V176BackpackEquipped.activeMagnet(player);}
  catch(RuntimeException noMagnet){return;}
  if(location==null)return;
  ItemStack original=location.stack();
  if(!V176BackpackCells.magnetEnabled(original)
      ||V176BackpackCells.capacity(original)<=0L)return;

  // AABB is only the cheap initial spatial search. The squared-distance
  // check enforces a true 8-block spherical radius (not an inflated cube).
  var targets=player.level().getEntitiesOfClass(
       ItemEntity.class,player.getBoundingBox().inflate(RANGE),
       entity->entity.isAlive()&&!entity.getItem().isEmpty());
  if(targets.isEmpty())return;
  var groups=new java.util.LinkedHashMap<
       net.neoforged.neoforge.transfer.item.ItemResource,XsxMagnetGroup>();
  for(ItemEntity entity:targets){
   if(entity.distanceToSqr(player)>RANGE*RANGE)continue;
   ItemStack dropped=entity.getItem();
   if(dropped.isEmpty())continue;
   // One exact grouping key per entity, but ONE filter check and expensive
   // Storage Cell write per distinct item type/components in the batch.
   var resource=net.neoforged.neoforge.transfer.item.ItemResource.of(dropped);
   if(resource.isEmpty())continue;
   XsxMagnetGroup group=groups.get(resource);
   if(group==null){
    group=new XsxMagnetGroup(dropped);
    groups.put(resource,group);
   }
   group.requested=Math.addExact(group.requested,(long)dropped.getCount());
   group.entities.add(entity);
  }
  if(groups.isEmpty())return;

  ItemStack updated=original.copy();
  for(XsxMagnetGroup group:groups.values()){
   if(!V176BackpackCells.magnetAccepts(player.level(),updated,group.sample))
    continue;
   try{
    // Failure of a single descriptor never poisons an already prepared
    // batch. The native Cell logic preserves Equipment Cell eligibility.
    ItemStack candidate=updated.copy();
    var transfer=V176BackpackCells.insert(
        player.level(),candidate,group.sample,group.requested);
    if(transfer.accepted()<=0)continue;
    group.accepted=transfer.accepted();
    updated=candidate;
   }catch(RuntimeException rejected){
    group.accepted=0L; // leave that group's ground entities unchanged
   }
  }

  var pickups=new java.util.ArrayList<XsxMagnetPickup>();
  for(XsxMagnetGroup group:groups.values()){
   long left=group.accepted;
   for(ItemEntity entity:group.entities){
    if(left<=0L)break;
    int take=(int)Math.min(left,(long)entity.getItem().getCount());
    if(take<=0)continue;
    pickups.add(new XsxMagnetPickup(entity,take));
    left-=take;
   }
   assert left==0L: "B1270_MAGNET_ACCEPTED_QUANTITY_UNACCOUNTED";
  }
  if(pickups.isEmpty())return;
  try{location.persist(player,updated);}
  catch(RuntimeException refused){return;} // ALL drops remain in the world.

  // Persist is complete. Only now move the exact accepted quantities out
  // of world entities; overflow keeps its original ItemStack components.
  for(XsxMagnetPickup pickup:pickups){
   ItemEntity entity=pickup.entity();
   ItemStack remainder=entity.getItem().copy();
   remainder.shrink(pickup.amount());
   if(remainder.isEmpty())entity.discard();
   else entity.setItem(remainder);
  }
 }
}
'''
java=java[:java.index(start)]+replacement
assert java.count("location.persist(player,updated);")==1
assert java.index("location.persist(player,updated);")<java.index("remainder.shrink(pickup.amount());")
assert "V176BackpackEquipped.activeMagnet(player)" in java
assert "private static final double RANGE=8.0D;" in java
assert "player.tickCount%" not in java
assert "ITEM_BUDGET" not in java and "ENTITY_BUDGET" not in java

# B817 GUI historically defaulted the button's state to OFF while B1234
# changed the actual installed upgrade to ON by default. Use the same value.
ui=exactly_once(ui,
'''tag.getBooleanOr("xsx_v176_magnet_on",false)''',
'''tag.getBooleanOr("xsx_v176_magnet_on",true)''',
"magnet ON default button")

assert "tag.getBooleanOr(\"xsx_v176_magnet_on\",true)" in ui
assert "networkbackpack magnet off" in ui and "networkbackpack magnet on" in ui
# Preflight both sources completely before writing either.
magnet.write_text(java,encoding="utf-8")
screen.write_text(ui,encoding="utf-8")
print("B1270_MAGNET_8_BLOCK_EVERY_TICK_EXACT_BATCH_SINGLE_COMMIT_GUI_ON_PASS")
