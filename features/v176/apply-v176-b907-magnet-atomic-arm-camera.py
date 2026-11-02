#!/usr/bin/env python3
"""B907: one atomic magnetic pickup per server tick, shared first-person arm pivot.

Runs after B902 on the reconstructed v1.7.6 source. Fail closed on drift.
A failed storage save must never remove entities from the world.
"""
import os
from pathlib import Path

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def change(rel,old,new):
    p=root/rel
    src=p.read_text(encoding="utf-8")
    assert src.count(old)==1,("B907_SOURCE_DRIFT",rel,src.count(old),old[:90])
    p.write_text(src.replace(old,new,1),encoding="utf-8")

mag="backpack/V176BackpackMagnetEvents.java"
p=root/mag
s=p.read_text(encoding="utf-8")
begin=" @SubscribeEvent public static void onPlayerTick(PlayerTickEvent.Post event){"
assert s.count(begin)==1 and s.rstrip().endswith("}\n}"),"B907_MAGNET_METHOD_DRIFT"
s=s[:s.index(begin)]+''' /**
  * Gather ALL eligible item entities this tick, stage their actual quantities
  * in a single copy of the bag and commit the storage once. Ground stacks are
  * shrunk ONLY after the full update has persisted successfully.
  */
 @SubscribeEvent public static void onPlayerTick(PlayerTickEvent.Post event){
  if(!(event.getEntity() instanceof ServerPlayer player)||!player.isAlive())return;
  V176BackpackEquipped.Located location;
  try{location=V176BackpackEquipped.active(player);}
  catch(RuntimeException ignored){return;}
  if(location==null||!V176BackpackCells.magnetEnabled(location.stack()))return;
  ItemStack original=location.stack();
  ItemStack updated=original.copy();
  var targets=player.level().getEntitiesOfClass(
      ItemEntity.class,player.getBoundingBox().inflate(RANGE),
      entity->entity.isAlive()&&!entity.getItem().isEmpty());
  record Collected(ItemEntity entity,int count){}
  var collected=new java.util.ArrayList<Collected>();
  for(ItemEntity entity:targets){
   if(entity.distanceToSqr(player)>RANGE*RANGE)continue;
   ItemStack dropped=entity.getItem();
   if(dropped.isEmpty()
       ||!V176BackpackCells.magnetAccepts(player.level(),updated,dropped))continue;
   try{
    var transfer=V176BackpackCells.insert(
        player.level(),updated,dropped,dropped.getCount());
    if(transfer.accepted()>0)
     collected.add(new Collected(entity,(int)transfer.accepted()));
   }catch(RuntimeException rejected){
    // One malformed/unfit stack does not block other nearby dropped items.
   }
  }
  if(collected.isEmpty())return;
  try{location.persist(player,updated);}
  catch(RuntimeException changed){return;} // Keep ALL ground items.
  // Server tick executes sequentially; nothing else can change the collected
  // entities between the staging pass and this successful storage commit.
  for(Collected item:collected){
   ItemStack remainder=item.entity().getItem().copy();
   remainder.shrink(item.count());
   if(remainder.isEmpty())item.entity().discard();
   else item.entity().setItem(remainder);
  }
 }
}
'''
p.write_text(s,encoding="utf-8")
assert s.count("location.persist(player,updated);")==1
assert s.index("location.persist(player,updated);")<s.index("remainder.shrink")
assert "private static final double RANGE=12.0D;" in s
assert "ITEM_BUDGET" not in s and "ENTITY_BUDGET" not in s

visual="client/V176MicroMgVisualClient.java"
p=root/visual
s=p.read_text(encoding="utf-8")
start=" @SubscribeEvent public static void xsxlabs$firstPersonStraightArm(RenderArmEvent event){"
stop=" @SubscribeEvent public static void worldSuit("
assert s.count(start)==1 and s.count(stop)==1 and s.index(start)<s.index(stop),"B907_ARM_EVENT_DRIFT"
# RenderArmEvent is a separate vanilla arm-only pass, which can be skipped when
# an item is held. It cannot align a barrel submitted from RenderHandEvent.
s=s[:s.index(start)]+s[s.index(stop):]
assert s.count("import net.neoforged.neoforge.client.event.RenderArmEvent;")==1
s=s.replace("import net.neoforged.neoforge.client.event.RenderArmEvent;\n","",1)
old='''  PoseStack pose=event.getPoseStack();
  pose.pushPose();
  // Camera-relative right upper arm. Positive model Y must point forwards.'''
new='''  PoseStack pose=event.getPoseStack();
  // RenderHandEvent precedes the vanilla main-hand draw. Rotate its shared
  // camera-space arm pose so the visible right arm aims forward as one rigid
  // piece. Keep the already aligned barrel on its original view axis by
  // undoing this parent rotation only inside the barrel's submission scope.
  // Deliberately do NOT pop the outer rotation: vanilla arm must receive it.
  pose.translate(0.0F,0.075F,-0.045F);
  pose.mulPose(com.mojang.math.Axis.XP.rotationDegrees(-36.0F));
  pose.pushPose();
  pose.mulPose(com.mojang.math.Axis.XP.rotationDegrees(36.0F));
  // Camera-relative right upper arm. Positive model Y must point forwards.'''
assert s.count(old)==1,("B907_HAND_ANCHOR_DRIFT",s.count(old))
s=s.replace(old,new,1)
p.write_text(s,encoding="utf-8")
assert "RenderHandEvent" in s and "xsxlabs$firstPersonStraightArm" not in s
print("B907_SINGLE_COMMIT_MAGNET_12_BLOCK_ALL_STACKS_SHARED_FIRSTPERSON_ARM_PASS")
