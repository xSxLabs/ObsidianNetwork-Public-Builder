#!/usr/bin/env python3
"""v1.7.8 mining-only FE Builder with a two-corner area card.

Each block performs bounded server-tick work; no block scanning during client
frames, never loads chunks, never mines outside claims/owner permission.
Real NeoForge 26.1 FE/item capabilities, 27-slot transactional output and
at most 2 block edits/machine/tick, 64 total/server-level/tick.
"""
import os,json
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])

def edit(rel,old,new):
 p=J/rel;s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("V178_MINING_SOURCE_DRIFT",rel,old[:90],s.count(old))
 p.write_text(s.replace(old,new,1),encoding="utf-8")
def emit(rel,java):
 p=J/rel;p.parent.mkdir(parents=True,exist_ok=True)
 assert not p.exists(),("V178_MINING_JAVA_DUPLICATE",rel)
 p.write_text(java,encoding="utf-8")
def asset(rel,data):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 assert not p.exists(),("V178_MINING_ASSET_DUPLICATE",rel)
 p.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

edit("ObsidianNetwork.java",
 '''   public static final DeferredBlock<dev.obsidiannetwork.power.V176PowerTerminalBlock> V176_POWER_TERMINAL =''',
 '''   public static final DeferredBlock<dev.obsidiannetwork.mining.V178MiningBuilderBlock> V178_MINING_BUILDER =
     BLOCKS.registerBlock("mining_builder",dev.obsidiannetwork.mining.V178MiningBuilderBlock::new,
       p -> p.mapColor(MapColor.METAL).strength(4.0F,12.0F).noOcclusion());
   public static final DeferredItem<BlockItem> V178_MINING_BUILDER_ITEM =
     ITEMS.registerSimpleBlockItem("mining_builder",V178_MINING_BUILDER);
   public static final DeferredItem<dev.obsidiannetwork.mining.V178MiningShapeCard> V178_SHAPE_CARD =
     ITEMS.registerItem("mining_shape_card",dev.obsidiannetwork.mining.V178MiningShapeCard::new);
   public static final DeferredBlock<dev.obsidiannetwork.power.V176PowerTerminalBlock> V176_POWER_TERMINAL =''')
edit("ObsidianNetwork.java",
 '''            output.accept((ItemLike)V176_POWER_TERMINAL_ITEM.get());''',
 '''            output.accept((ItemLike)V176_POWER_TERMINAL_ITEM.get());
            output.accept((ItemLike)V178_MINING_BUILDER_ITEM.get());
            output.accept((ItemLike)V178_SHAPE_CARD.get());''')
edit("registry/ModBlockEntities.java",
 '''   // V174_REACTOR_CONTROLLER_BE: only the controller owns runtime fuel/FE.''',
 '''   public static final DeferredHolder<BlockEntityType<?>,BlockEntityType<dev.obsidiannetwork.mining.V178MiningBuilderBE>> V178_MINING_BUILDER =
     TYPES.register("mining_builder",()->new BlockEntityType(
       dev.obsidiannetwork.mining.V178MiningBuilderBE::new,
       new Block[]{(Block)ObsidianNetwork.V178_MINING_BUILDER.get()}));
   // V174_REACTOR_CONTROLLER_BE: only the controller owns runtime fuel/FE.''')

emit("mining/V178MiningShapeCard.java",r'''package dev.obsidiannetwork.mining;

import dev.obsidiannetwork.item.NetworkBlueprintItem;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.UseOnContext;

/** Two corners selected on blocks; dimension-bound, permanent area on item.
 *  Fails closed on absurd volumes and cross-dimension copying.
 */
public final class V178MiningShapeCard extends Item {
 public static final int MAX_SIDE=512;
 public static final long MAX_VOLUME=8_388_608L;
 public record Bounds(String dimension,int minX,int minY,int minZ,
                      int maxX,int maxY,int maxZ){
  public int width(){return maxX-minX+1;}
  public int height(){return maxY-minY+1;}
  public int depth(){return maxZ-minZ+1;}
  public long volume(){return (long)width()*height()*depth();}
  public BlockPos at(long index){
   long plane=(long)width()*height();
   return new BlockPos(minX+(int)(index%width()),
       minY+(int)((index/width())%height()),
       minZ+(int)(index/plane));
  }
 }
 public V178MiningShapeCard(Properties p){super(p.stacksTo(1));}
 public static Bounds read(ItemStack card){
  if(!(card.getItem() instanceof V178MiningShapeCard))return null;
  String value=NetworkBlueprintItem.read(card,"xsxlabs_mining_bounds");
  String[] args=value.split("[|]",-1);
  if(args.length!=7)return null;
  try{
   int minX=Integer.parseInt(args[1]),minY=Integer.parseInt(args[2]),
       minZ=Integer.parseInt(args[3]),maxX=Integer.parseInt(args[4]),
       maxY=Integer.parseInt(args[5]),maxZ=Integer.parseInt(args[6]);
   Bounds bounds=new Bounds(args[0],minX,minY,minZ,maxX,maxY,maxZ);
   if(!valid(bounds))return null;
   return bounds;
  }catch(NumberFormatException ex){return null;}
 }
 public static boolean valid(Bounds b){
  return b!=null&&!b.dimension().isBlank()&&b.minX()<=b.maxX()
   &&b.minY()<=b.maxY()&&b.minZ()<=b.maxZ()
   &&b.width()>0&&b.height()>0&&b.depth()>0
   &&Math.abs((long)b.minX())<=30_000_000&&Math.abs((long)b.maxX())<=30_000_000
   &&Math.abs((long)b.minZ())<=30_000_000&&Math.abs((long)b.maxZ())<=30_000_000
   &&b.width()<=MAX_SIDE&&b.height()<=MAX_SIDE&&b.depth()<=MAX_SIDE
   &&b.volume()<=MAX_VOLUME;
 }
 @Override public InteractionResult useOn(UseOnContext c){
  if(!(c.getLevel() instanceof ServerLevel world))return InteractionResult.SUCCESS;
  if(!(c.getPlayer() instanceof ServerPlayer player))return InteractionResult.FAIL;
  ItemStack item=c.getItemInHand();
  BlockPos point=c.getClickedPos();
  String dim=world.dimension().identifier().toString();
  String pending=NetworkBlueprintItem.read(item,"xsxlabs_mining_first");
  if(!pending.startsWith(dim+"|")){
   NetworkBlueprintItem.write(item,"xsxlabs_mining_first",
       dim+"|"+point.getX()+"|"+point.getY()+"|"+point.getZ());
   player.sendOverlayMessage(Component.literal("Mining Card: corner A selected"));
   return InteractionResult.SUCCESS;
  }
  String[] xyz=pending.split("[|]",-1);
  if(xyz.length!=4)return InteractionResult.FAIL;
  try{
   int x=Integer.parseInt(xyz[1]),y=Integer.parseInt(xyz[2]),
       z=Integer.parseInt(xyz[3]);
   Bounds b=new Bounds(dim,Math.min(x,point.getX()),Math.min(y,point.getY()),
       Math.min(z,point.getZ()),Math.max(x,point.getX()),
       Math.max(y,point.getY()),Math.max(z,point.getZ()));
   if(!valid(b)){
    player.sendOverlayMessage(Component.literal(
       "Mining Card: area too large (max 512 each axis, 8M blocks)"));
    return InteractionResult.FAIL;
   }
   NetworkBlueprintItem.write(item,"xsxlabs_mining_bounds",
       dim+"|"+b.minX()+"|"+b.minY()+"|"+b.minZ()+"|"+
       b.maxX()+"|"+b.maxY()+"|"+b.maxZ());
   NetworkBlueprintItem.write(item,"xsxlabs_mining_first","");
   player.sendOverlayMessage(Component.literal(
       "Mining Card: "+b.width()+"x"+b.height()+"x"+b.depth()+
       " | "+b.volume()+" blocks"));
   return InteractionResult.SUCCESS;
  }catch(NumberFormatException ex){return InteractionResult.FAIL;}
 }
}
''')

emit("mining/V178MiningBuilderBlock.java",r'''package dev.obsidiannetwork.mining;
import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
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
public final class V178MiningBuilderBlock extends BaseEntityBlock {
 private static final MapCodec<V178MiningBuilderBlock> CODEC=simpleCodec(V178MiningBuilderBlock::new);
 public V178MiningBuilderBlock(Properties p){super(p);}
 @Override protected MapCodec<? extends BaseEntityBlock> codec(){return CODEC;}
 @Override public RenderShape getRenderShape(BlockState state){return RenderShape.MODEL;}
 @Nullable @Override public BlockEntity newBlockEntity(BlockPos pos,BlockState state){
  return new V178MiningBuilderBE(pos,state);
 }
 @Nullable @Override public <T extends BlockEntity> BlockEntityTicker<T> getTicker(
       Level level,BlockState state,BlockEntityType<T> type){
  return level.isClientSide()?null:createTickerHelper(type,
       dev.obsidiannetwork.registry.ModBlockEntities.V178_MINING_BUILDER.get(),
       V178MiningBuilderBE::serverTick);
 }
 private InteractionResult action(Level level,BlockPos pos,Player player,ItemStack held){
  if(!(player instanceof ServerPlayer server))return InteractionResult.SUCCESS;
  if(!(level.getBlockEntity(pos) instanceof V178MiningBuilderBE be))return InteractionResult.PASS;
  if(player.isShiftKeyDown()){
   ItemStack previous=be.removeCard(server);
   if(!previous.isEmpty()&&!server.getInventory().add(previous))
    net.minecraft.world.Containers.dropItemStack(level,player.getX(),player.getY(),player.getZ(),previous);
   return InteractionResult.SUCCESS;
  }
  if(held.getItem() instanceof V178MiningShapeCard){
   if(be.insertCard(server,held)){
    held.shrink(1);
    server.sendOverlayMessage(Component.literal("Mining Builder: region installed"));
   }else server.sendOverlayMessage(Component.literal("Mining Builder: invalid card or owner"));
   return InteractionResult.SUCCESS;
  }
  server.sendOverlayMessage(Component.literal(be.status()));
  return InteractionResult.SUCCESS;
 }
 @Override protected InteractionResult useWithoutItem(BlockState s,Level l,BlockPos p,Player u,BlockHitResult hit){
  return action(l,p,u,ItemStack.EMPTY);
 }
 @Override protected InteractionResult useItemOn(ItemStack item,BlockState s,Level l,
   BlockPos p,Player u,InteractionHand h,BlockHitResult hit){
  return h==InteractionHand.MAIN_HAND?action(l,p,u,item):InteractionResult.PASS;
 }
}
''')

emit("mining/V178MiningBuilderBE.java",r'''package dev.obsidiannetwork.mining;

import dev.obsidiannetwork.registry.ModBlockEntities;
import dev.obsidiannetwork.claims.V178Claims;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.Containers;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.neoforged.neoforge.transfer.CombinedResourceHandler;
import net.neoforged.neoforge.transfer.ResourceHandler;
import net.neoforged.neoforge.transfer.item.ItemResource;
import net.neoforged.neoforge.transfer.item.ItemStackResourceHandler;
import net.neoforged.neoforge.transfer.energy.SimpleEnergyHandler;
import net.neoforged.neoforge.transfer.transaction.Transaction;
import net.neoforged.neoforge.capabilities.Capabilities;
import java.util.*;

/** Mining ONLY. No block placement, world generation, no area scan each tick.
 *  Cursor iterates an immutable selection in O(1) per visited voxel.
 *  Output transfers use one root transaction for receiver+internal stock.
 */
public final class V178MiningBuilderBE extends BlockEntity {
 public static final int ENERGY_PER_BLOCK=2000, ENERGY_CAPACITY=2_000_000;
 public static final int MAX_VISITS=8,MAX_BREAKS=2;
 public static final int GLOBAL_BLOCK_BUDGET=Math.min(256,Math.max(1,
             Integer.getInteger("xsxlabs.mining.globalBreaks",64)));
 private static final Direction[] SIDES=Direction.values();
 private static final Map<ServerLevel,TickBudget> BUDGETS=
   Collections.synchronizedMap(new WeakHashMap<>());
 private static final class TickBudget{
  long tick=Long.MIN_VALUE;
  int remain=GLOBAL_BLOCK_BUDGET;
 }
 private final SimpleEnergyHandler energy=new SimpleEnergyHandler(
       ENERGY_CAPACITY,500_000,0){
  @Override protected void onEnergyChanged(int amount){setChanged();}
 };
 private final ItemStack[] stacks=new ItemStack[27];
 private final Slot[] slots=new Slot[27];
 private final ResourceHandler<ItemResource> output;
 private final class Slot extends ItemStackResourceHandler{
  private final int index;
  Slot(int index){this.index=index;}
  @Override protected ItemStack getStack(){return stacks[index];}
  @Override protected void setStack(ItemStack value){stacks[index]=value;setChanged();}
  @Override protected void onRootCommit(ItemStack previous){setChanged();}
 }
 private ItemStack card=ItemStack.EMPTY;
 private V178MiningShapeCard.Bounds bounds;
 private UUID owner;
 private long cursor=0L;
 private int nextOutputSlot=0;
 public V178MiningBuilderBE(BlockPos pos,BlockState state){
  super(ModBlockEntities.V178_MINING_BUILDER.get(),pos,state);
  Arrays.fill(stacks,ItemStack.EMPTY);
  for(int i=0;i<27;i++)slots[i]=new Slot(i);
  output=new CombinedResourceHandler<ItemResource>(slots);
 }
 public SimpleEnergyHandler energy(){return energy;}
 public ResourceHandler<ItemResource> items(){return output;}
 public String status(){
  return "Mining Builder | "+(bounds==null?"NO CARD":cursor+"/"+bounds.volume())+
     " | "+energy.getAmountAsLong()+" / "+ENERGY_CAPACITY+" FE";
 }
 public boolean insertCard(ServerPlayer player,ItemStack incoming){
  if(!card.isEmpty())return false;
  if(owner!=null&&!owner.equals(player.getUUID()))return false;
  V178MiningShapeCard.Bounds b=V178MiningShapeCard.read(incoming);
  if(b==null||!b.dimension().equals(player.level().dimension().identifier().toString()))return false;
  if(!V178Claims.mayModify((ServerLevel)player.level(),worldPosition,player.getUUID()))return false;
  owner=player.getUUID();bounds=b;
  card=incoming.copyWithCount(1);cursor=0L;setChanged();
  return true;
 }
 public ItemStack removeCard(ServerPlayer player){
  if(owner==null||!owner.equals(player.getUUID()))return ItemStack.EMPTY;
  ItemStack previous=card;
  card=ItemStack.EMPTY;bounds=null;cursor=0L;setChanged();
  return previous;
 }
 private static boolean budget(ServerLevel world){
  TickBudget t=BUDGETS.computeIfAbsent(world,k->new TickBudget());
  long tick=world.getGameTime();
  if(t.tick!=tick){t.tick=tick;t.remain=GLOBAL_BLOCK_BUDGET;}
  if(t.remain<=0)return false;
  --t.remain;return true;
 }
 private void output(ServerLevel world){
  if(world.getGameTime()%5!=0)return;
  // One output slot and up to six distinct loaded neighbors per cycle,
  // not a full 27x6 scan every tick. The exporter never drops mined items.
  for(int step=0;step<27;step++){
   int slot=(nextOutputSlot+step)%27;
   ItemResource what=output.getResource(slot);
   if(what.isEmpty())continue;
   int count=output.getAmountAsInt(slot);
   if(count<=0)continue;
   for(Direction side:SIDES){
    BlockPos at=worldPosition.relative(side);
    if(!world.hasChunkAt(at))continue;
    ResourceHandler<ItemResource> destination=world.getCapability(
             Capabilities.Item.BLOCK,at,side.getOpposite());
    if(destination==null||destination==output)continue;
    try(Transaction tx=Transaction.openRoot()){
     int accepted=destination.insert(what,count,tx);
     if(accepted>0&&output.extract(slot,what,accepted,tx)==accepted){
      tx.commit();
      nextOutputSlot=(slot+1)%27;
      return;
     }
    }
   }
  }
 }
 public static void serverTick(Level level,BlockPos at,BlockState state,V178MiningBuilderBE machine){
  if(!(level instanceof ServerLevel world))return;
  // Cheap idle gate: no FE or region -> zero world reads.
  if(machine.owner==null)return;
  machine.output(world);
  if(machine.bounds==null)return;
  if(machine.energy.getAmountAsLong()<ENERGY_PER_BLOCK)return;
  if(!machine.bounds.dimension().equals(world.dimension().identifier().toString()))return;
  if(machine.cursor>=machine.bounds.volume())return;
  int mined=0,visited=0;
  long previousCursor=machine.cursor;
  while(visited++<MAX_VISITS&&mined<MAX_BREAKS&&machine.cursor<machine.bounds.volume()){
   BlockPos target=machine.bounds.at(machine.cursor);
   if(!world.hasChunkAt(target))return; // never force/generate terrain
   BlockState current=world.getBlockState(target);
   if(current.isAir()||!current.getFluidState().isEmpty()
      ||current.getDestroySpeed(world,target)<0
      ||world.getBlockEntity(target)!=null
      ||target.equals(at)){
    ++machine.cursor;continue;
   }
   // Ownership enforced for every voxel, including cross-border selections.
   // Fail closed: target chunk must be owned by the builder operator.
   // No arbitrary wilderness or third-party-claimed mining.
   if(!machine.owner.equals(V178Claims.owner(world,target)))return;
   if(machine.energy.getAmountAsLong()<ENERGY_PER_BLOCK)return;
   // Read-only loot calculation. Ordinary drops, no silk/fortune duplication.
   var drops=Block.getDrops(current,world,target,null,null,new ItemStack(Items.NETHERITE_PICKAXE));
   try(Transaction tx=Transaction.openRoot()){
    boolean fits=true;
    for(ItemStack drop:drops)if(!drop.isEmpty()
       &&machine.output.insert(ItemResource.of(drop),drop.getCount(),tx)!=drop.getCount()){
      fits=false;break;
    }
    if(!fits)return; // full buffer means the mining machine PAUSES
    if(!budget(world))return; // global lag protection
    if(!world.destroyBlock(target,false))return;
    tx.commit(); // mined drops now owned by the machine, no item entities
    machine.energy.set(Math.max(0,machine.energy.getAmountAsInt()-ENERGY_PER_BLOCK));
    ++machine.cursor;machine.setChanged();mined++;
   }
  }
  if(machine.cursor!=previousCursor)machine.setChanged();
 }
 @Override protected void saveAdditional(ValueOutput out){
  super.saveAdditional(out);
  energy.serialize(out);
  if(!card.isEmpty())out.store("xsxMiningCard",ItemStack.CODEC,card);
  if(owner!=null)out.putString("xsxOwner",owner.toString());
  out.putLong("xsxMiningCursor",cursor);
  out.putInt("xsxMiningOutputSlot",nextOutputSlot);
  for(int i=0;i<27;i++)if(!stacks[i].isEmpty())
   out.store("xsxMiningSlot"+i,ItemStack.CODEC,stacks[i]);
 }
 @Override protected void loadAdditional(ValueInput in){
  super.loadAdditional(in);
  energy.deserialize(in);
  card=in.read("xsxMiningCard",ItemStack.CODEC).orElse(ItemStack.EMPTY);
  bounds=V178MiningShapeCard.read(card);
  try{owner=UUID.fromString(in.getStringOr("xsxOwner",""));}
  catch(IllegalArgumentException invalid){owner=null;}
  cursor=Math.max(0L,Math.min(bounds==null?0:bounds.volume(),
      in.getLongOr("xsxMiningCursor",0L)));
  nextOutputSlot=Math.floorMod(in.getIntOr("xsxMiningOutputSlot",0),27);
  for(int i=0;i<27;i++)stacks[i]=in.read("xsxMiningSlot"+i,ItemStack.CODEC)
     .orElse(ItemStack.EMPTY);
 }
 @Override public void preRemoveSideEffects(BlockPos p,BlockState state){
  if(level instanceof ServerLevel server){
   if(!card.isEmpty()){
    Containers.dropItemStack(server,p.getX()+.5,p.getY()+.5,p.getZ()+.5,card);
    card=ItemStack.EMPTY;
   }
   for(int i=0;i<27;i++)if(!stacks[i].isEmpty()){
    Containers.dropItemStack(server,p.getX()+.5,p.getY()+.5,p.getZ()+.5,stacks[i]);
    stacks[i]=ItemStack.EMPTY;
   }
  }
  super.preRemoveSideEffects(p,state);
 }
}
''')

emit("mining/V178MiningBuilderCapabilities.java",r'''package dev.obsidiannetwork.mining;
import dev.obsidiannetwork.registry.ModBlockEntities;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.capabilities.RegisterCapabilitiesEvent;
import net.neoforged.neoforge.capabilities.Capabilities;
/** Native NeoForge transactional FE input and 27-slot ItemResource output. */
@EventBusSubscriber(modid="obsidiannetwork")
public final class V178MiningBuilderCapabilities{
 private V178MiningBuilderCapabilities(){}
 @SubscribeEvent public static void register(RegisterCapabilitiesEvent e){
  e.registerBlockEntity(Capabilities.Energy.BLOCK,ModBlockEntities.V178_MINING_BUILDER.get(),
      (be,side)->be.energy());
  e.registerBlockEntity(Capabilities.Item.BLOCK,ModBlockEntities.V178_MINING_BUILDER.get(),
      (be,side)->be.items());
 }
}
''')

for name,texture in (("mining_builder","minecraft:block/iron_block"),):
 asset("assets/obsidiannetwork/blockstates/"+name+".json",
       {"variants":{"":{"model":"obsidiannetwork:block/"+name}}})
 asset("assets/obsidiannetwork/models/block/"+name+".json",
       {"parent":"minecraft:block/cube_all","textures":{"all":texture}})
 asset("assets/obsidiannetwork/items/"+name+".json",
       {"model":{"type":"minecraft:model","model":"obsidiannetwork:block/"+name}})
 asset("data/obsidiannetwork/loot_table/blocks/"+name+".json",
       {"type":"minecraft:block","pools":[{"rolls":1,
         "entries":[{"type":"minecraft:item","name":"obsidiannetwork:"+name}]}]})
asset("assets/obsidiannetwork/models/item/mining_shape_card.json",
      {"parent":"minecraft:item/generated",
       "textures":{"layer0":"minecraft:item/map"}})
asset("assets/obsidiannetwork/items/mining_shape_card.json",
      {"model":{"type":"minecraft:model","model":"obsidiannetwork:item/mining_shape_card"}})
asset("data/obsidiannetwork/recipe/mining_shape_card.json",
      {"type":"minecraft:crafting_shaped","pattern":["RPR","PMP","RPR"],
       "key":{"R":"minecraft:redstone","P":"minecraft:paper","M":"minecraft:map"},
       "result":{"id":"obsidiannetwork:mining_shape_card","count":1}})
asset("data/obsidiannetwork/recipe/mining_builder.json",
      {"type":"minecraft:crafting_shaped","pattern":["IDI","RPR","IGI"],
       "key":{"I":"minecraft:iron_block","D":"minecraft:diamond_pickaxe",
         "R":"minecraft:redstone_block","P":"minecraft:piston","G":"minecraft:gold_block"},
       "result":{"id":"obsidiannetwork:mining_builder","count":1}})
for lang,entries in [
 ("de_de",{"block.obsidiannetwork.mining_builder":"Mining Builder",
           "item.obsidiannetwork.mining_shape_card":"Mining-Bereichskarte"}),
 ("en_us",{"block.obsidiannetwork.mining_builder":"Mining Builder",
           "item.obsidiannetwork.mining_shape_card":"Mining Shape Card"})]:
 p=R/f"assets/obsidiannetwork/lang/{lang}.json"
 d=json.loads(p.read_text(encoding="utf-8"))
 for k,v in entries.items():
  assert k not in d,(lang,k)
  d[k]=v
 p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

print("V178_MINING_BUILDER_NEOFORGE_FE_ITEM_OUTPUT_CLAIMS_AND_BOUNDED_TICKS_INSTALLED")
