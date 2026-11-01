#!/usr/bin/env python3
"""Placeable 24-variant Backpack world blocks and exact item roundtrip.

Server copies the real ItemStack into the world BE after vanilla placement,
and returns that same stack on sneaking pickup or block destruction.
This step does not implement the final terminal-style screen/cable capability.
"""
import os,json
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])
def edit(rel,old,new,expected=1):
 p=J/rel
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==expected,("V176_BPK_PLACE_SOURCE_DRIFT",rel,s.count(old),expected)
 p.write_text(s.replace(old,new,expected),encoding="utf-8")
def add(rel,code):
 p=J/rel;p.parent.mkdir(parents=True,exist_ok=True)
 assert not p.exists(),str(p)
 p.write_text(code,encoding="utf-8")

source=J/"ObsidianNetwork.java"
s=source.read_text(encoding="utf-8")
anchor="   public static final DeferredItem<dev.obsidiannetwork.backpack.NetworkBackpackItem> NETWORK_BACKPACK_MK1 ="
assert s.count(anchor)==1
blocks=[]
for tier in range(1,25):
 key=f"NETWORK_BACKPACK_MK{tier}_BLOCK"
 blocks += [
  f"   public static final DeferredBlock<dev.obsidiannetwork.backpack.NetworkBackpackBlock> {key} =",
  f'      BLOCKS.registerBlock("network_backpack_mk{tier}",p -> new dev.obsidiannetwork.backpack.NetworkBackpackBlock(p,{tier}),',
  "         p -> p.mapColor(MapColor.METAL).strength(2.0F,6.0F).noOcclusion());"
 ]
 s=s.replace(f'ITEMS.registerItem("network_backpack_mk{tier}",p -> new dev.obsidiannetwork.backpack.NetworkBackpackItem(',
             f'ITEMS.registerItem("network_backpack_mk{tier}",p -> new dev.obsidiannetwork.backpack.NetworkBackpackItem({key}.get(),',1)
assert s.count(anchor)==1
s=s.replace(anchor,"\n".join(blocks)+"\n"+anchor,1)
source.write_text(s,encoding="utf-8")
registry=J/"registry/ModBlockEntities.java"
src=registry.read_text(encoding="utf-8")
anchor="   // V174_REACTOR_CONTROLLER_BE: only the controller owns runtime fuel/FE."
assert src.count(anchor)==1
blockrefs=",\n".join(f"         (Block)ObsidianNetwork.NETWORK_BACKPACK_MK{i}_BLOCK.get()" for i in range(1,25))
src=src.replace(anchor,'''   public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<dev.obsidiannetwork.backpack.NetworkBackpackBlockEntity>> NETWORK_BACKPACK =
       TYPES.register("network_backpack",()->new BlockEntityType(
        dev.obsidiannetwork.backpack.NetworkBackpackBlockEntity::new,
        new Block[]{'''+blockrefs+'''}));
'''+anchor,1)
registry.write_text(src,encoding="utf-8")

item=J/"backpack/NetworkBackpackItem.java"
assert item.exists()
item.write_text('''package dev.obsidiannetwork.backpack;

import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.InteractionResult;

/** Real placeable BlockItem, also valid in vanilla chest/Curios back slot. */
public final class NetworkBackpackItem extends BlockItem {
 private final int visualTier;
 public NetworkBackpackItem(Block block,Properties properties,int visualTier){
  super(block,properties);
  if(visualTier<1||visualTier>24)throw new IllegalArgumentException("color tier");
  this.visualTier=visualTier;
 }
 public int visualTier(){return visualTier;}
 @Override public InteractionResult useOn(UseOnContext context){
  // Sneak placement only; otherwise route to the hand-open menu later.
  if(context.getPlayer()!=null&&!context.getPlayer().isShiftKeyDown())
   return InteractionResult.PASS;
  return super.useOn(context);
 }
 @Override public InteractionResult place(BlockPlaceContext context){
  ItemStack original=context.getItemInHand().copy();
  original.setCount(1);
  InteractionResult result=super.place(context);
  if(result.consumesAction()&&!context.getLevel().isClientSide()){
   if(context.getLevel().getBlockEntity(context.getClickedPos())
       instanceof NetworkBackpackBlockEntity worldBag)
    worldBag.setBackpack(original);
  }
  return result;
 }
}
''',encoding="utf-8")

add("backpack/NetworkBackpackBlock.java",'''package dev.obsidiannetwork.backpack;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.DirectionProperty;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.phys.BlockHitResult;
import org.jetbrains.annotations.Nullable;

public final class NetworkBackpackBlock extends BaseEntityBlock {
 public static final DirectionProperty FACING=BlockStateProperties.HORIZONTAL_FACING;
 private final int color;
 private final MapCodec<NetworkBackpackBlock> codec;
 public NetworkBackpackBlock(Properties props,int color){
  super(props);
  this.color=color;
  this.codec=simpleCodec(p->new NetworkBackpackBlock(p,color));
  registerDefaultState(stateDefinition.any().setValue(FACING,Direction.NORTH));
 }
 @Override protected void createBlockStateDefinition(StateDefinition.Builder<net.minecraft.world.level.block.Block,BlockState> b){
  b.add(FACING);
 }
 @Override protected MapCodec<? extends BaseEntityBlock> codec(){return codec;}
 @Override public RenderShape getRenderShape(BlockState s){return RenderShape.MODEL;}
 @Nullable @Override public BlockState getStateForPlacement(BlockPlaceContext c){
  return defaultBlockState().setValue(FACING,c.getHorizontalDirection().getOpposite());
 }
 @Nullable @Override public BlockEntity newBlockEntity(BlockPos p,BlockState s){
  return new NetworkBackpackBlockEntity(p,s);
 }
 private InteractionResult interact(Level world,BlockPos pos,Player player){
  if(!(player instanceof ServerPlayer server))return InteractionResult.SUCCESS;
  if(!(world.getBlockEntity(pos) instanceof NetworkBackpackBlockEntity bag))return InteractionResult.PASS;
  if(player.isShiftKeyDown()){
   ItemStack original=bag.takeBackpack();
   if(original.isEmpty())return InteractionResult.FAIL;
   if(!server.getInventory().add(original))
    net.minecraft.world.Containers.dropItemStack(world,server.getX(),server.getY(),server.getZ(),original);
   world.removeBlock(pos,false);
   return InteractionResult.SUCCESS;
  }
  // Terminal-style GUI open will be connected after menu registration.
  return InteractionResult.SUCCESS;
 }
 @Override protected InteractionResult useWithoutItem(BlockState s,Level w,BlockPos p,Player u,BlockHitResult hit){
  return interact(w,p,u);
 }
 @Override protected InteractionResult useItemOn(ItemStack item,BlockState state,Level w,BlockPos p,Player u,InteractionHand hand,BlockHitResult hit){
  return hand==InteractionHand.MAIN_HAND?interact(w,p,u):InteractionResult.PASS;
 }
}
''')

add("backpack/NetworkBackpackBlockEntity.java",'''package dev.obsidiannetwork.backpack;

import dev.obsidiannetwork.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.Containers;

/** A placed bag owns exactly ONE original ItemStack. World and inventory
 * never concurrently own the same item. Pick-up clears BEFORE block removal.
 */
public final class NetworkBackpackBlockEntity extends BlockEntity {
 private ItemStack backpack=ItemStack.EMPTY;
 public NetworkBackpackBlockEntity(BlockPos p,BlockState s){
  super(ModBlockEntities.NETWORK_BACKPACK.get(),p,s);
 }
 public void setBackpack(ItemStack item){
  if(!(item.getItem() instanceof NetworkBackpackItem)||!backpack.isEmpty())
   throw new IllegalArgumentException("already populated or not backpack");
  backpack=item.copy();
  backpack.setCount(1);
  setChanged();
 }
 public ItemStack getBackpack(){return backpack;}
 public ItemStack takeBackpack(){
  ItemStack original=backpack;
  backpack=ItemStack.EMPTY;
  setChanged();
  return original;
 }
 @Override protected void saveAdditional(ValueOutput out){
  super.saveAdditional(out);
  if(!backpack.isEmpty())out.store("storedBackpack",ItemStack.CODEC,backpack);
 }
 @Override protected void loadAdditional(ValueInput in){
  super.loadAdditional(in);
  ItemStack loaded=in.read("storedBackpack",ItemStack.CODEC).orElse(ItemStack.EMPTY);
  backpack=loaded.getItem() instanceof NetworkBackpackItem?loaded:ItemStack.EMPTY;
 }
 @Override public void preRemoveSideEffects(BlockPos p,BlockState state){
  if(level instanceof ServerLevel server&&!backpack.isEmpty()){
   ItemStack output=takeBackpack();
   Containers.dropItemStack(server,p.getX()+.5,p.getY()+.5,p.getZ()+.5,output);
  }
  super.preRemoveSideEffects(p,state);
 }
}
''')

for tier in range(1,25):
 name=f"network_backpack_mk{tier}"
 # No normal loot drop: block entity drops the ORIGINAL populated backpack.
 rel=R/f"data/obsidiannetwork/loot_table/blocks/{name}.json"
 assert not rel.exists(),rel
 rel.parent.mkdir(parents=True,exist_ok=True)
 rel.write_text(json.dumps({"type":"minecraft:block","pools":[]},indent=2)+"\n")
 state=R/f"assets/obsidiannetwork/blockstates/{name}.json"
 assert not state.exists(),state
 state.parent.mkdir(parents=True,exist_ok=True)
 state.write_text(json.dumps({"variants":{
  d:{"model":"obsidiannetwork:block/"+name,"y":rotation}
  for d,rotation in (("facing=north",0),("facing=east",90),
                     ("facing=south",180),("facing=west",270))}},indent=2)+"\n")
print("V176_BACKPACK_24_WORLD_BLOCKS_ORIGINAL_ITEMSTACK_PICKUP_SAVE_PASS")
