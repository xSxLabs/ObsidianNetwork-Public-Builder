package dev.obsidiannetwork.backpack;

import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.item.ItemStack;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;

/**
 * The magnet upgrades a real carried/worn backpack (never a hidden global bag).
 * Drops are changed only AFTER the modified, real Storage Cell items are
 * successfully written back to the source equipment/Curios/hand slot.
 */
@EventBusSubscriber(modid="obsidiannetwork")
public final class V176BackpackMagnetEvents {
 private V176BackpackMagnetEvents(){}
 private static final int ITEM_BUDGET=128;
 private static final int ENTITY_BUDGET=16;
 private static final double RANGE=6.0D;
 @SubscribeEvent public static void onPlayerTick(PlayerTickEvent.Post event){
  if(!(event.getEntity() instanceof ServerPlayer player)
       ||player.tickCount%5!=0||!player.isAlive())return;
  V176BackpackEquipped.Located location;
  try{location=V176BackpackEquipped.active(player);}
  catch(RuntimeException ignored){return;}
  if(location==null)return;
  ItemStack backpack=location.stack();
  if(!V176BackpackCells.magnetEnabled(backpack))return;
  var targets=player.level().getEntitiesOfClass(
      ItemEntity.class,new AABB(player.blockPosition()).inflate(RANGE),
      e->e.isAlive()&&!e.getItem().isEmpty());
  int entities=0,items=0;
  for(ItemEntity entity:targets){
   if(++entities>ENTITY_BUDGET||items>=ITEM_BUDGET)break;
   if(entity.hasPickUpDelay())continue;
   ItemStack dropped=entity.getItem();
   if(dropped.isEmpty()||!V176BackpackCells.magnetAccepts(player.level(),backpack,dropped))
    continue;
   int tryItems=Math.min(ITEM_BUDGET-items,dropped.getCount());
   if(tryItems<=0)continue;
   ItemStack updated=backpack.copy();
   V176BackpackCells.Transfer result;
   try{
    result=V176BackpackCells.insert(player.level(),updated,dropped,tryItems);
    if(result.accepted()<=0)continue;
    location.persist(player,updated);
   }catch(RuntimeException blocked){continue;}
   int accepted=(int)result.accepted();
   ItemStack remainder=dropped.copy();
   remainder.shrink(accepted);
   if(remainder.isEmpty())entity.discard();
   else entity.setItem(remainder);
   items+=accepted;
   // Each persist replaces the owned stack. Reacquire it before the next
   // nearby entity so a stale bag snapshot is never written back.
   try{location=V176BackpackEquipped.active(player);}
   catch(RuntimeException changed){break;}
   if(location==null||!V176BackpackCells.magnetEnabled(location.stack()))break;
   backpack=location.stack();
  }
 }
}
