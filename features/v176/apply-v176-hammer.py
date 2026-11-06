#!/usr/bin/env python3
"""Generate the Hammer item during the v1.7.6 source reconstruction."""
import os,json
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])
A=R/"assets/obsidiannetwork"
main=J/"ObsidianNetwork.java"
s=main.read_text()
anchor='   public static final DeferredItem<dev.obsidiannetwork.powerarmor.UpgradeCardItem> POWER_CARD_MICRO_MG ='
assert s.count(anchor)==1
s=s.replace(anchor,'''   public static final DeferredItem<dev.obsidiannetwork.hammer.HammerItem> HAMMER =
      ITEMS.registerItem("hammer",p -> new dev.obsidiannetwork.hammer.HammerItem(p.durability(12186)));
'''+anchor,1)
creative='            output.accept((ItemLike)MULTITOOL.get());'
assert s.count(creative)==1
s=s.replace(creative,creative+'\n            output.accept((ItemLike)HAMMER.get());',1)
main.write_text(s)
p=J/"hammer/HammerItem.java";p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(r'''package dev.obsidiannetwork.hammer;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ToolMaterial;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
/** Netherite pick/shovel hammer, mining a view-aligned 3x3 plane. */
public final class HammerItem extends Item {
 private static final ThreadLocal<Boolean> EXTRA=ThreadLocal.withInitial(()->false);
 public HammerItem(Properties properties){
  super(ToolMaterial.NETHERITE.applyToolProperties(properties,BlockTags.MINEABLE_WITH_PICKAXE,8.0F,-3.0F,0.0F));
 }
 private static boolean mineable(BlockState s){
  return s.is(BlockTags.MINEABLE_WITH_PICKAXE)||s.is(BlockTags.MINEABLE_WITH_SHOVEL);
 }
 @Override public float getDestroySpeed(ItemStack stack,BlockState state){
  return mineable(state)?9.0F:super.getDestroySpeed(stack,state);
 }
 @Override public boolean isCorrectToolForDrops(ItemStack stack,BlockState state){
  return mineable(state)||super.isCorrectToolForDrops(stack,state);
 }
 @Override public boolean mineBlock(ItemStack stack,Level level,BlockState state,BlockPos origin,LivingEntity miner){
  boolean result=super.mineBlock(stack,level,state,origin,miner);
  if(level.isClientSide()||EXTRA.get()||!(miner instanceof ServerPlayer player)||player.isCreative()||!mineable(state))return result;
  ServerLevel server=(ServerLevel)level;
  var look=player.getLookAngle();
  double ax=Math.abs(look.x),ay=Math.abs(look.y),az=Math.abs(look.z);
  Direction.Axis axis=ay>=ax&&ay>=az?Direction.Axis.Y:(ax>=az?Direction.Axis.X:Direction.Axis.Z);
  EXTRA.set(true);
  try{
   for(int u=-1;u<=1;u++)for(int v=-1;v<=1;v++){
    if(u==0&&v==0||stack.isEmpty())continue;
    BlockPos at=axis==Direction.Axis.Y?origin.offset(u,0,v):axis==Direction.Axis.X?origin.offset(0,u,v):origin.offset(u,v,0);
    if(!server.hasChunkAt(at))continue;
    BlockState target=server.getBlockState(at);
    if(!mineable(target)||target.getDestroySpeed(server,at)<0||target.getDestroySpeed(server,at)>state.getDestroySpeed(server,origin)*3.0f+5.0f)continue;
    if(!server.mayInteract(player,at)||!player.mayUseItemAt(at,player.getDirection(),stack))continue;
    player.gameMode.destroyBlock(at);
   }
  }finally{EXTRA.set(false);}
  return result;
 }
}
''')
recipe=R/"data/obsidiannetwork/recipe/hammer.json";recipe.parent.mkdir(parents=True,exist_ok=True)
recipe.write_text(json.dumps({"type":"minecraft:crafting_shaped","pattern":["PPP"," N "," N "],"key":{"P":"minecraft:netherite_pickaxe","N":"minecraft:netherite_ingot"},"result":{"id":"obsidiannetwork:hammer","count":1}},indent=2)+"\n")
for lang in ("de_de","en_us"):
 f=A/f"lang/{lang}.json";d=json.loads(f.read_text());d["item.obsidiannetwork.hammer"]="Hammer";f.write_text(json.dumps(d,indent=2,ensure_ascii=False)+"\n")
print("HAMMER_3X3_ITEM_AND_RECIPE_GENERATED")
