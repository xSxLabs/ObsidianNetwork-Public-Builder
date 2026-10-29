#!/usr/bin/env python3
"""v1.7.4 reactor phase 1: actual multiblock blocks, structural validator, fuel/coolant/FE runtime.

Known phase-1 limitations: controller FE output only; automated fluid/item ports
and dedicated styled UI are follow-up features, not claimed as complete.
No changes to the immutable 1.7.3 v12 Build419 source or registry IDs.
"""
import json, os
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])
def rewrite(rel,old,new):
    p=J/rel
    s=p.read_text(encoding="utf-8")
    assert s.count(old)==1,("V174_REACTOR_SOURCE_DRIFT",rel,s.count(old),old[:100])
    p.write_text(s.replace(old,new,1),encoding="utf-8")
def add(rel,source):
    p=J/rel
    p.parent.mkdir(parents=True,exist_ok=True)
    assert not p.exists(),("V174_REACTOR_JAVA_COLLISION",str(p))
    p.write_text(source,encoding="utf-8")
def emit(rel,payload):
    p=R/rel
    p.parent.mkdir(parents=True,exist_ok=True)
    assert not p.exists(),("V174_REACTOR_RESOURCE_COLLISION",str(p))
    p.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

parts=[
 ("REACTOR_CASING","reactor_casing","net.minecraft.world.level.block.Block",False),
 ("REACTOR_GLASS","reactor_glass","net.minecraft.world.level.block.Block",False),
 ("REACTOR_FUEL_ASSEMBLY","reactor_fuel_assembly","net.minecraft.world.level.block.Block",False),
 ("REACTOR_ITEM_PORT","reactor_item_port","net.minecraft.world.level.block.Block",False),
 ("REACTOR_FLUID_PORT","reactor_fluid_port","net.minecraft.world.level.block.Block",False),
 ("REACTOR_POWER_PORT","reactor_power_port","net.minecraft.world.level.block.Block",False),
 ("REACTOR_CONTROLLER","reactor_controller","dev.obsidiannetwork.reactor.ReactorControllerBlock",True)
]
registration=[]
for field,name,clazz,controller in parts:
    cons="dev.obsidiannetwork.reactor.ReactorControllerBlock::new" if controller else "net.minecraft.world.level.block.Block::new"
    registration += [
        f"    public static final DeferredBlock<{clazz}> {field} =",
        f'        BLOCKS.registerBlock("{name}", {cons},',
        "            p -> p.mapColor(MapColor.METAL).strength(3.5F,9.0F).requiresCorrectToolForDrops());",
        f"    public static final DeferredItem<BlockItem> {field}_ITEM =",
        f'        ITEMS.registerSimpleBlockItem("{name}", {field});'
    ]
rewrite("ObsidianNetwork.java",
        "    // V174_URANIUM_FUEL_CHAIN: ore / raw material / ingot / reactor fuel rod.",
        "    // V174_REACTOR_CORE_427: add-only seven-part 5..64 multiblock.\n"+"\n".join(registration)+"\n"+
        "    // V174_URANIUM_FUEL_CHAIN: ore / raw material / ingot / reactor fuel rod.")
creative="            output.accept((ItemLike)URANIUM_ROD.get());"
rewrite("ObsidianNetwork.java",creative,creative+"\n"+"\n".join(
    f"            output.accept((ItemLike){field}_ITEM.get());" for field,_,_,_ in parts))
rewrite("registry/ModBlockEntities.java",
        "   public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<dev.obsidiannetwork.blockentity.NetworkDeviceBlockEntity>> NETWORK_DEVICE =",
        """   // V174_REACTOR_CONTROLLER_BE: only the controller owns runtime fuel/FE.
   public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<dev.obsidiannetwork.reactor.ReactorControllerBlockEntity>> REACTOR_CONTROLLER =
       TYPES.register("reactor_controller",()->new BlockEntityType(
         dev.obsidiannetwork.reactor.ReactorControllerBlockEntity::new,
         new Block[]{(Block)ObsidianNetwork.REACTOR_CONTROLLER.get()}));
   public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<dev.obsidiannetwork.blockentity.NetworkDeviceBlockEntity>> NETWORK_DEVICE =""")

add("reactor/ReactorStructure.java",r'''package dev.obsidiannetwork.reactor;

import dev.obsidiannetwork.ObsidianNetwork;
import java.util.ArrayDeque;
import java.util.HashSet;
import java.util.Set;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.state.BlockState;

/** V174_REACTOR_GEOMETRY: bounded, chunk-safe shell flood fill and solid interior check.
 * Only called on manual formation and infrequently during running state.
 * Cannot load missing chunks. 64^3 is a HARD validation cap, not a tick loop.
 */
public final class ReactorStructure {
 private ReactorStructure(){}
 public static final int MIN=5,MAX=64;
 public record Result(boolean valid,String reason,int width,int height,int depth,int rods) {
  public static Result fail(String why){return new Result(false,why,0,0,0,0);}
 }
 public static boolean shell(BlockState s){
  return s.is(ObsidianNetwork.REACTOR_CASING.get())
    ||s.is(ObsidianNetwork.REACTOR_GLASS.get())
    ||s.is(ObsidianNetwork.REACTOR_CONTROLLER.get())
    ||s.is(ObsidianNetwork.REACTOR_ITEM_PORT.get())
    ||s.is(ObsidianNetwork.REACTOR_FLUID_PORT.get())
    ||s.is(ObsidianNetwork.REACTOR_POWER_PORT.get());
 }
 public static Result inspect(ServerLevel world,BlockPos controller){
  if(!world.hasChunkAt(controller)||!world.getBlockState(controller).is(ObsidianNetwork.REACTOR_CONTROLLER.get()))
   return Result.fail("Controller not loaded");
  ArrayDeque<BlockPos> open=new ArrayDeque<>();
  Set<BlockPos> visited=new HashSet<>();
  open.add(controller);
  int minX=controller.getX(),maxX=minX,minY=controller.getY(),maxY=minY,minZ=controller.getZ(),maxZ=minZ;
  int controllerCount=0,energyPorts=0,itemPorts=0,fluidPorts=0;
  final int shellLimit=6*MAX*MAX;
  Direction[] sides=Direction.values();
  while(!open.isEmpty()){
   BlockPos at=open.removeFirst();
   if(!visited.add(at))continue;
   if(visited.size()>shellLimit)return Result.fail("Oversized/connected shells");
   if(!world.hasChunkAt(at))return Result.fail("Unloaded reactor shell");
   BlockState block=world.getBlockState(at);
   if(!shell(block))continue;
   minX=Math.min(minX,at.getX()); maxX=Math.max(maxX,at.getX());
   minY=Math.min(minY,at.getY()); maxY=Math.max(maxY,at.getY());
   minZ=Math.min(minZ,at.getZ()); maxZ=Math.max(maxZ,at.getZ());
   if(maxX-minX+1>MAX||maxY-minY+1>MAX||maxZ-minZ+1>MAX)
    return Result.fail("Reactor dimension above 64");
   if(block.is(ObsidianNetwork.REACTOR_CONTROLLER.get()))controllerCount++;
   if(block.is(ObsidianNetwork.REACTOR_POWER_PORT.get()))energyPorts++;
   if(block.is(ObsidianNetwork.REACTOR_ITEM_PORT.get()))itemPorts++;
   if(block.is(ObsidianNetwork.REACTOR_FLUID_PORT.get()))fluidPorts++;
   for(Direction d:sides){
    BlockPos next=at.relative(d);
    if(visited.contains(next))continue;
    // Do not touch unloaded chunks; never force-load an area for formation.
    if(!world.hasChunkAt(next))continue;
    if(shell(world.getBlockState(next)))open.addLast(next);
   }
  }
  int sx=maxX-minX+1,sy=maxY-minY+1,sz=maxZ-minZ+1;
  if(sx<MIN||sy<MIN||sz<MIN)return Result.fail("Minimum reactor: 5x5x5");
  if(controllerCount!=1)return Result.fail("Exactly one reactor controller is required");
  if(energyPorts<1||itemPorts<1||fluidPorts<1)
   return Result.fail("Require item, fluid and power port");
  int rods=0;
  // Every exterior cell must be casing/glass/controller/port, with an air or
  // fuel-assembly interior. A single missing frame piece rejects formation.
  for(int x=minX;x<=maxX;x++)for(int y=minY;y<=maxY;y++)for(int z=minZ;z<=maxZ;z++){
   BlockPos p=new BlockPos(x,y,z);
   if(!world.hasChunkAt(p))return Result.fail("Reactor chunks not loaded");
   BlockState state=world.getBlockState(p);
   boolean outer=x==minX||x==maxX||y==minY||y==maxY||z==minZ||z==maxZ;
   if(outer){
    if(!shell(state))return Result.fail("Exterior has gaps at "+p.toShortString());
   }else if(state.is(ObsidianNetwork.REACTOR_FUEL_ASSEMBLY.get())){
    rods++;
   }else if(!state.isAir()){
    return Result.fail("Interior obstruction at "+p.toShortString());
   }
  }
  if(rods<1)return Result.fail("Place at least one interior fuel assembly");
  return new Result(true,"FORMED",sx,sy,sz,rods);
 }
}
''')

add("reactor/ReactorControllerBlock.java",r'''package dev.obsidiannetwork.reactor;

import com.mojang.serialization.MapCodec;
import dev.obsidiannetwork.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
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

/** V174_REACTOR_CONTROLLER: shift-right-click to validate, ordinary use opens real inventory. */
public final class ReactorControllerBlock extends BaseEntityBlock {
 private static final MapCodec<ReactorControllerBlock> CODEC=simpleCodec(ReactorControllerBlock::new);
 public ReactorControllerBlock(Properties p){super(p);}
 @Override protected MapCodec<? extends BaseEntityBlock> codec(){return CODEC;}
 @Override public RenderShape getRenderShape(BlockState s){return RenderShape.MODEL;}
 @Nullable @Override public BlockEntity newBlockEntity(BlockPos p,BlockState s){
  return new ReactorControllerBlockEntity(p,s);
 }
 @Override public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level l,BlockState s,BlockEntityType<T> t){
  return l.isClientSide()?null:createTickerHelper(t,ModBlockEntities.REACTOR_CONTROLLER.get(),
     ReactorControllerBlockEntity::tick);
 }
 private InteractionResult open(Level world,BlockPos p,Player player){
  if(!(world instanceof ServerLevel sl))return InteractionResult.SUCCESS;
  if(!(player instanceof ServerPlayer sp)||!(world.getBlockEntity(p) instanceof ReactorControllerBlockEntity be))
   return InteractionResult.PASS;
  if(player.isShiftKeyDown()){
   var formed=be.revalidate(sl);
   sp.sendSystemMessage(Component.literal("xSxLabs Reactor: "+formed.reason()+
      (formed.valid()?" | "+formed.width()+"x"+formed.height()+"x"+formed.depth()+" | rods "+formed.rods():"")));
  }else{
   sp.openMenu(new SimpleMenuProvider((id,inventory,p2)->new ReactorMenu(id,inventory,be),
      Component.literal("Reactor | "+be.status())));
  }
  return InteractionResult.SUCCESS;
 }
 @Override protected InteractionResult useWithoutItem(BlockState s,Level l,BlockPos p,Player u,BlockHitResult hit){
  return open(l,p,u);
 }
 @Override protected InteractionResult useItemOn(ItemStack stack,BlockState s,Level l,BlockPos p,Player u,
     net.minecraft.world.InteractionHand hand,BlockHitResult hit){
  return hand==net.minecraft.world.InteractionHand.MAIN_HAND?open(l,p,u):InteractionResult.PASS;
 }
}
''')

add("reactor/ReactorMenu.java",r'''package dev.obsidiannetwork.reactor;

import dev.obsidiannetwork.ObsidianNetwork;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

/** Real synchronized vanilla 9x3 container: fuel, water buckets and empty returns. */
public final class ReactorMenu extends ChestMenu {
 private final ReactorControllerBlockEntity reactor;
 public ReactorMenu(int id,Inventory inventory,ReactorControllerBlockEntity block){
  super(MenuType.GENERIC_9x3,id,inventory,block,3);
  reactor=block;
  slots.set(0,new Slot(block,0,26,35){
   @Override public boolean mayPlace(ItemStack s){return s.is(ObsidianNetwork.URANIUM_ROD.get());}
  });
  slots.set(1,new Slot(block,1,62,35){
   @Override public boolean mayPlace(ItemStack s){return s.is(Items.WATER_BUCKET);}
  });
  slots.set(2,new Slot(block,2,98,35){
   @Override public boolean mayPlace(ItemStack s){return false;}
  });
  for(int i=3;i<27;i++){
   final int index=i;
   slots.set(i,new Slot(block,index,8+(i%9)*18,18+(i/9)*18){
    @Override public boolean mayPlace(ItemStack s){return false;}
    @Override public boolean mayPickup(Player p){return false;}
   });
  }
 }
 @Override public boolean stillValid(Player p){return reactor.stillValid(p);}
}
''')

add("reactor/ReactorControllerBlockEntity.java",r'''package dev.obsidiannetwork.reactor;

import dev.obsidiannetwork.ObsidianNetwork;
import dev.obsidiannetwork.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Container;
import net.minecraft.world.Containers;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/** V174_REACTOR_RUNTIME: server authority, persisted fuel/water/FE, no ambient FE. */
public final class ReactorControllerBlockEntity extends BlockEntity implements Container {
 private ItemStack rod=ItemStack.EMPTY,waterBucket=ItemStack.EMPTY,empties=ItemStack.EMPTY;
 private long storedFe=0L;
 private int waterMb=0,fuelTicks=0,rodAssemblies=0;
 private boolean formed=false;
 private String status="UNFORMED";
 public static final long FE_CAPACITY=1_000_000_000L;
 public static final int WATER_CAPACITY=16_000;
 public ReactorControllerBlockEntity(BlockPos p,BlockState s){
  super(ModBlockEntities.REACTOR_CONTROLLER.get(),p,s);
 }
 public String status(){return status+" | "+storedFe+" FE | "+waterMb+" mB water";}
 public ReactorStructure.Result revalidate(ServerLevel sl){
  ReactorStructure.Result r=ReactorStructure.inspect(sl,worldPosition);
  formed=r.valid();
  rodAssemblies=formed?r.rods():0;
  status=r.reason();
  setChanged();
  return r;
 }
 private final net.neoforged.neoforge.transfer.transaction.SnapshotJournal<Long> energyJournal =
  new net.neoforged.neoforge.transfer.transaction.SnapshotJournal<>() {
   @Override protected Long createSnapshot(){return storedFe;}
   @Override protected void revertToSnapshot(Long before){storedFe=before;}
   @Override protected void onRootCommit(Long before){if(before!=storedFe)setChanged();}
  };
 private final net.neoforged.neoforge.transfer.energy.EnergyHandler energyPort =
  new net.neoforged.neoforge.transfer.energy.EnergyHandler() {
   @Override public long getAmountAsLong(){return storedFe;}
   @Override public long getCapacityAsLong(){return FE_CAPACITY;}
   @Override public int insert(int offered,net.neoforged.neoforge.transfer.transaction.TransactionContext t){return 0;}
   @Override public int extract(int demand,net.neoforged.neoforge.transfer.transaction.TransactionContext t){
    if(demand<=0||!formed)return 0;
    int paid=(int)Math.min((long)demand,storedFe);
    if(paid>0){energyJournal.updateSnapshots(t);storedFe-=paid;}
    return paid;
   }
  };
 public net.neoforged.neoforge.transfer.energy.EnergyHandler energyPort(){return energyPort;}
 public static void tick(Level level,BlockPos pos,BlockState state,ReactorControllerBlockEntity be){
  if(!(level instanceof ServerLevel sl)||sl.getGameTime()%20L!=0L)return;
  // Full revalidation is deliberately infrequent, NOT on every block/entity tick.
  if(be.formed&&sl.getGameTime()%1200L==0L){be.revalidate(sl);if(!be.formed)return;}
  if(!be.formed)return;
  if(be.waterMb<=WATER_CAPACITY-1000&&be.waterBucket.is(Items.WATER_BUCKET)
      &&(be.empties.isEmpty() || (be.empties.is(Items.BUCKET)&&be.empties.getCount()<64))){
   be.waterBucket.shrink(1);
   if(be.waterBucket.isEmpty())be.waterBucket=ItemStack.EMPTY;
   if(be.empties.isEmpty())be.empties=new ItemStack(Items.BUCKET);
   else be.empties.grow(1);
   be.waterMb+=1000;
   be.setChanged();
  }
  if(be.fuelTicks==0&&!be.rod.isEmpty()&&be.rod.is(ObsidianNetwork.URANIUM_ROD.get())){
   be.rod.shrink(1);
   if(be.rod.isEmpty())be.rod=ItemStack.EMPTY;
   be.fuelTicks=12_000;
   be.setChanged();
  }
  if(be.fuelTicks<=0||be.waterMb<20){be.status=be.fuelTicks<=0?"NO FUEL":"NO COOLANT";return;}
  long generated=Math.min(FE_CAPACITY-be.storedFe,(long)be.rodAssemblies*120L*20L);
  if(generated<=0){be.status="ENERGY FULL";return;}
  // Fuel is consumed only on power-producing steps; coolant matters.
  be.storedFe+=generated;
  be.waterMb-=20;
  be.fuelTicks=Math.max(0,be.fuelTicks-20);
  be.status="RUNNING";
  be.setChanged();
 }
 @Override protected void saveAdditional(ValueOutput out){
  super.saveAdditional(out);
  if(!rod.isEmpty())out.store("reactorRod",ItemStack.CODEC,rod);
  if(!waterBucket.isEmpty())out.store("reactorWater",ItemStack.CODEC,waterBucket);
  if(!empties.isEmpty())out.store("reactorEmpty",ItemStack.CODEC,empties);
  out.putLong("reactorFE",storedFe);out.putInt("reactorWaterMb",waterMb);
  out.putInt("reactorFuelTicks",fuelTicks);out.putInt("reactorAssemblies",rodAssemblies);
  out.putBoolean("reactorFormed",formed);
 }
 @Override protected void loadAdditional(ValueInput in){
  super.loadAdditional(in);
  rod=in.read("reactorRod",ItemStack.CODEC).orElse(ItemStack.EMPTY);
  waterBucket=in.read("reactorWater",ItemStack.CODEC).orElse(ItemStack.EMPTY);
  empties=in.read("reactorEmpty",ItemStack.CODEC).orElse(ItemStack.EMPTY);
  storedFe=Math.max(0L,Math.min(FE_CAPACITY,in.getLongOr("reactorFE",0L)));
  waterMb=Math.max(0,Math.min(WATER_CAPACITY,in.getIntOr("reactorWaterMb",0)));
  fuelTicks=Math.max(0,in.getIntOr("reactorFuelTicks",0));
  rodAssemblies=Math.max(0,in.getIntOr("reactorAssemblies",0));
  // Revalidate before generation after a restart; never trust stale formed flag.
  formed=false;status="REVALIDATE (SHIFT + RIGHT CLICK)";
 }
 @Override public void preRemoveSideEffects(BlockPos p,BlockState s){
  if(level instanceof ServerLevel sl){
   for(ItemStack stack:new ItemStack[]{rod,waterBucket,empties})
    if(!stack.isEmpty())Containers.dropItemStack(sl,p.getX()+.5,p.getY()+.5,p.getZ()+.5,stack.copy());
  }
  super.preRemoveSideEffects(p,s);
 }
 @Override public int getContainerSize(){return 27;}
 @Override public boolean isEmpty(){return rod.isEmpty()&&waterBucket.isEmpty()&&empties.isEmpty();}
 @Override public ItemStack getItem(int slot){return slot==0?rod:slot==1?waterBucket:slot==2?empties:ItemStack.EMPTY;}
 @Override public ItemStack removeItem(int slot,int count){
  ItemStack s=getItem(slot);if(s.isEmpty()||count<=0)return ItemStack.EMPTY;
  ItemStack removed=s.split(count);if(s.isEmpty())setItem(slot,ItemStack.EMPTY);
  setChanged();return removed;
 }
 @Override public ItemStack removeItemNoUpdate(int slot){
  ItemStack s=getItem(slot),copy=s.copy();
  if(slot==0)rod=ItemStack.EMPTY;
  if(slot==1)waterBucket=ItemStack.EMPTY;
  if(slot==2)empties=ItemStack.EMPTY;
  setChanged();return copy;
 }
 @Override public void setItem(int slot,ItemStack s){
  if(slot==0&&(s.isEmpty()||s.is(ObsidianNetwork.URANIUM_ROD.get())))rod=s.copy();
  else if(slot==1&&(s.isEmpty()||s.is(Items.WATER_BUCKET)))waterBucket=s.copy();
  else if(slot==2&&(s.isEmpty()||s.is(Items.BUCKET)))empties=s.copy();
  setChanged();
 }
 @Override public boolean canPlaceItem(int slot,ItemStack s){
  return slot==0?s.is(ObsidianNetwork.URANIUM_ROD.get()):slot==1&&s.is(Items.WATER_BUCKET);
 }
 @Override public boolean stillValid(Player p){
  return !isRemoved()&&p.distanceToSqr(worldPosition.getX()+.5,worldPosition.getY()+.5,worldPosition.getZ()+.5)<=64D;
 }
 @Override public void clearContent(){rod=waterBucket=empties=ItemStack.EMPTY;setChanged();}
}
''')

add("reactor/ReactorEnergyCapabilities.java",r'''package dev.obsidiannetwork.reactor;

import dev.obsidiannetwork.registry.ModBlockEntities;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.capabilities.RegisterCapabilitiesEvent;

/** Phase 1: real cable-compatible transactional FE EXTRACT on the controller face.
 * Power-port externalization will follow, and is NOT silently emulated here.
 */
@EventBusSubscriber(modid="obsidiannetwork")
public final class ReactorEnergyCapabilities {
 private ReactorEnergyCapabilities(){}
 @SubscribeEvent public static void register(RegisterCapabilitiesEvent event){
  event.registerBlockEntity(Capabilities.Energy.BLOCK,ModBlockEntities.REACTOR_CONTROLLER.get(),
    (controller,side)->controller.energyPort());
 }
}
''')

texture={
 "reactor_casing":"minecraft:block/polished_blackstone",
 "reactor_glass":"minecraft:block/tinted_glass",
 "reactor_fuel_assembly":"minecraft:block/emerald_block",
 "reactor_controller":"minecraft:block/respawn_anchor_side0",
 "reactor_item_port":"minecraft:block/hopper_outside",
 "reactor_fluid_port":"minecraft:block/prismarine_bricks",
 "reactor_power_port":"minecraft:block/copper_block",
}
for field,name,clazz,controller in parts:
    emit(f"assets/obsidiannetwork/blockstates/{name}.json",{"variants":{"":{"model":f"obsidiannetwork:block/{name}"}}})
    emit(f"assets/obsidiannetwork/models/block/{name}.json",{"parent":"minecraft:block/cube_all","textures":{"all":texture[name]}})
    emit(f"assets/obsidiannetwork/items/{name}.json",
        {"model":{"type":"minecraft:model","model":f"obsidiannetwork:block/{name}"}})
    emit(f"data/obsidiannetwork/loot_table/blocks/{name}.json",{
         "type":"minecraft:block","pools":[{"rolls":1,"entries":[{"type":"minecraft:item","name":"obsidiannetwork:"+name}]}]})
    for rel in ("data/minecraft/tags/block/mineable/pickaxe.json",):
        path=R/rel
        obj=json.loads(path.read_text(encoding="utf-8"))
        if "obsidiannetwork:"+name not in obj["values"]:obj["values"].append("obsidiannetwork:"+name)
        path.write_text(json.dumps(obj,indent=2)+"\n",encoding="utf-8")
    # component costs and recipes are phase-1 survival-accessible; casing yields 4.
    emit(f"data/obsidiannetwork/recipe/{name}.json",{
        "type":"minecraft:crafting_shaped","category":"misc",
        "pattern":["III","IRI","III"],
        "key":{"I":"minecraft:iron_ingot",
               "R":"obsidiannetwork:uranium_rod" if name in ("reactor_controller","reactor_fuel_assembly") else "minecraft:stone"},
        "result":{"id":"obsidiannetwork:"+name,"count":4 if name=="reactor_casing" else 1}})
for lang,names in {
    "en_us":["Reactor Casing","Reactor Glass","Fuel Assembly","Reactor Item Port","Reactor Water Port","Reactor Energy Port","Reactor Controller"],
    "de_de":["Reaktorhülle","Reaktorglas","Brennstab-Einsatz","Reaktor-Itemport","Reaktor-Wasserport","Reaktor-Energieport","Reaktorsteuerung"]
}.items():
    p=R/f"assets/obsidiannetwork/lang/{lang}.json"
    obj=json.loads(p.read_text(encoding="utf-8"))
    for (_,name,_,_),label in zip(parts,names):
        key="block.obsidiannetwork."+name
        assert key not in obj,key
        obj[key]=label
    p.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("V174_REACTOR_CORE_427_PASS: 7 blocks, world-safe geometry, controller inventory, FE + fuel/water tick")
