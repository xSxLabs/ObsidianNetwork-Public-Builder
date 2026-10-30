#!/usr/bin/env python3
"""v1.7.4: real item/fluid/FE reactor ports (NeoForge 26.1 resource transfer).
Apply after B431. No per-transfer multiblock scans or chunk loads.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def rep(path,old,new):
 p=J/path;s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("B433_DRIFT",path,s.count(old),old[:80])
 p.write_text(s.replace(old,new,1),encoding="utf-8")
def add(path,code):
 p=J/path;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists(),str(p)
 p.write_text(code,encoding="utf-8")

for kind in ("item","fluid","power"):
 field="REACTOR_"+kind.upper()+"_PORT";name="reactor_"+kind+"_port"
 rep("ObsidianNetwork.java",f"DeferredBlock<net.minecraft.world.level.block.Block> {field} =",
     f"DeferredBlock<dev.obsidiannetwork.reactor.ReactorPortBlock> {field} =")
 rep("ObsidianNetwork.java",f'BLOCKS.registerBlock("{name}", net.minecraft.world.level.block.Block::new,',
     f'BLOCKS.registerBlock("{name}", p -> new dev.obsidiannetwork.reactor.ReactorPortBlock(p,dev.obsidiannetwork.reactor.ReactorPortBlock.Mode.{kind.upper()}),')
rep("registry/ModBlockEntities.java",
    "   // V174_REACTOR_CONTROLLER_BE: only the controller owns runtime fuel/FE.",
    """   // V174_B433_REACTOR_PORT_ENTITY: one BE type for the three IO port blocks.
   public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<dev.obsidiannetwork.reactor.ReactorPortBlockEntity>> REACTOR_PORT =
       TYPES.register("reactor_port",()->new BlockEntityType(
         dev.obsidiannetwork.reactor.ReactorPortBlockEntity::new,
         new Block[]{(Block)ObsidianNetwork.REACTOR_ITEM_PORT.get(),
                     (Block)ObsidianNetwork.REACTOR_FLUID_PORT.get(),
                     (Block)ObsidianNetwork.REACTOR_POWER_PORT.get()}));
   // V174_REACTOR_CONTROLLER_BE: only the controller owns runtime fuel/FE.""")

rep("reactor/ReactorStructure.java",
    "int width,int height,int depth,int rods) {",
    "int width,int height,int depth,int rods,java.util.List<BlockPos> ports) {")
rep("reactor/ReactorStructure.java","new Result(false,why,0,0,0,0);",
    "new Result(false,why,0,0,0,0,java.util.List.of());")
rep("reactor/ReactorStructure.java","  int rods=0;\n  // Every exterior cell",
    "  int rods=0;\n  java.util.List<BlockPos> ports=new java.util.ArrayList<>();\n  // Every exterior cell")
rep("reactor/ReactorStructure.java",
    'if(!shell(state))return Result.fail("Exterior has gaps at "+p.toShortString());',
    '''if(!shell(state))return Result.fail("Exterior has gaps at "+p.toShortString());
    if(state.is(ObsidianNetwork.REACTOR_ITEM_PORT.get())
     ||state.is(ObsidianNetwork.REACTOR_FLUID_PORT.get())
     ||state.is(ObsidianNetwork.REACTOR_POWER_PORT.get()))ports.add(p);''')
rep("reactor/ReactorStructure.java",
    'new Result(true,"FORMED",sx,sy,sz,rods);',
    'new Result(true,"FORMED",sx,sy,sz,rods,java.util.List.copyOf(ports));')

rep("reactor/ReactorControllerBlockEntity.java",
    " private boolean formed=false;\n private boolean restorePending=false;",
    """ private boolean formed=false;
 // V174_B433_APPROVED_PORTS: reset on every successful/failed validation.
 private final java.util.Set<Long> approvedPorts=new java.util.HashSet<>();
 private boolean restorePending=false;""")
rep("reactor/ReactorControllerBlockEntity.java",
    "  formed=r.valid();\n  rodAssemblies=formed?r.rods():0;",
    """  formed=r.valid();
  approvedPorts.clear();
  rodAssemblies=formed?r.rods():0;
  if(formed)for(BlockPos at:r.ports()){
   approvedPorts.add(at.asLong());
   if(sl.getBlockEntity(at) instanceof ReactorPortBlockEntity port)port.linkTo(worldPosition);
  }""")
rep("reactor/ReactorControllerBlockEntity.java",
    ' public String status(){return status+" | "+storedFe+" FE | "+waterMb+" mB water";}',
    ''' public String status(){return status+" | "+storedFe+" FE | "+waterMb+" mB water";}
 public boolean allowsPort(BlockPos at){return formed&&approvedPorts.contains(at.asLong());}''')
rep("reactor/ReactorControllerBlockEntity.java",
    " public net.neoforged.neoforge.transfer.energy.EnergyHandler energyPort(){return energyPort;}",
    r''' public net.neoforged.neoforge.transfer.energy.EnergyHandler energyPort(){return energyPort;}

 // B433 fuel item / water bucket: existing server-authoritative slots.
 private final net.neoforged.neoforge.transfer.ResourceHandler<
    net.neoforged.neoforge.transfer.item.ItemResource> inventoryHandler =
    net.neoforged.neoforge.transfer.item.VanillaContainerWrapper.of(this);
 public net.neoforged.neoforge.transfer.ResourceHandler<
    net.neoforged.neoforge.transfer.item.ItemResource> inventoryPort(){return inventoryHandler;}

 // B433 coolant uses the exact waterMb consumed by the power generation tick.
 private final net.neoforged.neoforge.transfer.transaction.SnapshotJournal<Integer> coolantJournal =
   new net.neoforged.neoforge.transfer.transaction.SnapshotJournal<>() {
    @Override protected Integer createSnapshot(){return waterMb;}
    @Override protected void revertToSnapshot(Integer previous){waterMb=previous;}
    @Override protected void onRootCommit(Integer previous){if(previous!=waterMb)setChanged();}
   };
 private final net.neoforged.neoforge.transfer.ResourceHandler<
    net.neoforged.neoforge.transfer.fluid.FluidResource> waterHandler =
   new net.neoforged.neoforge.transfer.ResourceHandler<>() {
    private net.neoforged.neoforge.transfer.fluid.FluidResource water(){
     return net.neoforged.neoforge.transfer.fluid.FluidResource.of(net.minecraft.world.level.material.Fluids.WATER);
    }
    @Override public int size(){return 1;}
    @Override public net.neoforged.neoforge.transfer.fluid.FluidResource getResource(int i){
     java.util.Objects.checkIndex(i,1);
     return waterMb==0?net.neoforged.neoforge.transfer.fluid.FluidResource.EMPTY:water();
    }
    @Override public long getAmountAsLong(int i){java.util.Objects.checkIndex(i,1);return waterMb;}
    @Override public boolean isValid(int i,net.neoforged.neoforge.transfer.fluid.FluidResource r){
     java.util.Objects.checkIndex(i,1);return water().equals(r);
    }
    @Override public long getCapacityAsLong(int i,net.neoforged.neoforge.transfer.fluid.FluidResource r){
     java.util.Objects.checkIndex(i,1);
     return r.isEmpty()||isValid(i,r)?WATER_CAPACITY:0L;
    }
    @Override public int insert(int i,net.neoforged.neoforge.transfer.fluid.FluidResource r,
        int count,net.neoforged.neoforge.transfer.transaction.TransactionContext tx){
     java.util.Objects.checkIndex(i,1);
     if(count<=0||!formed||!isValid(i,r))return 0;
     int accepted=Math.min(count,WATER_CAPACITY-waterMb);
     if(accepted>0){coolantJournal.updateSnapshots(tx);waterMb+=accepted;}
     return accepted;
    }
    @Override public int extract(int i,net.neoforged.neoforge.transfer.fluid.FluidResource r,
        int count,net.neoforged.neoforge.transfer.transaction.TransactionContext tx){
     java.util.Objects.checkIndex(i,1);return 0; // input only, reactor consumes it.
    }
   };
 public net.neoforged.neoforge.transfer.ResourceHandler<
    net.neoforged.neoforge.transfer.fluid.FluidResource> fluidPort(){return waterHandler;}''')

add("reactor/ReactorPortBlock.java",r'''package dev.obsidiannetwork.reactor;
import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import org.jetbrains.annotations.Nullable;
public final class ReactorPortBlock extends BaseEntityBlock {
 public enum Mode {ITEM,FLUID,POWER}
 private final Mode mode;
 private static final MapCodec<ReactorPortBlock> I=simpleCodec(p->new ReactorPortBlock(p,Mode.ITEM));
 private static final MapCodec<ReactorPortBlock> F=simpleCodec(p->new ReactorPortBlock(p,Mode.FLUID));
 private static final MapCodec<ReactorPortBlock> P=simpleCodec(p->new ReactorPortBlock(p,Mode.POWER));
 public ReactorPortBlock(Properties props,Mode mode){super(props);this.mode=mode;}
 public Mode mode(){return mode;}
 @Override protected MapCodec<? extends BaseEntityBlock> codec(){
  return switch(mode){case ITEM->I;case FLUID->F;case POWER->P;};
 }
 @Override public RenderShape getRenderShape(BlockState s){return RenderShape.MODEL;}
 @Nullable @Override public BlockEntity newBlockEntity(BlockPos p,BlockState s){
  return new ReactorPortBlockEntity(p,s);
 }
}
''')
add("reactor/ReactorPortBlockEntity.java",r'''package dev.obsidiannetwork.reactor;
import dev.obsidiannetwork.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/** V174_B433_NO_ORPHANS: every cached handler rechecks current controller permission. */
public final class ReactorPortBlockEntity extends BlockEntity {
 private static final long UNLINKED=Long.MIN_VALUE;
 private long linkedPos=UNLINKED;
 public ReactorPortBlockEntity(BlockPos p,BlockState s){super(ModBlockEntities.REACTOR_PORT.get(),p,s);}
 public void linkTo(BlockPos controller){
  if(linkedPos!=controller.asLong()){linkedPos=controller.asLong();setChanged();}
 }
 private ReactorControllerBlockEntity controller(){
  if(linkedPos==UNLINKED||level==null)return null;
  BlockPos pos=BlockPos.of(linkedPos);
  if(!level.hasChunkAt(pos))return null;
  if(level.getBlockEntity(pos) instanceof ReactorControllerBlockEntity be
      &&be.allowsPort(worldPosition))return be;
  return null;
 }
 private ReactorPortBlock.Mode mode(){
  return getBlockState().getBlock() instanceof ReactorPortBlock b?b.mode():ReactorPortBlock.Mode.ITEM;
 }
 private net.neoforged.neoforge.transfer.ResourceHandler<
     net.neoforged.neoforge.transfer.item.ItemResource> items(){
  ReactorControllerBlockEntity c=controller();
  return mode()==ReactorPortBlock.Mode.ITEM&&c!=null?c.inventoryPort():null;
 }
 // Stable guarded façade: caching never bypasses the live validity check.
 private final net.neoforged.neoforge.transfer.ResourceHandler<
     net.neoforged.neoforge.transfer.item.ItemResource> itemHandler =
   new net.neoforged.neoforge.transfer.ResourceHandler<>() {
    private net.neoforged.neoforge.transfer.ResourceHandler<
      net.neoforged.neoforge.transfer.item.ItemResource> h(){return items();}
    @Override public int size(){var x=h();return x==null?0:x.size();}
    @Override public net.neoforged.neoforge.transfer.item.ItemResource getResource(int i){
     var x=h();return x==null?net.neoforged.neoforge.transfer.item.ItemResource.EMPTY:x.getResource(i);
    }
    @Override public long getAmountAsLong(int i){var x=h();return x==null?0:x.getAmountAsLong(i);}
    @Override public long getCapacityAsLong(int i,net.neoforged.neoforge.transfer.item.ItemResource r){
     var x=h();return x==null?0:x.getCapacityAsLong(i,r);
    }
    @Override public boolean isValid(int i,net.neoforged.neoforge.transfer.item.ItemResource r){
     var x=h();return x!=null&&x.isValid(i,r);
    }
    @Override public int insert(int i,net.neoforged.neoforge.transfer.item.ItemResource r,int n,
       net.neoforged.neoforge.transfer.transaction.TransactionContext tx){
     var x=h();return x==null?0:x.insert(i,r,n,tx);
    }
    @Override public int extract(int i,net.neoforged.neoforge.transfer.item.ItemResource r,int n,
       net.neoforged.neoforge.transfer.transaction.TransactionContext tx){
     var x=h();return x==null?0:x.extract(i,r,n,tx);
    }
   };
 public net.neoforged.neoforge.transfer.ResourceHandler<
   net.neoforged.neoforge.transfer.item.ItemResource> itemPort(){
  return mode()==ReactorPortBlock.Mode.ITEM?itemHandler:null;
 }
 private final net.neoforged.neoforge.transfer.ResourceHandler<
   net.neoforged.neoforge.transfer.fluid.FluidResource> fluidHandler =
   new net.neoforged.neoforge.transfer.ResourceHandler<>() {
    private net.neoforged.neoforge.transfer.ResourceHandler<
     net.neoforged.neoforge.transfer.fluid.FluidResource> h(){
     var c=controller();return c==null?null:c.fluidPort();
    }
    @Override public int size(){var x=h();return x==null?0:x.size();}
    @Override public net.neoforged.neoforge.transfer.fluid.FluidResource getResource(int i){
     var x=h();return x==null?net.neoforged.neoforge.transfer.fluid.FluidResource.EMPTY:x.getResource(i);
    }
    @Override public long getAmountAsLong(int i){var x=h();return x==null?0:x.getAmountAsLong(i);}
    @Override public long getCapacityAsLong(int i,net.neoforged.neoforge.transfer.fluid.FluidResource r){
     var x=h();return x==null?0:x.getCapacityAsLong(i,r);
    }
    @Override public boolean isValid(int i,net.neoforged.neoforge.transfer.fluid.FluidResource r){
     var x=h();return x!=null&&x.isValid(i,r);
    }
    @Override public int insert(int i,net.neoforged.neoforge.transfer.fluid.FluidResource r,int n,
      net.neoforged.neoforge.transfer.transaction.TransactionContext tx){
     var x=h();return x==null?0:x.insert(i,r,n,tx);
    }
    @Override public int extract(int i,net.neoforged.neoforge.transfer.fluid.FluidResource r,int n,
      net.neoforged.neoforge.transfer.transaction.TransactionContext tx){return 0;}
   };
 public net.neoforged.neoforge.transfer.ResourceHandler<
    net.neoforged.neoforge.transfer.fluid.FluidResource> fluidPort(){
  return mode()==ReactorPortBlock.Mode.FLUID?fluidHandler:null;
 }
 private final net.neoforged.neoforge.transfer.energy.EnergyHandler powerHandler =
   new net.neoforged.neoforge.transfer.energy.EnergyHandler(){
    private net.neoforged.neoforge.transfer.energy.EnergyHandler h(){
     var c=controller();return c==null?null:c.energyPort();
    }
    @Override public long getAmountAsLong(){var x=h();return x==null?0:x.getAmountAsLong();}
    @Override public long getCapacityAsLong(){var x=h();return x==null?0:x.getCapacityAsLong();}
    @Override public int insert(int n,net.neoforged.neoforge.transfer.transaction.TransactionContext tx){return 0;}
    @Override public int extract(int n,net.neoforged.neoforge.transfer.transaction.TransactionContext tx){
     var x=h();return x==null?0:x.extract(n,tx);
    }
   };
 public net.neoforged.neoforge.transfer.energy.EnergyHandler powerPort(){
  return mode()==ReactorPortBlock.Mode.POWER?powerHandler:null;
 }
 @Override protected void saveAdditional(ValueOutput out){super.saveAdditional(out);out.putLong("reactorController",linkedPos);}
 @Override protected void loadAdditional(ValueInput in){super.loadAdditional(in);linkedPos=in.getLongOr("reactorController",UNLINKED);}
}
''')
add("reactor/ReactorPortCapabilities.java",r'''package dev.obsidiannetwork.reactor;
import dev.obsidiannetwork.registry.ModBlockEntities;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.capabilities.RegisterCapabilitiesEvent;

/** Connected reactor's item, water, and output-FE ports. */
@EventBusSubscriber(modid="obsidiannetwork")
public final class ReactorPortCapabilities {
 private ReactorPortCapabilities(){}
 @SubscribeEvent public static void register(RegisterCapabilitiesEvent event){
  event.registerBlockEntity(Capabilities.Item.BLOCK,ModBlockEntities.REACTOR_PORT.get(),
    (be,side)->be.itemPort());
  event.registerBlockEntity(Capabilities.Fluid.BLOCK,ModBlockEntities.REACTOR_PORT.get(),
    (be,side)->be.fluidPort());
  event.registerBlockEntity(Capabilities.Energy.BLOCK,ModBlockEntities.REACTOR_PORT.get(),
    (be,side)->be.powerPort());
 }
}
''')
print("V174_REACTOR_PORTS_433_PASS: FE item water NeoForge capabilities, no orphan access")
