package dev.obsidiannetwork.backpack;

import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import top.theillusivec4.curios.api.CuriosApi;

/** Loaded ONLY when optional Curios is installed. Do not reference from
 * unguarded client or server class initializers on Curios-absent servers.
 */
public final class V176BackpackCuriosCompat {
 private V176BackpackCuriosCompat(){}
 public record Found(int index,ItemStack stack) {}
 public static Found firstBack(ServerPlayer player){
  var opt=CuriosApi.getCuriosInventory(player);
  if(opt.isEmpty())return null;
  var handler=opt.get().getStacksHandler("back");
  if(handler.isEmpty())return null;
  var slots=handler.get().getStacks();
  for(int i=0;i<slots.getSlots();i++){
   ItemStack candidate=slots.getStackInSlot(i);
   if(candidate.getItem() instanceof NetworkBackpackItem)
    return new Found(i,candidate);
  }
  return null;
 }
 public static void save(ServerPlayer player,int index,ItemStack bag){
  if(!(bag.getItem() instanceof NetworkBackpackItem))
   throw new IllegalArgumentException("not a Network Backpack");
  var opt=CuriosApi.getCuriosInventory(player);
  if(opt.isEmpty())throw new IllegalStateException("Curios not present");
  var handler=opt.get().getStacksHandler("back");
  if(handler.isEmpty()||index<0||index>=handler.get().getStacks().getSlots())
   throw new IllegalStateException("Curios back slot unavailable");
  if(!(handler.get().getStacks().getStackInSlot(index).getItem() instanceof NetworkBackpackItem))
   throw new IllegalStateException("back slot moved");
  opt.get().setEquippedCurio("back",index,bag.copy());
 }
}
