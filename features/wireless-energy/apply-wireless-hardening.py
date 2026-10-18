#!/usr/bin/env python3
"""Bound wireless FE dispatch and protect antenna configuration, fail-closed.

Runs after the original wireless runtime and menu patches. Do not add a third
device or alter transaction semantics; real FE/GameTests remain the authority.
"""
import os
from pathlib import Path

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def change(path, before, after):
    target=root/path
    source=target.read_text()
    assert source.count(before)==1, f"{path}: expected exactly one anchor {before[:95]!r}, found {source.count(before)}"
    target.write_text(source.replace(before,after,1))

entity="blockentity/WirelessNetworkBlockEntity.java"
change(entity,
    " private long stored;\n private String networkId=WirelessNetworkData.DEFAULT_ID;",
    " private long stored;\n private String ownerId=\"\";\n private String networkId=WirelessNetworkData.DEFAULT_ID;")
change(entity,
    " public String networkId(){return networkId;}",
    """ public String networkId(){return networkId;}
 /** New placements are owned by the placer. Older, unowned antennas are claimed on first GUI use. */
 public void markPlacedBy(net.minecraft.server.level.ServerPlayer player){
  if(ownerId.isEmpty()){ownerId=player.getUUID().toString();setChanged();}
 }
 public boolean canConfigure(net.minecraft.server.level.ServerPlayer player){
  if(!(level instanceof ServerLevel)||player==null)return false;
  if(ownerId.isEmpty())markPlacedBy(player);
  return ownerId.equals(player.getUUID().toString());
 }
 public boolean selectNetworkFor(net.minecraft.server.level.ServerPlayer player,String id){
  if(!canConfigure(player)||!WirelessNetworkData.get(player.level().getServer()).canAccess(player,id))return false;
  selectNetwork(id);
  return networkId.equals(id);
 }""")
change(entity,
    '  out.putString("network_id",networkId);',
    '  out.putString("network_id",networkId);\n  out.putString("wireless_owner",ownerId);')
change(entity,
    '  networkId=in.getStringOr("network_id",WirelessNetworkData.DEFAULT_ID);',
    '  networkId=in.getStringOr("network_id",WirelessNetworkData.DEFAULT_ID);\n  ownerId=in.getStringOr("wireless_owner","");\n  if(ownerId.length()>64)ownerId="";')
change(entity,
    "  // Push to neighboring FE machines without scanning other chunks or the network graph.\n  for(Direction side:DIRECTIONS){",
    "  // Total receiver budget across all faces, not 16k FE per side.\n  int remainingBudget=MAX_TRANSFER;\n  for(Direction side:DIRECTIONS){\n   if(remainingBudget<=0)break;")
change(entity,
    "   int offer=(int)Math.min(MAX_TRANSFER,WirelessEnergyRuntime.available(server.getServer(),be.networkId));",
    "   int offer=(int)Math.min(remainingBudget,WirelessEnergyRuntime.available(server.getServer(),be.networkId));")
change(entity,
    "     if(accepted==withdrawn)tx.commit();",
    "     if(accepted==withdrawn){tx.commit();remainingBudget-=accepted;}")

block="block/WirelessNetworkBlock.java"
change(block,
    " @Override protected InteractionResult useWithoutItem(",
    """ @Override public void setPlacedBy(Level level,BlockPos pos,BlockState state,
  net.minecraft.world.entity.LivingEntity placer,net.minecraft.world.item.ItemStack stack){
  super.setPlacedBy(level,pos,state,placer,stack);
  if(!level.isClientSide()&&placer instanceof ServerPlayer sp
      &&level.getBlockEntity(pos) instanceof WirelessNetworkBlockEntity be)be.markPlacedBy(sp);
 }
 @Override protected InteractionResult useWithoutItem(""")
change(block,
    "  if(level.isClientSide())return InteractionResult.SUCCESS;\n  player.openMenu(",
    """  if(level.isClientSide())return InteractionResult.SUCCESS;
  if(!(player instanceof ServerPlayer sp)||!device.canConfigure(sp)){
   player.sendSystemMessage(Component.literal("Only the antenna owner can configure this device"));
   return InteractionResult.FAIL;
  }
  player.openMenu(""")

menu="menu/WirelessNetworkMenu.java"
change(menu,
    "  if(!(player instanceof ServerPlayer p)||device==null||!stillValid(player))return false;",
    "  if(!(player instanceof ServerPlayer p)||device==null||!stillValid(player)||!device.canConfigure(p))return false;")
change(menu,
    "   device.selectNetwork(list.get(index%list.size()).id());return true;",
    "   return device.selectNetworkFor(p,list.get(index%list.size()).id());")
change(menu,
    "   device.selectNetwork(created.id());return true;",
    "   return device.selectNetworkFor(p,created.id());")

runtime="wireless/WirelessEnergyRuntime.java"
change(runtime,
    " private static final ThreadLocal<Boolean> IN_TRANSFER=ThreadLocal.withInitial(()->false);",
    """ private static final ThreadLocal<Boolean> IN_TRANSFER=ThreadLocal.withInitial(()->false);
 // Separate per-server cursors keep many transmitters from starving behind the first.
 private static final Map<MinecraftServer,Map<String,Integer>> NEXT_SENDER=new WeakHashMap<>();""")
change(runtime,
    """   int remaining=wanted;
   // Non-chunk-loading indexed visits; orphaned and unloaded transmitters are skipped.
   for(var ref:group){
    var be=ref.get();
    if(be==null||!be.isActive()||!id.equals(be.networkId()))continue;
    remaining-=be.withdraw(remaining,tx);
    if(remaining<=0)break;
   }
   return wanted-remaining;""",
    """   int remaining=wanted;
   // Fixed-size indexed walk; never loads a chunk, and rotates the starting sender.
   int size=group.size();
   if(size==0)return 0;
   var cursors=NEXT_SENDER.computeIfAbsent(server,s->new HashMap<>());
   int start=Math.floorMod(cursors.getOrDefault(id,0),size);
   for(int offset=0;offset<size&&remaining>0;offset++){
    var be=group.get((start+offset)%size).get();
    if(be==null||!be.isActive()||!id.equals(be.networkId()))continue;
    remaining-=be.withdraw(remaining,tx);
   }
   cursors.put(id,(start+1)%size);
   return wanted-remaining;""")
print("WIRELESS_OWNER_BUDGET_ROUNDROBIN_V1 PASS")
