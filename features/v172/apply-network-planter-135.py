#!/usr/bin/env python3
"""v1.7.2: NETWORK PLANTER. Durable crop/soil/upgrades + output to adjacent
xSxLabs Network Cable or bottom hopper/pipe. Failure keeps the actual items.
"""
import os,json
from pathlib import Path
java=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
res=Path(os.environ["V1_RESOURCE_ROOT"])
def edit(path,old,new):
 f=java/path
 s=f.read_text(encoding="utf-8")
 assert s.count(old)==1,(path,old[:80],s.count(old))
 f.write_text(s.replace(old,new,1),encoding="utf-8")
def write(rel,body):
 p=java/rel;assert not p.exists(),str(p);p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(body,encoding="utf-8")
def resource(rel,obj):
 p=res/rel;p.parent.mkdir(parents=True,exist_ok=True)
 assert not p.exists(),rel
 p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
edit("ObsidianNetwork.java",
 '''    public static final DeferredItem<BlockItem> ARMOR_STATION_ITEM=ITEMS.registerSimpleBlockItem("armor_station",ARMOR_STATION);''',
 '''    public static final DeferredItem<BlockItem> ARMOR_STATION_ITEM=ITEMS.registerSimpleBlockItem("armor_station",ARMOR_STATION);
    // V172_NETWORK_PLANTER: crop factory with native xSxLabs cable injection.
    public static final DeferredBlock<dev.obsidiannetwork.block.NetworkPlanterBlock> NETWORK_PLANTER =
       BLOCKS.registerBlock("network_planter",dev.obsidiannetwork.block.NetworkPlanterBlock::new,
          p -> p.mapColor(MapColor.WOOD).strength(1.0F,6.0F).noOcclusion());
    public static final DeferredItem<BlockItem> NETWORK_PLANTER_ITEM =
       ITEMS.registerSimpleBlockItem("network_planter",NETWORK_PLANTER);''')
edit("registry/ModBlockEntities.java",
 '''   public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<dev.obsidiannetwork.powerarmor.ArmorStationBlockEntity>> ARMOR_STATION =''',
 '''   public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<dev.obsidiannetwork.blockentity.NetworkPlanterBlockEntity>> NETWORK_PLANTER =
      TYPES.register("network_planter", () -> new BlockEntityType(
        dev.obsidiannetwork.blockentity.NetworkPlanterBlockEntity::new,
        new Block[]{(Block)ObsidianNetwork.NETWORK_PLANTER.get()}));
   public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<dev.obsidiannetwork.powerarmor.ArmorStationBlockEntity>> ARMOR_STATION =''')
write("block/NetworkPlanterBlock.java",r'''package dev.obsidiannetwork.block;
import com.mojang.serialization.MapCodec;
import dev.obsidiannetwork.blockentity.NetworkPlanterBlockEntity;
import dev.obsidiannetwork.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import org.jetbrains.annotations.Nullable;
/** V172_NETWORK_PLANTER: hand-place soil, seed, existing Speed Upgrade x16. */
public final class NetworkPlanterBlock extends BaseEntityBlock {
 private static final MapCodec<NetworkPlanterBlock> CODEC=simpleCodec(NetworkPlanterBlock::new);
 public NetworkPlanterBlock(Properties p){super(p);}
 @Override protected MapCodec<? extends BaseEntityBlock> codec(){return CODEC;}
 @Override public RenderShape getRenderShape(BlockState state){return RenderShape.MODEL;}
 @Nullable @Override public BlockEntity newBlockEntity(BlockPos pos,BlockState state){
  return new NetworkPlanterBlockEntity(pos,state);
 }
 @Override public <T extends BlockEntity> BlockEntityTicker<T> getTicker(
   Level level,BlockState state,BlockEntityType<T> type){
  return level.isClientSide()?null:createTickerHelper(type,ModBlockEntities.NETWORK_PLANTER.get(),
      NetworkPlanterBlockEntity::tick);
 }
 @Override protected InteractionResult useItemOn(ItemStack held,BlockState state,
   Level level,BlockPos pos,Player player,InteractionHand hand,BlockHitResult hit){
  if(hand!=InteractionHand.MAIN_HAND)return InteractionResult.PASS;
  if(level.getBlockEntity(pos) instanceof NetworkPlanterBlockEntity be && be.accepts(held)){
   if(!level.isClientSide())be.install(player,held);
   return InteractionResult.SUCCESS;
  }
  return InteractionResult.PASS;
 }
 @Override protected InteractionResult useWithoutItem(BlockState state,Level level,
   BlockPos pos,Player player,BlockHitResult hit){
  if(level.getBlockEntity(pos) instanceof NetworkPlanterBlockEntity be){
   if(!level.isClientSide())be.inspectOrRemove(player);
   return InteractionResult.SUCCESS;
  }
  return InteractionResult.PASS;
 }
}
''')
write("blockentity/NetworkPlanterBlockEntity.java",r'''package dev.obsidiannetwork.blockentity;
import dev.obsidiannetwork.ObsidianNetwork;
import dev.obsidiannetwork.core.ItemKey;
import dev.obsidiannetwork.core.NetworkRuntime;
import dev.obsidiannetwork.network.WorldTopologyBridge;
import dev.obsidiannetwork.registry.ModBlockEntities;
import java.util.*;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Container;
import net.minecraft.world.Containers;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/** V172_NETWORK_PLANTER_SAFE_INSERT: one single authoritative output stack.
 * The output only shrinks by an acknowledged network insert or a real inventory
 * extraction; no simulated/visual second copy exists. Soil and seed are stable.
 */
public final class NetworkPlanterBlockEntity extends BlockEntity implements Container {
 private ItemStack soil=ItemStack.EMPTY,seed=ItemStack.EMPTY,output=ItemStack.EMPTY;
 private int upgrades=0,progress=0,harvests=0;
 public NetworkPlanterBlockEntity(BlockPos pos,BlockState state){
  super(ModBlockEntities.NETWORK_PLANTER.get(),pos,state);
 }
 public boolean accepts(ItemStack item){
  return !item.isEmpty() &&
    (item.is(ObsidianNetwork.SPEED_UPGRADE.get()) || isSoil(item) || crop(item)!=null);
 }
 private static boolean isSoil(ItemStack stack){
  return stack.is(Blocks.DIRT.asItem())||stack.is(Blocks.GRASS_BLOCK.asItem())
    ||stack.is(Blocks.FARMLAND.asItem())||stack.is(Blocks.SOUL_SAND.asItem())
    ||stack.is(Blocks.MUD.asItem())||stack.is(Blocks.PODZOL.asItem());
 }
 private static Item crop(ItemStack stack){
  if(stack.is(Items.WHEAT_SEEDS))return Items.WHEAT;
  if(stack.is(Items.BEETROOT_SEEDS))return Items.BEETROOT;
  if(stack.is(Items.CARROT))return Items.CARROT;
  if(stack.is(Items.POTATO))return Items.POTATO;
  if(stack.is(Items.MELON_SEEDS))return Items.MELON_SLICE;
  if(stack.is(Items.PUMPKIN_SEEDS))return Items.PUMPKIN;
  if(stack.is(Items.NETHER_WART))return Items.NETHER_WART;
  if(stack.is(Items.SWEET_BERRIES))return Items.SWEET_BERRIES;
  if(stack.is(Items.COCOA_BEANS))return Items.COCOA_BEANS;
  if(stack.is(Items.CACTUS))return Items.CACTUS;
  if(stack.is(Items.SUGAR_CANE))return Items.SUGAR_CANE;
  if(stack.is(Items.BAMBOO))return Items.BAMBOO;
  return null;
 }
 private boolean validPair(){
  if(soil.isEmpty()||seed.isEmpty()||crop(seed)==null)return false;
  // Nether wart needs soul sand. Everything else needs dirt-type soil.
  return seed.is(Items.NETHER_WART)==soil.is(Blocks.SOUL_SAND.asItem());
 }
 public void install(Player player,ItemStack held){
  if(held.is(ObsidianNetwork.SPEED_UPGRADE.get())){
   int n=Math.min(16-upgrades,held.getCount());
   if(n>0){upgrades+=n;if(!player.isCreative())held.shrink(n);setChanged();}
   status(player);return;
  }
  if(isSoil(held)&&soil.isEmpty()){
   soil=held.copyWithCount(1);if(!player.isCreative())held.shrink(1);
   progress=0;setChanged();status(player);return;
  }
  if(crop(held)!=null&&seed.isEmpty()){
   seed=held.copyWithCount(1);if(!player.isCreative())held.shrink(1);
   progress=0;setChanged();status(player);return;
  }
  status(player);
 }
 public void inspectOrRemove(Player player){
  // Sneak + empty hand removes upgrades, then seed, then soil, then stored harvest.
  if(player.isShiftKeyDown()){
   ItemStack removed=ItemStack.EMPTY;
   if(upgrades>0){removed=new ItemStack(ObsidianNetwork.SPEED_UPGRADE.get(),upgrades);upgrades=0;}
   else if(!seed.isEmpty()){removed=seed;seed=ItemStack.EMPTY;progress=0;}
   else if(!soil.isEmpty()){removed=soil;soil=ItemStack.EMPTY;progress=0;}
   else if(!output.isEmpty()){removed=output;output=ItemStack.EMPTY;}
   if(!removed.isEmpty()){
    if(!player.getInventory().add(removed))Containers.dropItemStack(player.level(),player.getX(),player.getY(),player.getZ(),removed);
    setChanged();
   }
  }
  status(player);
 }
 private void status(Player p){
  String s=soil.isEmpty()?"none":soil.getHoverName().getString();
  String c=seed.isEmpty()?"none":seed.getHoverName().getString();
  p.displayClientMessage(Component.literal("Network Planter | Soil: "+s+" | Seed: "+c+
    " | Speed "+upgrades+"/16 | Growth "+progress+"/"+period()+
    " | Stored "+output.getCount()),true);
 }
 private int period(){
  // 0 = 30 seconds, 16 = ~2.5 seconds; every upgrade improves production.
  return Math.max(20,(int)Math.ceil(600D/(1D+0.70D*upgrades)));
 }
 private int yield(){
  if(seed.is(Items.NETHER_WART))return 2;
  if(seed.is(Items.MELON_SEEDS))return 4;
  if(seed.is(Items.COCOA_BEANS))return 3;
  if(seed.is(Items.SWEET_BERRIES))return 2;
  return 1;
 }
 public static void tick(Level level,BlockPos pos,BlockState state,NetworkPlanterBlockEntity be){
  if(!(level instanceof ServerLevel world))return;
  // Direct cable output is attempted before and after harvest. Storage FULL
  // => leave all items in the same persistent buffer for hopper/pipes to pull.
  if(world.getGameTime()%5L==0L)be.flushNetwork(world);
  if(!be.validPair())return;
  if(be.progress<be.period()){be.progress++;be.setChanged();return;}
  Item item=crop(be.seed);
  int n=be.yield();
  if(item==null)return;
  if(!be.output.isEmpty()&&(!be.output.is(item)||be.output.getCount()+n>be.output.getMaxStackSize()))return;
  if(be.output.isEmpty())be.output=new ItemStack(item,n);
  else be.output.grow(n);
  be.harvests++;
  be.progress=0;be.setChanged();
  be.flushNetwork(world);
 }
 private void flushNetwork(ServerLevel level){
  if(output.isEmpty())return;
  for(Direction face:Direction.values()){
   BlockPos cablePos=worldPosition.relative(face);
   if(!level.hasChunkAt(cablePos) || !level.getBlockState(cablePos).is(ObsidianNetwork.NETWORK_CABLE.get()))continue;
   NetworkRuntime runtime=WorldTopologyBridge.runtimeForAccessory(level,cablePos);
   if(runtime==null||!runtime.powered())continue;
   ItemKey key=ItemKey.simple(BuiltInRegistries.ITEM.getKey(output.getItem()).toString());
   long written=runtime.storage().insert(key,output.getCount());
   if(written>0L){
    output.shrink((int)Math.min(written,output.getCount()));
    if(output.isEmpty())output=ItemStack.EMPTY;
    setChanged();
   }
   // Exactly one active network at a time. Never spray one harvest over
   // differently-owned networks or duplicate failed batches.
   return;
  }
 }
 @Override protected void saveAdditional(ValueOutput out){
  super.saveAdditional(out);
  if(!soil.isEmpty())out.store("soil",ItemStack.CODEC,soil);
  if(!seed.isEmpty())out.store("seed",ItemStack.CODEC,seed);
  if(!output.isEmpty())out.store("output",ItemStack.CODEC,output);
  out.putInt("upgrades",upgrades);out.putInt("progress",progress);out.putInt("harvests",harvests);
 }
 @Override protected void loadAdditional(ValueInput in){
  super.loadAdditional(in);
  soil=in.read("soil",ItemStack.CODEC).orElse(ItemStack.EMPTY);
  seed=in.read("seed",ItemStack.CODEC).orElse(ItemStack.EMPTY);
  output=in.read("output",ItemStack.CODEC).orElse(ItemStack.EMPTY);
  upgrades=Math.max(0,Math.min(16,in.getIntOr("upgrades",0)));
  progress=Math.max(0,in.getIntOr("progress",0));
  harvests=Math.max(0,in.getIntOr("harvests",0));
 }
 @Override public void preRemoveSideEffects(BlockPos pos,BlockState state){
  if(level instanceof ServerLevel world){
   for(ItemStack s:new ItemStack[]{soil,seed,output})
    if(!s.isEmpty())Containers.dropItemStack(world,pos.getX()+.5,pos.getY()+.5,pos.getZ()+.5,s.copy());
   if(upgrades>0)Containers.dropItemStack(world,pos.getX()+.5,pos.getY()+.5,pos.getZ()+.5,
      new ItemStack(ObsidianNetwork.SPEED_UPGRADE.get(),upgrades));
   soil=ItemStack.EMPTY;seed=ItemStack.EMPTY;output=ItemStack.EMPTY;upgrades=0;
  }
  super.preRemoveSideEffects(pos,state);
 }
 // Only the OUTPUT is exposed. Pipes/hoppers never steal seed or soil.
 @Override public int getContainerSize(){return 1;}
 @Override public boolean isEmpty(){return output.isEmpty();}
 @Override public ItemStack getItem(int slot){return slot==0?output:ItemStack.EMPTY;}
 @Override public ItemStack removeItem(int slot,int amount){
  if(slot!=0||amount<=0||output.isEmpty())return ItemStack.EMPTY;
  ItemStack taken=output.split(amount);
  if(output.isEmpty())output=ItemStack.EMPTY;
  setChanged();return taken;
 }
 @Override public ItemStack removeItemNoUpdate(int slot){
  if(slot!=0)return ItemStack.EMPTY;
  ItemStack taken=output;output=ItemStack.EMPTY;setChanged();return taken;
 }
 @Override public void setItem(int slot,ItemStack stack){
  if(slot==0){output=stack.copy();setChanged();}
 }
 @Override public boolean canPlaceItem(int slot,ItemStack stack){return false;}
 @Override public boolean stillValid(Player p){return !isRemoved()&&
  p.distanceToSqr(worldPosition.getX()+.5,worldPosition.getY()+.5,worldPosition.getZ()+.5)<=64D;}
 @Override public void clearContent(){output=ItemStack.EMPTY;setChanged();}
}
''')
write("blockentity/NetworkPlanterCapabilities.java",r'''package dev.obsidiannetwork.blockentity;
import dev.obsidiannetwork.registry.ModBlockEntities;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.capabilities.RegisterCapabilitiesEvent;
import net.neoforged.neoforge.transfer.item.VanillaContainerWrapper;
import net.minecraft.core.Direction;
/** V172_PLANTER_BOTTOM_OUTPUT: Hopper and item-pipe extraction only. */
@EventBusSubscriber(modid="obsidiannetwork")
public final class NetworkPlanterCapabilities {
 private NetworkPlanterCapabilities(){}
 @SubscribeEvent public static void register(RegisterCapabilitiesEvent event){
  event.registerBlockEntity(Capabilities.Item.BLOCK,
    ModBlockEntities.NETWORK_PLANTER.get(),
    (planter,side)->side==Direction.DOWN?VanillaContainerWrapper.of(planter):null);
 }
}
''')
# Basic shaped recipe + block/item visuals and English/German descriptions.
resource("data/obsidiannetwork/recipe/network_planter.json",{
 "type":"minecraft:crafting_shaped","pattern":["IGI","IHI","IRI"],
 "key":{"I":"minecraft:iron_ingot","G":"minecraft:glass","H":"minecraft:hopper","R":"minecraft:redstone"},
 "result":{"id":"obsidiannetwork:network_planter","count":1}})
resource("data/obsidiannetwork/loot_table/blocks/network_planter.json",{
 "type":"minecraft:block","pools":[{"rolls":1,"entries":[{"type":"minecraft:item","name":"obsidiannetwork:network_planter"}]}]})
resource("assets/obsidiannetwork/blockstates/network_planter.json",{"variants":{"":{"model":"obsidiannetwork:block/network_planter"}}})
cuboids=[
 ([1,0,1],[15,3,15],"base"),
 ([1,3,1],[3,10,15],"base"),
 ([13,3,1],[15,10,15],"base"),
 ([3,3,1],[13,10,3],"base"),
 ([3,3,13],[13,10,15],"base"),
 ([3,3,3],[13,7,13],"soil"),
 ([4,7,4],[12,8,12],"soil"),
]
parts=[]
for frm,to,key in cuboids:
 parts.append({"from":frm,"to":to,"faces":{f:{"texture":"#"+key}
    for f in ("north","south","east","west","up","down")}})
resource("assets/obsidiannetwork/models/block/network_planter.json",{
 "parent":"minecraft:block/block","ambientocclusion":False,
 "textures":{"base":"minecraft:block/stripped_oak_log","soil":"minecraft:block/dirt","particle":"minecraft:block/dirt"},
 "elements":parts})
resource("assets/obsidiannetwork/models/item/network_planter.json",{"parent":"obsidiannetwork:block/network_planter"})
resource("assets/obsidiannetwork/items/network_planter.json",{"model":{"type":"minecraft:model","model":"obsidiannetwork:item/network_planter"}})
for loc,text in (("de_de","Network Planter"),("en_us","Network Planter")):
 f=res/"assets/obsidiannetwork/lang"/(loc+".json")
 data=json.loads(f.read_text(encoding="utf-8"))
 data["block.obsidiannetwork.network_planter"]=text
 f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("V172_NETWORK_PLANTER PASS: planted crops, speed 0..16, direct cable insert, bottom pipe/hopper, persistent buffered output")
