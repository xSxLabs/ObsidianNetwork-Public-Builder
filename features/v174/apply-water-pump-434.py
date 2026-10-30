#!/usr/bin/env python3
"""v1.7.4 electric water pump: source-adjacent, FE-driven, native fluid output.

Never loads chunks or takes water from other tanks. Speed upgrades work
on the real item slot and proportionally increase water & FE per cycle.
"""
import os,json
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])
def edit(rel,a,b):
 p=J/rel;text=p.read_text(encoding="utf-8")
 assert text.count(a)==1,("B434_PATCH_DRIFT",rel,a[:75],text.count(a))
 p.write_text(text.replace(a,b,1),encoding="utf-8")
def java(rel,s):
 p=J/rel;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists(),str(p);p.write_text(s,encoding="utf-8")
def emit(rel,j):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists(),str(p)
 p.write_text(json.dumps(j,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
edit("ObsidianNetwork.java","    // V174_REACTOR_CORE_427: add-only seven-part 5..64 multiblock.",
 '''    // V174_B434_ELECTRIC_WATER_PUMP: outputs water to NeoForge fluid cables.
    public static final DeferredBlock<dev.obsidiannetwork.pump.ElectricWaterPumpBlock> ELECTRIC_WATER_PUMP =
      BLOCKS.registerBlock("electric_water_pump",dev.obsidiannetwork.pump.ElectricWaterPumpBlock::new,
        p -> p.mapColor(MapColor.METAL).strength(3.0F,8.0F).requiresCorrectToolForDrops());
    public static final DeferredItem<BlockItem> ELECTRIC_WATER_PUMP_ITEM =
      ITEMS.registerSimpleBlockItem("electric_water_pump",ELECTRIC_WATER_PUMP);
    // V174_REACTOR_CORE_427: add-only seven-part 5..64 multiblock.''')
edit("ObsidianNetwork.java","            output.accept((ItemLike)REACTOR_CONTROLLER_ITEM.get());",
     "            output.accept((ItemLike)REACTOR_CONTROLLER_ITEM.get());\n"
     "            output.accept((ItemLike)ELECTRIC_WATER_PUMP_ITEM.get());")
edit("registry/ModBlockEntities.java",
 '   // V174_REACTOR_CONTROLLER_BE: only the controller owns runtime fuel/FE.',
 '''   // V174_B434_PUMP_BE: one bounded FE-driven fluid source pump.
   public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<dev.obsidiannetwork.pump.ElectricWaterPumpBlockEntity>> ELECTRIC_WATER_PUMP =
     TYPES.register("electric_water_pump",()->new BlockEntityType(
       dev.obsidiannetwork.pump.ElectricWaterPumpBlockEntity::new,
       new Block[]{(Block)ObsidianNetwork.ELECTRIC_WATER_PUMP.get()}));
   // V174_REACTOR_CONTROLLER_BE: only the controller owns runtime fuel/FE.''')
java("pump/ElectricWaterPumpBlock.java",r'''package dev.obsidiannetwork.pump;
import com.mojang.serialization.MapCodec;
import dev.obsidiannetwork.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.SimpleMenuProvider;
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

/** B434_PUMP_CONTROL: one speed-upgrade GUI and liquid/FE status. */
public final class ElectricWaterPumpBlock extends BaseEntityBlock {
 private static final MapCodec<ElectricWaterPumpBlock> CODEC=simpleCodec(ElectricWaterPumpBlock::new);
 public ElectricWaterPumpBlock(Properties p){super(p);}
 @Override protected MapCodec<? extends BaseEntityBlock> codec(){return CODEC;}
 @Override public RenderShape getRenderShape(BlockState s){return RenderShape.MODEL;}
 @Nullable @Override public BlockEntity newBlockEntity(BlockPos p,BlockState s){
  return new ElectricWaterPumpBlockEntity(p,s);
 }
 @Override public <T extends BlockEntity> BlockEntityTicker<T> getTicker(
   Level l,BlockState s,BlockEntityType<T> type){
  return l.isClientSide()?null:createTickerHelper(type,ModBlockEntities.ELECTRIC_WATER_PUMP.get(),
    ElectricWaterPumpBlockEntity::tick);
 }
 private InteractionResult open(Level l,BlockPos pos,Player user){
  if(l.isClientSide())return InteractionResult.SUCCESS;
  if(!(user instanceof ServerPlayer sp)
     ||!(l.getBlockEntity(pos) instanceof ElectricWaterPumpBlockEntity be))
   return InteractionResult.PASS;
  if(user.isShiftKeyDown())sp.sendSystemMessage(Component.literal(be.status()));
  else sp.openMenu(new SimpleMenuProvider((id,inv,p)->new ElectricWaterPumpMenu(id,inv,be),
     Component.literal(be.status())));
  return InteractionResult.SUCCESS;
 }
 @Override protected InteractionResult useWithoutItem(BlockState s,Level l,BlockPos pos,
    Player user,BlockHitResult hit){return open(l,pos,user);}
 @Override protected InteractionResult useItemOn(ItemStack stack,BlockState s,Level l,BlockPos pos,
    Player user,net.minecraft.world.InteractionHand hand,BlockHitResult hit){
  return hand==net.minecraft.world.InteractionHand.MAIN_HAND?open(l,pos,user):InteractionResult.PASS;
 }
}
''')
java("pump/ElectricWaterPumpMenu.java",r'''package dev.obsidiannetwork.pump;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;

/** One real speed-upgrade input, no fake extractable storage in empty cells. */
public final class ElectricWaterPumpMenu extends ChestMenu {
 private final ElectricWaterPumpBlockEntity pump;
 public ElectricWaterPumpMenu(int id,Inventory inv,ElectricWaterPumpBlockEntity be){
  super(MenuType.GENERIC_9x3,id,inv,be,3);
  pump=be;
  slots.set(0,new Slot(be,0,80,35){
   @Override public boolean mayPlace(ItemStack item){return ElectricWaterPumpBlockEntity.isSpeed(item);}
  });
  for(int i=1;i<27;i++){
   final int slot=i;
   slots.set(i,new Slot(be,slot,8+(i%9)*18,18+(i/9)*18){
    @Override public boolean mayPlace(ItemStack item){return false;}
    @Override public boolean mayPickup(Player p){return false;}
   });
  }
 }
 @Override public boolean stillValid(Player p){return pump.stillValid(p);}
}
''')
java("pump/ElectricWaterPumpBlockEntity.java",r'''package dev.obsidiannetwork.pump;
import dev.obsidiannetwork.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Container;
import net.minecraft.world.Containers;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.tags.FluidTags;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/** B434_PUMP: 1-17 buckets per 20 ticks, 200 FE/bucket, 32 bucket tank.
 * Only adjacent loaded infinite/source water is accepted, server-side.
 */
public final class ElectricWaterPumpBlockEntity extends BlockEntity implements Container {
 private static final long MAX_FE=2_000_000L;
 private static final int MAX_WATER=32_000;
 private long energy=0L;
 private int water=0;
 private ItemStack speed=ItemStack.EMPTY;
 private boolean drawing=false;
 public ElectricWaterPumpBlockEntity(BlockPos p,BlockState s){
  super(ModBlockEntities.ELECTRIC_WATER_PUMP.get(),p,s);
 }
 public static boolean isSpeed(ItemStack stack){
  if(stack.isEmpty())return false;
  var name=BuiltInRegistries.ITEM.getKey(stack.getItem());
  return name!=null&&"obsidiannetwork".equals(name.getNamespace())
       &&name.getPath().contains("speed_upgrade");
 }
 private int speedLevel(){return isSpeed(speed)?Math.min(16,speed.getCount()):0;}
 public String status(){return "Electric Water Pump | "+energy+" FE | "+water+" mB | Speed "+speedLevel();}
 private static boolean hasSource(ServerLevel world,BlockPos here){
  for(Direction side:Direction.values()){
   BlockPos at=here.relative(side);
   if(!world.hasChunkAt(at))continue;
   FluidState fluid=world.getFluidState(at);
   if(fluid.is(FluidTags.WATER)&&fluid.isSource())return true;
  }
  return false;
 }
 public static void tick(Level level,BlockPos pos,BlockState state,ElectricWaterPumpBlockEntity be){
  if(!(level instanceof ServerLevel world)||world.getGameTime()%20L!=0L)return;
  if(be.energy<200L||be.water>=MAX_WATER){be.drawing=false;return;}
  if(!hasSource(world,pos)){be.drawing=false;return;}
  int batches=Math.min(1+be.speedLevel(),(MAX_WATER-be.water)/1000);
  batches=(int)Math.min((long)batches,be.energy/200L);
  if(batches<=0){be.drawing=false;return;}
  be.energy-=200L*batches;
  be.water+=1000*batches;
  be.drawing=true;
  be.setChanged();
 }
 private final net.neoforged.neoforge.transfer.transaction.SnapshotJournal<Long> energyJournal =
   new net.neoforged.neoforge.transfer.transaction.SnapshotJournal<>() {
    @Override protected Long createSnapshot(){return energy;}
    @Override protected void revertToSnapshot(Long old){energy=old;}
    @Override protected void onRootCommit(Long old){if(old!=energy)setChanged();}
   };
 private final net.neoforged.neoforge.transfer.energy.EnergyHandler energyPort =
   new net.neoforged.neoforge.transfer.energy.EnergyHandler(){
    @Override public long getAmountAsLong(){return energy;}
    @Override public long getCapacityAsLong(){return MAX_FE;}
    @Override public int insert(int n,net.neoforged.neoforge.transfer.transaction.TransactionContext tx){
     if(n<=0)return 0;
     int accepted=(int)Math.min((long)n,MAX_FE-energy);
     if(accepted>0){energyJournal.updateSnapshots(tx);energy+=accepted;}
     return accepted;
    }
    @Override public int extract(int n,net.neoforged.neoforge.transfer.transaction.TransactionContext tx){return 0;}
   };
 public net.neoforged.neoforge.transfer.energy.EnergyHandler energyPort(){return energyPort;}
 private final net.neoforged.neoforge.transfer.transaction.SnapshotJournal<Integer> waterJournal =
   new net.neoforged.neoforge.transfer.transaction.SnapshotJournal<>() {
    @Override protected Integer createSnapshot(){return water;}
    @Override protected void revertToSnapshot(Integer old){water=old;}
    @Override protected void onRootCommit(Integer old){if(old!=water)setChanged();}
   };
 private final net.neoforged.neoforge.transfer.ResourceHandler<
   net.neoforged.neoforge.transfer.fluid.FluidResource> fluidPort =
   new net.neoforged.neoforge.transfer.ResourceHandler<>() {
    private net.neoforged.neoforge.transfer.fluid.FluidResource waterResource(){
     return net.neoforged.neoforge.transfer.fluid.FluidResource.of(net.minecraft.world.level.material.Fluids.WATER);
    }
    @Override public int size(){return 1;}
    @Override public net.neoforged.neoforge.transfer.fluid.FluidResource getResource(int i){
     java.util.Objects.checkIndex(i,1);
     return water>0?waterResource():net.neoforged.neoforge.transfer.fluid.FluidResource.EMPTY;
    }
    @Override public long getAmountAsLong(int i){java.util.Objects.checkIndex(i,1);return water;}
    @Override public boolean isValid(int i,net.neoforged.neoforge.transfer.fluid.FluidResource r){
     java.util.Objects.checkIndex(i,1);return waterResource().equals(r);
    }
    @Override public long getCapacityAsLong(int i,net.neoforged.neoforge.transfer.fluid.FluidResource r){
     java.util.Objects.checkIndex(i,1);return r.isEmpty()||isValid(i,r)?MAX_WATER:0L;
    }
    @Override public int insert(int i,net.neoforged.neoforge.transfer.fluid.FluidResource r,int n,
      net.neoforged.neoforge.transfer.transaction.TransactionContext tx){
     java.util.Objects.checkIndex(i,1);return 0; // output-only.
    }
    @Override public int extract(int i,net.neoforged.neoforge.transfer.fluid.FluidResource r,int n,
      net.neoforged.neoforge.transfer.transaction.TransactionContext tx){
     java.util.Objects.checkIndex(i,1);
     if(n<=0||!isValid(i,r))return 0;
     int sent=Math.min(n,water);
     if(sent>0){waterJournal.updateSnapshots(tx);water-=sent;}
     return sent;
    }
   };
 public net.neoforged.neoforge.transfer.ResourceHandler<
   net.neoforged.neoforge.transfer.fluid.FluidResource> fluidPort(){return fluidPort;}
 public net.neoforged.neoforge.transfer.ResourceHandler<
   net.neoforged.neoforge.transfer.item.ItemResource> upgradePort(){
  return net.neoforged.neoforge.transfer.item.VanillaContainerWrapper.of(this);
 }
 @Override protected void saveAdditional(ValueOutput out){
  super.saveAdditional(out);
  out.putLong("pumpEnergy",energy);out.putInt("pumpWater",water);
  if(!speed.isEmpty())out.store("pumpSpeed",ItemStack.CODEC,speed);
 }
 @Override protected void loadAdditional(ValueInput in){
  super.loadAdditional(in);
  energy=Math.max(0L,Math.min(MAX_FE,in.getLongOr("pumpEnergy",0L)));
  water=Math.max(0,Math.min(MAX_WATER,in.getIntOr("pumpWater",0)));
  speed=in.read("pumpSpeed",ItemStack.CODEC).orElse(ItemStack.EMPTY);
  if(!isSpeed(speed))speed=ItemStack.EMPTY;
  drawing=false;
 }
 @Override public void preRemoveSideEffects(BlockPos p,BlockState s){
  if(level instanceof ServerLevel world&&!speed.isEmpty())
   Containers.dropItemStack(world,p.getX()+.5,p.getY()+.5,p.getZ()+.5,speed.copy());
  super.preRemoveSideEffects(p,s);
 }
 @Override public int getContainerSize(){return 27;}
 @Override public boolean isEmpty(){return speed.isEmpty();}
 @Override public ItemStack getItem(int i){return i==0?speed:ItemStack.EMPTY;}
 @Override public ItemStack removeItem(int i,int count){
  if(i!=0||count<=0)return ItemStack.EMPTY;
  ItemStack removed=speed.split(count);setChanged();return removed;
 }
 @Override public ItemStack removeItemNoUpdate(int i){
  if(i!=0)return ItemStack.EMPTY;
  ItemStack old=speed.copy();speed=ItemStack.EMPTY;setChanged();return old;
 }
 @Override public void setItem(int i,ItemStack stack){
  if(i==0&&(stack.isEmpty()||isSpeed(stack))){speed=stack.copy();setChanged();}
 }
 @Override public boolean canPlaceItem(int i,ItemStack stack){return i==0&&isSpeed(stack);}
 @Override public boolean stillValid(Player p){
  return !isRemoved()&&p.distanceToSqr(worldPosition.getX()+.5,worldPosition.getY()+.5,worldPosition.getZ()+.5)<=64D;
 }
 @Override public void clearContent(){speed=ItemStack.EMPTY;setChanged();}
}
''')
java("pump/ElectricWaterPumpCapabilities.java",r'''package dev.obsidiannetwork.pump;
import dev.obsidiannetwork.registry.ModBlockEntities;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.capabilities.RegisterCapabilitiesEvent;
@EventBusSubscriber(modid="obsidiannetwork")
public final class ElectricWaterPumpCapabilities {
 private ElectricWaterPumpCapabilities(){}
 @SubscribeEvent public static void register(RegisterCapabilitiesEvent e){
  e.registerBlockEntity(Capabilities.Energy.BLOCK,ModBlockEntities.ELECTRIC_WATER_PUMP.get(),
    (pump,side)->pump.energyPort());
  e.registerBlockEntity(Capabilities.Fluid.BLOCK,ModBlockEntities.ELECTRIC_WATER_PUMP.get(),
    (pump,side)->pump.fluidPort());
  e.registerBlockEntity(Capabilities.Item.BLOCK,ModBlockEntities.ELECTRIC_WATER_PUMP.get(),
    (pump,side)->pump.upgradePort());
 }
}
''')
emit("assets/obsidiannetwork/blockstates/electric_water_pump.json",{"variants":{"":{"model":"obsidiannetwork:block/electric_water_pump"}}})
emit("assets/obsidiannetwork/models/block/electric_water_pump.json",
     {"parent":"minecraft:block/cube_all","textures":{"all":"minecraft:block/prismarine_bricks"}})
emit("assets/obsidiannetwork/items/electric_water_pump.json",
     {"model":{"type":"minecraft:model","model":"obsidiannetwork:block/electric_water_pump"}})
emit("data/obsidiannetwork/loot_table/blocks/electric_water_pump.json",
     {"type":"minecraft:block","pools":[{"rolls":1,"entries":[{"type":"minecraft:item","name":"obsidiannetwork:electric_water_pump"}]}]})
emit("data/obsidiannetwork/recipe/electric_water_pump.json",
     {"type":"minecraft:crafting_shaped","category":"misc","pattern":["IRI","BEB","IRI"],
      "key":{"I":"minecraft:iron_ingot","R":"minecraft:redstone_block","B":"minecraft:bucket","E":"minecraft:ender_pearl"},
      "result":{"id":"obsidiannetwork:electric_water_pump","count":1}})
for lang,label in (("de_de","Elektrische Wasserpumpe"),("en_us","Electric Water Pump")):
 p=R/f"assets/obsidiannetwork/lang/{lang}.json";obj=json.loads(p.read_text(encoding="utf-8"))
 assert "block.obsidiannetwork.electric_water_pump" not in obj
 obj["block.obsidiannetwork.electric_water_pump"]=label
 p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
p=R/"data/minecraft/tags/block/mineable/pickaxe.json"
tag=json.loads(p.read_text(encoding="utf-8"))
tag["values"].append("obsidiannetwork:electric_water_pump")
p.write_text(json.dumps(tag,indent=2)+"\n",encoding="utf-8")
print("V174_ELECTRIC_WATER_PUMP_434_PASS: FE, real source, speed 1-17, transactional water output")
