#!/usr/bin/env python3
"""Build146: v1.7.2 Network Planter expansion; no mutation of stable freeze."""
import os,json
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])
def change(rel,old,new):
 p=J/rel;s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,(rel,old[:130],s.count(old))
 p.write_text(s.replace(old,new,1),encoding="utf-8")
def java(rel,body):
 p=J/rel;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(body,encoding="utf-8")
def asset(rel,contents):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(contents,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
WOODS={
 "oak":("minecraft:block/stripped_oak_log","minecraft:stripped_oak_log"),
 "spruce":("minecraft:block/stripped_spruce_log","minecraft:stripped_spruce_log"),
 "birch":("minecraft:block/stripped_birch_log","minecraft:stripped_birch_log"),
 "jungle":("minecraft:block/stripped_jungle_log","minecraft:stripped_jungle_log"),
 "acacia":("minecraft:block/stripped_acacia_log","minecraft:stripped_acacia_log"),
 "dark_oak":("minecraft:block/stripped_dark_oak_log","minecraft:stripped_dark_oak_log"),
 "mangrove":("minecraft:block/stripped_mangrove_log","minecraft:stripped_mangrove_log"),
 "cherry":("minecraft:block/stripped_cherry_log","minecraft:stripped_cherry_log"),
 "pale_oak":("minecraft:block/stripped_pale_oak_log","minecraft:stripped_pale_oak_log"),
 "bamboo":("minecraft:block/stripped_bamboo_block","minecraft:stripped_bamboo_block"),
 "crimson":("minecraft:block/stripped_crimson_stem","minecraft:stripped_crimson_stem"),
 "warped":("minecraft:block/stripped_warped_stem","minecraft:stripped_warped_stem")
}
# (enum ID, accepted seed, guaranteed product, leaf, plant texture, tree?)
PLANTS=[
 ("WHEAT","WHEAT_SEEDS","WHEAT","", "minecraft:block/wheat_stage7",False),
 ("BEETROOT","BEETROOT_SEEDS","BEETROOT","", "minecraft:block/beetroots_stage3",False),
 ("CARROT","CARROT","CARROT","", "minecraft:block/carrots_stage3",False),
 ("POTATO","POTATO","POTATO","", "minecraft:block/potatoes_stage3",False),
 ("MELON","MELON_SEEDS","MELON_SLICE","", "minecraft:block/melon_stem",False),
 ("PUMPKIN","PUMPKIN_SEEDS","PUMPKIN","", "minecraft:block/pumpkin_stem",False),
 ("NETHER_WART","NETHER_WART","NETHER_WART","", "minecraft:block/nether_wart_stage2",False),
 ("SWEET_BERRIES","SWEET_BERRIES","SWEET_BERRIES","", "minecraft:block/sweet_berry_bush_stage3",False),
 ("COCOA","COCOA_BEANS","COCOA_BEANS","", "minecraft:block/cocoa_stage2",False),
 ("CACTUS","CACTUS","CACTUS","", "minecraft:block/cactus_side",False),
 ("SUGAR_CANE","SUGAR_CANE","SUGAR_CANE","", "minecraft:block/sugar_cane",False),
 ("BAMBOO","BAMBOO","BAMBOO","", "minecraft:block/bamboo_stalk",False),
 ("OAK","OAK_SAPLING","OAK_LOG","OAK_LEAVES","minecraft:block/oak_sapling",True),
 ("SPRUCE","SPRUCE_SAPLING","SPRUCE_LOG","SPRUCE_LEAVES","minecraft:block/spruce_sapling",True),
 ("BIRCH","BIRCH_SAPLING","BIRCH_LOG","BIRCH_LEAVES","minecraft:block/birch_sapling",True),
 ("JUNGLE","JUNGLE_SAPLING","JUNGLE_LOG","JUNGLE_LEAVES","minecraft:block/jungle_sapling",True),
 ("ACACIA","ACACIA_SAPLING","ACACIA_LOG","ACACIA_LEAVES","minecraft:block/acacia_sapling",True),
 ("DARK_OAK","DARK_OAK_SAPLING","DARK_OAK_LOG","DARK_OAK_LEAVES","minecraft:block/dark_oak_sapling",True),
 ("MANGROVE","MANGROVE_PROPAGULE","MANGROVE_LOG","MANGROVE_LEAVES","minecraft:block/mangrove_propagule",True),
 ("CHERRY","CHERRY_SAPLING","CHERRY_LOG","CHERRY_LEAVES","minecraft:block/cherry_sapling",True),
 ("PALE_OAK","PALE_OAK_SAPLING","PALE_OAK_LOG","PALE_OAK_LEAVES","minecraft:block/pale_oak_sapling",True),
 ("AZALEA","AZALEA","OAK_LOG","AZALEA_LEAVES","minecraft:block/azalea",True),
 ("FLOWERING_AZALEA","FLOWERING_AZALEA","OAK_LOG","FLOWERING_AZALEA_LEAVES","minecraft:block/flowering_azalea",True),
 ("CRIMSON","CRIMSON_FUNGUS","CRIMSON_STEM","NETHER_WART_BLOCK","minecraft:block/crimson_fungus",True),
 ("WARPED","WARPED_FUNGUS","WARPED_STEM","WARPED_WART_BLOCK","minecraft:block/warped_fungus",True)
]
enum="\n".join(f'  {a}(Items.{b},Items.{c},{"Items."+d if d else "Items.AIR"},{str(tree).lower()})'+("," if i<len(PLANTS)-1 else ";") for i,(a,b,c,d,tex,tree) in enumerate(PLANTS))
java("block/NetworkPlanterBlock.java",r'''package dev.obsidiannetwork.block;
import com.mojang.serialization.MapCodec;
import dev.obsidiannetwork.blockentity.NetworkPlanterBlockEntity;
import dev.obsidiannetwork.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.util.StringRepresentable;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.network.chat.Component;
import org.jetbrains.annotations.Nullable;
public final class NetworkPlanterBlock extends BaseEntityBlock {
 private static final MapCodec<NetworkPlanterBlock> CODEC=simpleCodec(NetworkPlanterBlock::new);
 public static final IntegerProperty AGE=IntegerProperty.create("age",0,3);
 public static final EnumProperty<Plant> PLANT=EnumProperty.create("plant",Plant.class);
 public enum Plant implements StringRepresentable {
PLANT_ENTRIES
  public final Item seed,produce,leaves;public final boolean tree;
  Plant(Item s,Item p,Item l,boolean t){seed=s;produce=p;leaves=l;tree=t;}
  @Override public String getSerializedName(){return name().toLowerCase(java.util.Locale.ROOT);}
  public static Plant of(ItemStack stack){
   if(stack.isEmpty())return WHEAT;
   for(Plant p:values())if(stack.is(p.seed))return p;
   return WHEAT;
  }
  public static boolean valid(ItemStack s){
   if(s.isEmpty())return false;
   for(Plant p:values())if(s.is(p.seed))return true;
   return false;
  }
 }
 public NetworkPlanterBlock(Properties p){
  super(p);registerDefaultState(stateDefinition.any().setValue(AGE,0).setValue(PLANT,Plant.WHEAT));
 }
 @Override protected void createBlockStateDefinition(StateDefinition.Builder<net.minecraft.world.level.block.Block,BlockState> builder){
  builder.add(AGE,PLANT);
 }
 @Override protected MapCodec<? extends BaseEntityBlock> codec(){return CODEC;}
 @Override public RenderShape getRenderShape(BlockState s){return RenderShape.MODEL;}
 @Nullable @Override public BlockEntity newBlockEntity(BlockPos pos,BlockState s){
  return new NetworkPlanterBlockEntity(pos,s);
 }
 @Override public <T extends BlockEntity> BlockEntityTicker<T> getTicker(
     Level level,BlockState state,BlockEntityType<T> type){
  return level.isClientSide()?null:createTickerHelper(type,ModBlockEntities.NETWORK_PLANTER.get(),
       NetworkPlanterBlockEntity::tick);
 }
 @Override protected InteractionResult useWithoutItem(BlockState state,Level level,
     BlockPos pos,Player player,BlockHitResult hit){return open(level,pos,player);}
 @Override protected InteractionResult useItemOn(ItemStack held,BlockState state,Level level,
     BlockPos pos,Player player,net.minecraft.world.InteractionHand hand,BlockHitResult hit){
  return hand==net.minecraft.world.InteractionHand.MAIN_HAND?open(level,pos,player):InteractionResult.PASS;
 }
 private InteractionResult open(Level level,BlockPos pos,Player player){
  if(!(level.getBlockEntity(pos) instanceof NetworkPlanterBlockEntity planter))return InteractionResult.PASS;
  if(player instanceof ServerPlayer sp)sp.openMenu(new SimpleMenuProvider(
      (id,inventory,who)->new dev.obsidiannetwork.menu.NetworkPlanterMenu(id,inventory,planter),
      Component.literal("xSxLabs | Network Planter")));
  return InteractionResult.SUCCESS;
 }
}
'''.replace("PLANT_ENTRIES",enum))
change("registry/ModBlockEntities.java",
 "new Block[]{(Block)ObsidianNetwork.NETWORK_PLANTER.get()}",
 "new Block[]{(Block)ObsidianNetwork.NETWORK_PLANTER.get(),"+",".join("(Block)ObsidianNetwork.NETWORK_PLANTER_"+w.upper()+".get()" for w in WOODS if w!="oak")+"}")
register="\n".join(
 "    public static final DeferredBlock<dev.obsidiannetwork.block.NetworkPlanterBlock> NETWORK_PLANTER_"+w.upper()+" =\n"+
 "       BLOCKS.registerBlock(\"network_planter_stripped_"+w+"\",dev.obsidiannetwork.block.NetworkPlanterBlock::new,\n"+
 "         p -> p.mapColor(MapColor.WOOD).strength(1.0F,6.0F).noOcclusion());\n"+
 "    public static final DeferredItem<BlockItem> NETWORK_PLANTER_"+w.upper()+"_ITEM =\n"+
 "       ITEMS.registerSimpleBlockItem(\"network_planter_stripped_"+w+"\",NETWORK_PLANTER_"+w.upper()+");"
 for w in WOODS if w!="oak")
change("ObsidianNetwork.java",
 'ITEMS.registerSimpleBlockItem("network_planter",NETWORK_PLANTER);',
 'ITEMS.registerSimpleBlockItem("network_planter",NETWORK_PLANTER);\n'+register)
creative="            output.accept((ItemLike)NETWORK_PLANTER_ITEM.get());\n"+"\n".join(
 "            output.accept((ItemLike)NETWORK_PLANTER_"+w.upper()+"_ITEM.get());"
 for w in WOODS if w!="oak")
change("ObsidianNetwork.java",
 "            output.accept((ItemLike)ARMOR_STATION_ITEM.get());",
 "            output.accept((ItemLike)ARMOR_STATION_ITEM.get());\n"+creative)
java("menu/NetworkPlanterMenu.java",r'''package dev.obsidiannetwork.menu;
import dev.obsidiannetwork.blockentity.NetworkPlanterBlockEntity;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.inventory.Slot;
public final class NetworkPlanterMenu extends ChestMenu {
 private final NetworkPlanterBlockEntity planter;
 public NetworkPlanterMenu(int id,Inventory inventory,NetworkPlanterBlockEntity be){
  super(MenuType.GENERIC_9x3,id,inventory,be,3);
  planter=be;
  // Exactly sixteen speed upgrades; no excess ItemStacks silently truncated.
  slots.set(2,new Slot(be,2,44,18){
   @Override public int getMaxStackSize(){return 16;}
  });
 }
 @Override public boolean stillValid(Player player){return planter.stillValid(player);}
}
''')
java("client/NetworkPlanterScreen.java",r'''package dev.obsidiannetwork.client;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.inventory.ContainerScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.ChestMenu;
/** Dedicated dark xSxLabs panel; server owns all 12 actual inventory slots. */
public final class NetworkPlanterScreen extends ContainerScreen {
 public NetworkPlanterScreen(ChestMenu menu,Inventory inventory,Component title){
  super(menu,inventory,title);
 }
 @Override public void extractBackground(GuiGraphicsExtractor g,int mouseX,int mouseY,float partial){
  int x=getLeftPos(),y=getTopPos();
  g.fill(x-3,y-3,x+179,y+getImageHeight()+3,0xff13b6cf);
  g.fill(x,y,x+176,y+getImageHeight(),0xff15202d);
  g.fill(x+4,y+15,x+172,y+74,0xff0a1721);
  for(int i=0;i<27;i++){
   int sx=x+7+(i%9)*18,sy=y+17+(i/9)*18;
   boolean active=i==0||i==1||i==2||(i>=9&&i<18);
   g.fill(sx,sy,sx+18,sy+18,active?0xffb99548:0xff20313e);
   g.fill(sx+1,sy+1,sx+17,sy+17,active?0xff243442:0xff10202b);
  }
  // Vanilla player inventory grid coordinates preserved exactly.
  int off=getImageHeight()-114;
  for(int i=0;i<36;i++){
   int sx=x+7+(i%9)*18,sy=y+off+(i<27?84+(i/9)*18:142);
   g.fill(sx,sy,sx+18,sy+18,0xff38556a);
   g.fill(sx+1,sy+1,sx+17,sy+17,0xff253545);
  }
  g.fill(x+4,y+75,x+172,y+78,0xff14879d);
 }
}
''')
# Existing Power Armor client subscriber already handles ScreenEvent.Opening safely.
client=J/"powerarmor/PowerArmorExitKeyClient.java"
src=client.read_text(encoding="utf-8")
assert src.rstrip().endswith("}")
src=src.rstrip()[:-1]+r'''
 @net.neoforged.bus.api.SubscribeEvent public static void xsxNetworkPlanterOpen(
    net.neoforged.neoforge.client.event.ScreenEvent.Opening event){
  if(!(event.getNewScreen() instanceof
       net.minecraft.client.gui.screens.inventory.ContainerScreen chest))return;
  if(!chest.getTitle().getString().equals("xSxLabs | Network Planter"))return;
  var client=net.minecraft.client.Minecraft.getInstance();
  if(client.player!=null)
   event.setNewScreen(new dev.obsidiannetwork.client.NetworkPlanterScreen(
       chest.getMenu(),client.player.getInventory(),chest.getTitle()));
 }
}
'''
client.write_text(src,encoding="utf-8")
# All output-only transfer paths must be side-limited (never steal seed/soil).
java("blockentity/NetworkPlanterCapabilities.java",r'''package dev.obsidiannetwork.blockentity;
import dev.obsidiannetwork.registry.ModBlockEntities;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.capabilities.RegisterCapabilitiesEvent;
import net.neoforged.neoforge.transfer.item.VanillaContainerWrapper;
import net.minecraft.core.Direction;
/** V172_PLANTER_BOTTOM_OUTPUT: only outputs exposed to downward item pipes. */
@EventBusSubscriber(modid="obsidiannetwork")
public final class NetworkPlanterCapabilities {
 private NetworkPlanterCapabilities(){}
 @SubscribeEvent public static void register(RegisterCapabilitiesEvent event){
  event.registerBlockEntity(Capabilities.Item.BLOCK,ModBlockEntities.NETWORK_PLANTER.get(),
    (planter,side)->side==Direction.DOWN?VanillaContainerWrapper.of(planter.outputOnly()):null);
 }
}
''')
java("blockentity/NetworkPlanterBlockEntity.java",r'''package dev.obsidiannetwork.blockentity;
import dev.obsidiannetwork.ObsidianNetwork;
import dev.obsidiannetwork.block.NetworkPlanterBlock;
import dev.obsidiannetwork.core.ItemKey;
import dev.obsidiannetwork.core.NetworkRuntime;
import dev.obsidiannetwork.network.WorldTopologyBridge;
import dev.obsidiannetwork.registry.ModBlockEntities;
import java.util.*;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Container;
import net.minecraft.world.Containers;
import net.minecraft.world.WorldlyContainer;
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
/** BUILD146_PLANTER_ATOMIC_NINE_SLOT: 0 soil, 1 seed, 2 speed, 9..17 output.
 * V172_NETWORK_PLANTER_SAFE_INSERT retained: multiple persistent outputs.
 * Nine independent persistent output stacks. Never insert more than capacity,
 * never consume an unacknowledged network/adjacent container transfer.
 */
public final class NetworkPlanterBlockEntity extends BlockEntity implements WorldlyContainer {
 private ItemStack soil=ItemStack.EMPTY,seed=ItemStack.EMPTY,speed=ItemStack.EMPTY;
 private final ItemStack[] output=new ItemStack[9];
 private int progress=0,harvests=0;
 private boolean stalled=false;
 private static final int[] OUTPUT_SLOTS={9,10,11,12,13,14,15,16,17};
 public NetworkPlanterBlockEntity(BlockPos p,BlockState s){
  super(ModBlockEntities.NETWORK_PLANTER.get(),p,s);
  Arrays.fill(output,ItemStack.EMPTY);
 }
 private static boolean soil(ItemStack s){
  return s.is(Blocks.DIRT.asItem())||s.is(Blocks.GRASS_BLOCK.asItem())
     ||s.is(Blocks.FARMLAND.asItem())||s.is(Blocks.SOUL_SAND.asItem())
     ||s.is(Blocks.MUD.asItem())||s.is(Blocks.PODZOL.asItem());
 }
 private static boolean seed(ItemStack s){return NetworkPlanterBlock.Plant.valid(s);}
 private boolean pair(){
  if(soil.isEmpty()||seed.isEmpty())return false;
  var plant=NetworkPlanterBlock.Plant.of(seed);
  if(plant==NetworkPlanterBlock.Plant.NETHER_WART)return soil.is(Blocks.SOUL_SAND.asItem());
  if(plant==NetworkPlanterBlock.Plant.CRIMSON||plant==NetworkPlanterBlock.Plant.WARPED)
   return soil.is(Blocks.CRIMSON_NYLIUM.asItem())||soil.is(Blocks.WARPED_NYLIUM.asItem());
  return !soil.is(Blocks.SOUL_SAND.asItem());
 }
 public int upgrades(){return Math.min(16,speed.getCount());}
 public int duration(){return Math.max(20,(int)Math.ceil(600D/(1D+.70D*upgrades())));}
 public int growth(){return progress;}
 public boolean paused(){return stalled;}
 public ItemStack soilStack(){return soil;}
 public ItemStack seedStack(){return seed;}
 public int stored(){int n=0;for(ItemStack x:output)n+=x.getCount();return n;}
 public int slotsUsed(){int n=0;for(ItemStack x:output)if(!x.isEmpty())n++;return n;}
 private void sync(){
  setChanged();
  if(level!=null&&!level.isClientSide())level.sendBlockUpdated(worldPosition,getBlockState(),getBlockState(),3);
 }
 @Override public net.minecraft.nbt.CompoundTag getUpdateTag(HolderLookup.Provider registry){
  return saveWithoutMetadata(registry);
 }
 @Override public Packet<ClientGamePacketListener> getUpdatePacket(){
  return ClientboundBlockEntityDataPacket.create(this);
 }
 private void phase(){
  if(level==null||level.isClientSide())return;
  BlockState state=getBlockState();
  if(!(state.getBlock() instanceof NetworkPlanterBlock))return;
  int age=pair()?Math.min(3,(int)((long)progress*4L/Math.max(1,duration()))):0;
  var plant=NetworkPlanterBlock.Plant.of(seed);
  if(state.getValue(NetworkPlanterBlock.AGE)!=age||state.getValue(NetworkPlanterBlock.PLANT)!=plant)
   level.setBlock(worldPosition,state.setValue(NetworkPlanterBlock.AGE,age)
       .setValue(NetworkPlanterBlock.PLANT,plant),3);
 }
 private static void addDrop(Map<Item,Integer> drops,Item item,int quantity){
  if(quantity>0&&item!=Items.AIR)drops.merge(item,quantity,Integer::sum);
 }
 private Map<Item,Integer> harvest(ServerLevel world){
  Map<Item,Integer> drops=new LinkedHashMap<>();
  var plant=NetworkPlanterBlock.Plant.of(seed);
  addDrop(drops,plant.produce,plant.tree?1+world.getRandom().nextInt(3):1);
  if(plant.tree){
   // Each harvest always contains logs; optional secondary products use
   // independent rolls. Sticks/leaves/saplings for every tree type.
   if(world.getRandom().nextFloat()<.34F)addDrop(drops,plant.leaves,1+world.getRandom().nextInt(3));
   if(world.getRandom().nextFloat()<.24F)addDrop(drops,Items.STICK,1+world.getRandom().nextInt(2));
   if(world.getRandom().nextFloat()<.12F)addDrop(drops,plant.seed,1);
   if((plant==NetworkPlanterBlock.Plant.OAK||plant==NetworkPlanterBlock.Plant.DARK_OAK)
        &&world.getRandom().nextFloat()<.08F)addDrop(drops,Items.APPLE,1);
  }else if(plant==NetworkPlanterBlock.Plant.MELON)addDrop(drops,Items.MELON_SLICE,2);
  else if(plant==NetworkPlanterBlock.Plant.SWEET_BERRIES)addDrop(drops,Items.SWEET_BERRIES,1);
  return drops;
 }
 private boolean fits(Map<Item,Integer> drops){
  for(var drop:drops.entrySet()){
   int required=drop.getValue();
   for(ItemStack s:output)if(s.is(drop.getKey()))
     required-=s.getMaxStackSize()-s.getCount();
   for(ItemStack s:output)if(s.isEmpty())
     required-=drop.getKey().getDefaultMaxStackSize();
   if(required>0)return false;
  }
  // Also account for competition for initially empty slots from DIFFERENT products.
  int empty=0;for(ItemStack s:output)if(s.isEmpty())empty++;
  int need=0;
  for(var drop:drops.entrySet()){
   int excess=drop.getValue();
   for(ItemStack s:output)if(s.is(drop.getKey()))
     excess-=s.getMaxStackSize()-s.getCount();
   if(excess>0)need+=(excess+drop.getKey().getDefaultMaxStackSize()-1)
                   /drop.getKey().getDefaultMaxStackSize();
  }
  return need<=empty;
 }
 private void store(Map<Item,Integer> drops){
  assert fits(drops);
  for(var e:drops.entrySet()){
   int n=e.getValue();Item item=e.getKey();
   for(int i=0;i<9&&n>0;i++){
    ItemStack s=output[i];
    if(!s.is(item))continue;
    int move=Math.min(n,s.getMaxStackSize()-s.getCount());
    s.grow(move);n-=move;
   }
   for(int i=0;i<9&&n>0;i++){
    if(!output[i].isEmpty())continue;
    int move=Math.min(n,item.getDefaultMaxStackSize());
    output[i]=new ItemStack(item,move);n-=move;
   }
   if(n!=0)throw new IllegalStateException("Network Planter buffer invariant");
  }
  sync();
 }
 public static void tick(Level level,BlockPos pos,BlockState state,NetworkPlanterBlockEntity be){
  if(!(level instanceof ServerLevel world))return;
  if(world.getGameTime()%5L==0L)be.flush(world);
  if(!be.pair()){
   if(be.progress!=0||be.stalled){be.progress=0;be.stalled=false;be.phase();be.sync();}
   return;
  }
  if(be.progress<be.duration()){
   be.progress++;
   if(world.getGameTime()%5L==0L)be.phase();
   if(be.progress>=be.duration())be.phase();
   return;
  }
  Map<Item,Integer> batch=be.harvest(world);
  if(!be.fits(batch)){
   if(!be.stalled){be.stalled=true;be.sync();}
   return;
  }
  be.store(batch);
  be.progress=0;be.harvests++;be.stalled=false;be.phase();
  be.flush(world);
 }
 private void flush(ServerLevel world){
  if(stored()==0)return;
  // An active adjacent xSxLabs cable gets priority, exactly one network.
  for(Direction face:Direction.values()){
   BlockPos p=worldPosition.relative(face);
   if(!world.hasChunkAt(p)||!world.getBlockState(p).is(ObsidianNetwork.NETWORK_CABLE.get()))continue;
   NetworkRuntime runtime=WorldTopologyBridge.runtimeForAccessory(world,p);
   if(runtime==null||!runtime.powered())continue;
   for(int i=0;i<9;i++){
    ItemStack stack=output[i];
    if(stack.isEmpty())continue;
    ItemKey key=ItemKey.simple(BuiltInRegistries.ITEM.getKey(stack.getItem()).toString());
    long accepted=runtime.storage().insert(key,stack.getCount());
    if(accepted>0){
     stack.shrink((int)Math.min(accepted,stack.getCount()));
     if(stack.isEmpty())output[i]=ItemStack.EMPTY;
     sync();
    }
   }
   return;
  }
  // Direct vanilla/modded Container chest BELOW. No hopper or extra block.
  BlockPos beneath=worldPosition.below();
  if(!world.hasChunkAt(beneath))return;
  if(world.getBlockEntity(beneath) instanceof Container dest &&dest!=this){
   int[] slots;
   if(dest instanceof WorldlyContainer sided)slots=sided.getSlotsForFace(Direction.UP);
   else {slots=new int[dest.getContainerSize()];for(int i=0;i<slots.length;i++)slots[i]=i;}
   for(int index=0;index<9;index++){
    ItemStack stack=output[index];
    if(stack.isEmpty())continue;
    for(int slot:slots){
     if(slot<0||slot>=dest.getContainerSize())continue;
     if(!dest.canPlaceItem(slot,stack))continue;
     if(dest instanceof WorldlyContainer sided &&!sided.canPlaceItemThroughFace(slot,stack,Direction.UP))continue;
     ItemStack present=dest.getItem(slot);
     if(!present.isEmpty()&&!ItemStack.isSameItemSameComponents(present,stack))continue;
     int capacity=Math.min(dest.getMaxStackSize(),stack.getMaxStackSize());
     int room=capacity-(present.isEmpty()?0:present.getCount());
     int moved=Math.min(room,stack.getCount());
     if(moved<=0)continue;
     ItemStack updated=present.isEmpty()?stack.copyWithCount(moved):present.copy();
     if(!present.isEmpty())updated.grow(moved);
     dest.setItem(slot,updated);
     dest.setChanged();
     stack.shrink(moved);
     if(stack.isEmpty())output[index]=ItemStack.EMPTY;
     sync();
     if(stack.isEmpty())break;
    }
   }
  }
 }
 @Override protected void saveAdditional(ValueOutput out){
  super.saveAdditional(out);
  if(!soil.isEmpty())out.store("soil",ItemStack.CODEC,soil);
  if(!seed.isEmpty())out.store("seed",ItemStack.CODEC,seed);
  if(!speed.isEmpty())out.store("speed",ItemStack.CODEC,speed);
  out.store("outputs",ItemStack.OPTIONAL_CODEC.listOf(),Arrays.asList(output));
  out.putInt("progress",progress);out.putInt("harvests",harvests);
 }
 @Override protected void loadAdditional(ValueInput in){
  super.loadAdditional(in);
  soil=in.read("soil",ItemStack.CODEC).orElse(ItemStack.EMPTY);
  seed=in.read("seed",ItemStack.CODEC).orElse(ItemStack.EMPTY);
  speed=in.read("speed",ItemStack.CODEC).orElse(ItemStack.EMPTY);
  if(speed.isEmpty()&&in.getIntOr("upgrades",0)>0)
   speed=new ItemStack(ObsidianNetwork.SPEED_UPGRADE.get(),Math.min(16,in.getIntOr("upgrades",0)));
  var saved=in.read("outputs",ItemStack.OPTIONAL_CODEC.listOf()).orElse(List.of());
  Arrays.fill(output,ItemStack.EMPTY);
  for(int i=0;i<Math.min(9,saved.size());i++)output[i]=saved.get(i).copy();
  if(saved.isEmpty())output[0]=in.read("output",ItemStack.CODEC).orElse(ItemStack.EMPTY);
  progress=Math.max(0,in.getIntOr("progress",0));
  harvests=Math.max(0,in.getIntOr("harvests",0));
  stalled=false;
 }
 @Override public void preRemoveSideEffects(BlockPos pos,BlockState state){
  if(level instanceof ServerLevel world){
   for(ItemStack s:new ItemStack[]{soil,seed,speed})
    if(!s.isEmpty())Containers.dropItemStack(world,pos.getX()+.5,pos.getY()+.5,pos.getZ()+.5,s.copy());
   for(ItemStack s:output)if(!s.isEmpty())
    Containers.dropItemStack(world,pos.getX()+.5,pos.getY()+.5,pos.getZ()+.5,s.copy());
   soil=seed=speed=ItemStack.EMPTY;Arrays.fill(output,ItemStack.EMPTY);
  }
  super.preRemoveSideEffects(pos,state);
 }
 @Override public int getContainerSize(){return 27;}
 @Override public boolean isEmpty(){return soil.isEmpty()&&seed.isEmpty()&&speed.isEmpty()&&stored()==0;}
 @Override public ItemStack getItem(int slot){
  if(slot==0)return soil;if(slot==1)return seed;if(slot==2)return speed;
  return slot>=9&&slot<=17?output[slot-9]:ItemStack.EMPTY;
 }
 @Override public ItemStack removeItem(int slot,int amount){
  if(amount<=0||slot<0||slot>=27)return ItemStack.EMPTY;
  ItemStack current=getItem(slot);if(current.isEmpty())return ItemStack.EMPTY;
  ItemStack removed=current.split(amount);
  if(current.isEmpty())setInternal(slot,ItemStack.EMPTY);
  sync();if(slot==0||slot==1){progress=0;phase();}
  return removed;
 }
 @Override public ItemStack removeItemNoUpdate(int slot){
  ItemStack s=getItem(slot);if(s.isEmpty())return ItemStack.EMPTY;
  ItemStack result=s.copy();setInternal(slot,ItemStack.EMPTY);
  sync();if(slot==0||slot==1){progress=0;phase();}
  return result;
 }
 private void setInternal(int slot,ItemStack s){
  if(slot==0)soil=s;
  else if(slot==1)seed=s;
  else if(slot==2)speed=s;
  else if(slot>=9&&slot<=17)output[slot-9]=s;
 }
 @Override public void setItem(int slot,ItemStack stack){
  if(!stack.isEmpty()&&!canPlaceItem(slot,stack)&&slot<9)return;
  if(slot<0||slot>=27)return;
  if(slot>=3&&slot<9 || slot>=18)return;
  // Only output mutations due to player removal or accepted extraction;
  // no insertion of arbitrary items into output slots.
  if(slot>=9&&!stack.isEmpty()&&!ItemStack.isSameItemSameComponents(getItem(slot),stack))return;
  setInternal(slot,stack.copy());sync();
  if(slot==0||slot==1){progress=0;stalled=false;phase();}
 }
 @Override public boolean canPlaceItem(int slot,ItemStack s){
  return slot==0?soil(s):slot==1?seed(s):
         slot==2?s.is(ObsidianNetwork.SPEED_UPGRADE.get()):false;
 }
 @Override public boolean stillValid(Player p){
  return !isRemoved()&&p.distanceToSqr(worldPosition.getX()+.5,
                worldPosition.getY()+.5,worldPosition.getZ()+.5)<=64D;
 }
 @Override public void clearContent(){
  soil=seed=speed=ItemStack.EMPTY;Arrays.fill(output,ItemStack.EMPTY);
  progress=0;stalled=false;sync();phase();
 }
 @Override public int[] getSlotsForFace(Direction face){return face==Direction.DOWN?OUTPUT_SLOTS:new int[0];}
 @Override public boolean canPlaceItemThroughFace(int slot,ItemStack stack,Direction face){return false;}
 @Override public boolean canTakeItemThroughFace(int slot,ItemStack stack,Direction face){
  return face==Direction.DOWN&&slot>=9&&slot<=17;
 }
 private final class OutputView implements Container {
  @Override public int getContainerSize(){return 9;}
  @Override public boolean isEmpty(){return stored()==0;}
  @Override public ItemStack getItem(int slot){return slot>=0&&slot<9?output[slot]:ItemStack.EMPTY;}
  @Override public ItemStack removeItem(int slot,int count){
   return NetworkPlanterBlockEntity.this.removeItem(slot+9,count);
  }
  @Override public ItemStack removeItemNoUpdate(int slot){
   return NetworkPlanterBlockEntity.this.removeItemNoUpdate(slot+9);
  }
  @Override public void setItem(int slot,ItemStack stack){
   NetworkPlanterBlockEntity.this.setItem(slot+9,stack);
  }
  @Override public void setChanged(){NetworkPlanterBlockEntity.this.sync();}
  @Override public boolean stillValid(Player p){return NetworkPlanterBlockEntity.this.stillValid(p);}
  @Override public void clearContent(){for(int i=0;i<9;i++)output[i]=ItemStack.EMPTY;sync();}
  @Override public boolean canPlaceItem(int slot,ItemStack stack){return false;}
 }
 public Container outputOnly(){return new OutputView();}
}
''')
# Saplings require compatible substrate and the old 9-slot buffer stays saved.
change("blockentity/NetworkPlanterBlockEntity.java",
 '||s.is(Blocks.MUD.asItem())||s.is(Blocks.PODZOL.asItem());',
 '||s.is(Blocks.MUD.asItem())||s.is(Blocks.PODZOL.asItem())\n     ||s.is(Blocks.CRIMSON_NYLIUM.asItem())||s.is(Blocks.WARPED_NYLIUM.asItem());')
# Multi-part models combine 12 stripped wood variants with animated crop stages.
def wood_model(tex):
 cuboids=[
  ([1,0,1],[15,3,15],"base"),
  ([1,3,1],[3,10,15],"base"),
  ([13,3,1],[15,10,15],"base"),
  ([3,3,1],[13,10,3],"base"),
  ([3,3,13],[13,10,15],"base"),
  ([3,3,3],[13,7,13],"soil")]
 return {"parent":"minecraft:block/block","ambientocclusion":False,
   "textures":{"base":tex,"soil":"minecraft:block/dirt","particle":tex},
   "elements":[{"from":a,"to":b,"faces":{d:{"texture":"#"+k} for d in
     ["up","down","north","south","east","west"]}} for a,b,k in cuboids]}
for w,(texture,log) in WOODS.items():
 block="network_planter" if w=="oak" else "network_planter_stripped_"+w
 model="network_planter_wood_"+w
 asset("assets/obsidiannetwork/models/block/"+model+".json",wood_model(texture))
 multipart=[{"apply":{"model":"obsidiannetwork:block/"+model}}]
 for plant,seed,product,leaves,tex,tree in PLANTS:
  for age in range(4):
   multipart.append({"when":{"plant":plant.lower(),"age":str(age)},
     "apply":{"model":"obsidiannetwork:block/network_planter_grow_"+plant.lower()+"_"+str(age)}})
 asset("assets/obsidiannetwork/blockstates/"+block+".json",{"multipart":multipart})
 if w!="oak":
  asset("assets/obsidiannetwork/models/item/"+block+".json",{"parent":"obsidiannetwork:block/"+model})
  asset("assets/obsidiannetwork/items/"+block+".json",
    {"model":{"type":"minecraft:model","model":"obsidiannetwork:item/"+block}})
  asset("data/obsidiannetwork/recipe/"+block+".json",{
   "type":"minecraft:crafting_shapeless","ingredients":[
      "obsidiannetwork:network_planter",log],
   "result":{"id":"obsidiannetwork:"+block,"count":1}})
  asset("data/obsidiannetwork/loot_table/blocks/"+block+".json",{
   "type":"minecraft:block","pools":[{"rolls":1,"entries":[
      {"type":"minecraft:item","name":"obsidiannetwork:"+block}]}]})
 else:
  asset("assets/obsidiannetwork/models/item/network_planter.json",
        {"parent":"obsidiannetwork:block/"+model})
for plant,seed,product,leaves,tex,tree in PLANTS:
 for age in range(4):
  height=[2,4,8,12][age]
  # Two 45-degree crossed, transparent plant planes, progressively growing.
  parts=[]
  for angle in [-45,45]:
   parts.append({"from":[5,7,8],"to":[11,7+height,8],
      "rotation":{"origin":[8,8,8],"axis":"y","angle":angle,"rescale":False},
      "faces":{"north":{"texture":"#plant"},"south":{"texture":"#plant"}}})
  asset("assets/obsidiannetwork/models/block/network_planter_grow_"+plant.lower()+"_"+str(age)+".json",
    {"parent":"minecraft:block/block","ambientocclusion":False,"render_type":"minecraft:cutout",
     "textures":{"plant":tex,"particle":tex},"elements":parts})
for lang in ["de_de","en_us"]:
 file=R/"assets/obsidiannetwork/lang"/(lang+".json")
 data=json.loads(file.read_text(encoding="utf-8"))
 data["block.obsidiannetwork.network_planter"]="Network Planter (Stripped Oak)"
 data["item.obsidiannetwork.network_planter"]="Network Planter (Stripped Oak)"
 for w in WOODS:
  if w=="oak":continue
  name=" ".join(p.capitalize() for p in w.split("_"))
  data["block.obsidiannetwork.network_planter_stripped_"+w]="Network Planter (Stripped "+name+")"
  data["item.obsidiannetwork.network_planter_stripped_"+w]="Network Planter (Stripped "+name+")"
 file.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("BUILD146_NINE_BUFFER_WOOD_GROWTH_PASS: dedicated GUI, 12 stripped models, percent tree loot, paused on full, direct chest and native network")
