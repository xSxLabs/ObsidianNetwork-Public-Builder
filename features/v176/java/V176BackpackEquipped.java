package dev.obsidiannetwork.backpack;

import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.neoforged.fml.ModList;

/** The server always discovers an actual equipped or carried backpack.
 * No remote keypress can supply an arbitrary target item/player/slot.
 */
public final class V176BackpackEquipped {
 private V176BackpackEquipped(){}
 public enum Where { CHEST, CURIOS_BACK, MAIN_HAND, OFF_HAND }
 public record Located(Where where,int index,ItemStack stack) {
  public Located {
   if(!(stack.getItem() instanceof NetworkBackpackItem))
    throw new IllegalArgumentException("not a Backpack");
  }
  public void persist(ServerPlayer player,ItemStack updated){
   if(!(updated.getItem() instanceof NetworkBackpackItem))
    throw new IllegalArgumentException("not a Backpack");
   switch(where){
    case CHEST->{
     if(!(player.getItemBySlot(EquipmentSlot.CHEST).getItem() instanceof NetworkBackpackItem))
      throw new IllegalStateException("chest item changed during operation");
     player.setItemSlot(EquipmentSlot.CHEST,updated);
    }
    case CURIOS_BACK->{
     try{
      Class<?> cls=Class.forName("dev.obsidiannetwork.backpack.V176BackpackCuriosCompat");
      cls.getMethod("save",ServerPlayer.class,int.class,ItemStack.class)
          .invoke(null,player,index,updated);
     }catch(ReflectiveOperationException e){
      throw new IllegalStateException("Curios back write unavailable",e);
     }
    }
    case MAIN_HAND->player.setItemInHand(InteractionHand.MAIN_HAND,updated);
    case OFF_HAND->player.setItemInHand(InteractionHand.OFF_HAND,updated);
   }
  }
 }
 public static Located worn(ServerPlayer player){
  ItemStack chest=player.getItemBySlot(EquipmentSlot.CHEST);
  if(chest.getItem() instanceof NetworkBackpackItem)
   return new Located(Where.CHEST,-1,chest);
  if(ModList.get().isLoaded("curios")){
   try{
    Class<?> cls=Class.forName("dev.obsidiannetwork.backpack.V176BackpackCuriosCompat");
    Object found=cls.getMethod("firstBack",ServerPlayer.class).invoke(null,player);
    if(found!=null){
     ItemStack stack=(ItemStack)found.getClass().getMethod("stack").invoke(found);
     int index=(Integer)found.getClass().getMethod("index").invoke(found);
     if(stack.getItem() instanceof NetworkBackpackItem)
      return new Located(Where.CURIOS_BACK,index,stack);
    }
   }catch(ReflectiveOperationException e){
    throw new IllegalStateException("Curios back lookup unavailable",e);
   }
  }
  return null;
 }
 public static Located active(ServerPlayer player){
  var equipped=worn(player);
  if(equipped!=null)return equipped;
  ItemStack main=player.getItemInHand(InteractionHand.MAIN_HAND);
  if(main.getItem() instanceof NetworkBackpackItem)
   return new Located(Where.MAIN_HAND,-1,main);
  ItemStack off=player.getItemInHand(InteractionHand.OFF_HAND);
  if(off.getItem() instanceof NetworkBackpackItem)
   return new Located(Where.OFF_HAND,-1,off);
  return null;
 }
}
