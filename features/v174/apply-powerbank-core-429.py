#!/usr/bin/env python3
"""v1.7.4 Powerbank: real 3x3x3..12 shell, long FE capacity and transactional IO.

This is a staged feature until its full clean CI compile/game test passes.
"""
import json,os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])
def edit(rel,needle,replacement):
 p=J/rel;s=p.read_text(encoding="utf-8");assert s.count(needle)==1,(rel,needle,s.count(needle))
 p.write_text(s.replace(needle,replacement,1),encoding="utf-8")
def write(rel,s):
 p=J/rel;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists(),p;p.write_text(s,encoding="utf-8")
def resource(path,content):
 p=R/path;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists(),p
 p.write_text(json.dumps(content,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
items=[
 ("POWERBANK_CASING","powerbank_casing",None),
 ("POWERBANK_GLASS","powerbank_glass",None),
 ("POWERBANK_CONTROLLER","powerbank_controller","CONTROLLER"),
 ("POWERBANK_INPUT","powerbank_input_port","INPUT"),
 ("POWERBANK_OUTPUT","powerbank_output_port","OUTPUT")]
parts=[]
for field,name,mode in items:
 c="dev.obsidiannetwork.powerbank.PowerbankBlock" if mode else "net.minecraft.world.level.block.Block"
 maker=("p -> new "+c+"(p,dev.obsidiannetwork.powerbank.PowerbankBlock.Mode."+mode+")") if mode else "net.minecraft.world.level.block.Block::new"
 parts.extend([f"    public static final DeferredBlock<{c}> {field} =",
 f'        BLOCKS.registerBlock("{name}",{maker},',
 "            p -> p.mapColor(MapColor.METAL).strength(3.0F,9.0F).requiresCorrectToolForDrops());",
 f"    public static final DeferredItem<BlockItem> {field}_ITEM =",
 f'        ITEMS.registerSimpleBlockItem("{name}",{field});'])
edit("ObsidianNetwork.java","    // V174_REACTOR_CORE_427: add-only seven-part 5..64 multiblock.",
     "    // V174_POWERBANK_429: long-capacity multiblock with real energy ports.\n"+"\n".join(parts)+"\n"+
     "    // V174_REACTOR_CORE_427: add-only seven-part 5..64 multiblock.")
entry="            output.accept((ItemLike)REACTOR_CONTROLLER_ITEM.get());"
edit("ObsidianNetwork.java",entry,entry+"\n"+"\n".join(f"            output.accept((ItemLike){field}_ITEM.get());" for field,_,_ in items))
edit("registry/ModBlockEntities.java",
 "   // V174_REACTOR_CONTROLLER_BE: only the controller owns runtime fuel/FE.",
 """   // V174_POWERBANK_BE: controller and IO ports share one entity type.
   public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<dev.obsidiannetwork.powerbank.PowerbankBlockEntity>> POWERBANK =
       TYPES.register("powerbank",()->new BlockEntityType(
         dev.obsidiannetwork.powerbank.PowerbankBlockEntity::new,
         new Block[]{(Block)ObsidianNetwork.POWERBANK_CONTROLLER.get(),
                     (Block)ObsidianNetwork.POWERBANK_INPUT.get(),
                     (Block)ObsidianNetwork.POWERBANK_OUTPUT.get()}));
   // V174_REACTOR_CONTROLLER_BE: only the controller owns runtime fuel/FE.""")

write("powerbank/PowerbankGeometry.java",r'''package dev.obsidiannetwork.powerbank;
import dev.obsidiannetwork.ObsidianNetwork;
import java.util.*;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.state.BlockState;

/** V174_POWERBANK_GEOMETRY: closed 3x3x(3..12), any length axis, loaded chunks only. */
public final class PowerbankGeometry {
 private PowerbankGeometry(){}
 public static final long MIN_FE=10_000_000_000L,MAX_FE=100_000_000_000L;
 public record Result(boolean valid,String reason,int length,long capacity,List<BlockPos> ports) {
  public static Result fail(String why){return new Result(false,why,0,0L,List.of());}
 }
 private static boolean shell(BlockState s){
  return s.is(ObsidianNetwork.POWERBANK_CASING.get())
   ||s.is(ObsidianNetwork.POWERBANK_GLASS.get())
   ||s.is(ObsidianNetwork.POWERBANK_CONTROLLER.get())
   ||s.is(ObsidianNetwork.POWERBANK_INPUT.get())
   ||s.is(ObsidianNetwork.POWERBANK_OUTPUT.get());
 }
 public static Result inspect(ServerLevel world,BlockPos start){
  if(!world.hasChunkAt(start)||!world.getBlockState(start).is(ObsidianNetwork.POWERBANK_CONTROLLER.get()))
   return Result.fail("Controller unloaded");
  Set<BlockPos> seen=new HashSet<>();
  ArrayDeque<BlockPos> queue=new ArrayDeque<>();queue.add(start);
  int ax=start.getX(),bx=ax,ay=start.getY(),by=ay,az=start.getZ(),bz=az;
  while(!queue.isEmpty()){
   BlockPos p=queue.removeFirst();
   if(!seen.add(p))continue;
   if(seen.size()>216)return Result.fail("Oversized or touching powerbanks");
   if(!world.hasChunkAt(p))return Result.fail("Chunk unloaded");
   if(!shell(world.getBlockState(p)))continue;
   ax=Math.min(ax,p.getX());bx=Math.max(bx,p.getX());
   ay=Math.min(ay,p.getY());by=Math.max(by,p.getY());
   az=Math.min(az,p.getZ());bz=Math.max(bz,p.getZ());
   if(bx-ax+1>12||by-ay+1>12||bz-az+1>12)return Result.fail("Length above 12");
   for(Direction d:Direction.values()){
    BlockPos n=p.relative(d);
    if(!seen.contains(n)&&world.hasChunkAt(n)&&shell(world.getBlockState(n)))queue.add(n);
   }
  }
  int x=bx-ax+1,y=by-ay+1,z=bz-az+1;
  int length=Math.max(x,Math.max(y,z));
  if(length<3||length>12||((x==3?1:0)+(y==3?1:0)+(z==3?1:0))<2)
   return Result.fail("Must be 3x3x3 through 3x3x12");
  int controllers=0,inputs=0,outputs=0;
  List<BlockPos> ports=new ArrayList<>();
  for(int i=ax;i<=bx;i++)for(int j=ay;j<=by;j++)for(int k=az;k<=bz;k++){
   BlockPos p=new BlockPos(i,j,k);
   if(!world.hasChunkAt(p))return Result.fail("Required chunk not loaded");
   BlockState s=world.getBlockState(p);
   boolean outside=i==ax||i==bx||j==ay||j==by||k==az||k==bz;
   if(outside){
    if(!shell(s))return Result.fail("Shell incomplete: "+p.toShortString());
    if(s.is(ObsidianNetwork.POWERBANK_CONTROLLER.get()))controllers++;
    if(s.is(ObsidianNetwork.POWERBANK_INPUT.get())){inputs++;ports.add(p);}
    if(s.is(ObsidianNetwork.POWERBANK_OUTPUT.get())){outputs++;ports.add(p);}
   }else if(!s.isAir())return Result.fail("Interior occupied: "+p.toShortString());
  }
  if(controllers!=1||inputs<1||outputs<1)
   return Result.fail("Exactly one controller, at least one input and output");
  long capacity=MIN_FE+(long)(length-3)*10_000_000_000L;
  if(capacity>MAX_FE)return Result.fail("Invalid capacity");
  return new Result(true,"FORMED",length,capacity,List.copyOf(ports));
 }
}
''')
write("powerbank/PowerbankBlock.java",r'''package dev.obsidiannetwork.powerbank;
import com.mojang.serialization.MapCodec;
import dev.obsidiannetwork.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import org.jetbrains.annotations.Nullable;
public final class PowerbankBlock extends BaseEntityBlock {
 public enum Mode {CONTROLLER,INPUT,OUTPUT}
 private final Mode mode;
 private static final MapCodec<PowerbankBlock> C=simpleCodec(p->new PowerbankBlock(p,Mode.CONTROLLER));
 private static final MapCodec<PowerbankBlock> I=simpleCodec(p->new PowerbankBlock(p,Mode.INPUT));
 private static final MapCodec<PowerbankBlock> O=simpleCodec(p->new PowerbankBlock(p,Mode.OUTPUT));
 public PowerbankBlock(Properties p,Mode mode){super(p);this.mode=mode;}
 public Mode mode(){return mode;}
 @Override protected MapCodec<? extends BaseEntityBlock> codec(){
  return switch(mode){case CONTROLLER->C;case INPUT->I;case OUTPUT->O;};
 }
 @Override public RenderShape getRenderShape(BlockState s){return RenderShape.MODEL;}
 @Nullable @Override public BlockEntity newBlockEntity(BlockPos p,BlockState s){return new PowerbankBlockEntity(p,s);}
 private InteractionResult access(Level level,BlockPos p,Player user){
  if(!(level instanceof ServerLevel sl))return InteractionResult.SUCCESS;
  if(!(user instanceof ServerPlayer sp)||!(level.getBlockEntity(p) instanceof PowerbankBlockEntity be))
   return InteractionResult.PASS;
  if(mode==Mode.CONTROLLER&&user.isShiftKeyDown()){
   var r=be.revalidate(sl);
   sp.sendSystemMessage(Component.literal("xSxLabs Powerbank: "+r.reason()+
      (r.valid()?" | 3x3x"+r.length()+" | "+r.capacity()+" FE":"")));
  }else sp.sendSystemMessage(Component.literal("xSxLabs Powerbank: "+be.status()));
  return InteractionResult.SUCCESS;
 }
 @Override protected InteractionResult useWithoutItem(BlockState s,Level l,BlockPos p,Player u,BlockHitResult hit){return access(l,p,u);}
 @Override protected InteractionResult useItemOn(ItemStack stack,BlockState s,Level l,BlockPos p,Player u,
    net.minecraft.world.InteractionHand hand,BlockHitResult hit){
  return hand==net.minecraft.world.InteractionHand.MAIN_HAND?access(l,p,u):InteractionResult.PASS;
 }
}
''')
write("powerbank/PowerbankBlockEntity.java",r'''package dev.obsidiannetwork.powerbank;
import dev.obsidiannetwork.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/** V174_POWERBANK_FE: safe transactional FE IO, source of truth is controller BE. */
public final class PowerbankBlockEntity extends BlockEntity {
 private static final long NONE=Long.MIN_VALUE;
 private static final int MAX_IO=1_000_000;
 private long linked=NONE,amount=0L,capacity=0L;
 private boolean formed=false;
 public PowerbankBlockEntity(BlockPos p,BlockState s){super(ModBlockEntities.POWERBANK.get(),p,s);}
 public PowerbankBlock.Mode mode(){
  return getBlockState().getBlock() instanceof PowerbankBlock b?b.mode():PowerbankBlock.Mode.CONTROLLER;
 }
 private PowerbankBlockEntity controller(){
  if(mode()==PowerbankBlock.Mode.CONTROLLER)return this;
  if(linked==NONE||level==null)return null;
  BlockPos p=BlockPos.of(linked);
  if(!level.hasChunkAt(p))return null;
  if(level.getBlockEntity(p) instanceof PowerbankBlockEntity be
      &&be.mode()==PowerbankBlock.Mode.CONTROLLER&&be.formed)return be;
  return null;
 }
 public String status(){
  var bank=controller();
  return bank==null?"UNLINKED":(bank.formed?"ONLINE ":"UNFORMED ")+bank.amount+" / "+bank.capacity+" FE";
 }
 public PowerbankGeometry.Result revalidate(ServerLevel sl){
  if(mode()!=PowerbankBlock.Mode.CONTROLLER)return PowerbankGeometry.Result.fail("Not controller");
  var result=PowerbankGeometry.inspect(sl,worldPosition);
  if(result.valid()&&amount>result.capacity())
   result=PowerbankGeometry.Result.fail("Cannot resize below stored FE");
  formed=result.valid();
  if(formed){
   capacity=result.capacity();
   for(BlockPos p:result.ports()){
    if(sl.getBlockEntity(p) instanceof PowerbankBlockEntity port){
     port.linked=worldPosition.asLong();port.setChanged();
    }
   }
  }
  setChanged();
  return result;
 }
 private final net.neoforged.neoforge.transfer.transaction.SnapshotJournal<Long> journal=
   new net.neoforged.neoforge.transfer.transaction.SnapshotJournal<>() {
    @Override protected Long createSnapshot(){return amount;}
    @Override protected void revertToSnapshot(Long before){amount=before;}
    @Override protected void onRootCommit(Long before){if(amount!=before)setChanged();}
   };
 private final net.neoforged.neoforge.transfer.energy.EnergyHandler energyPort=
   new net.neoforged.neoforge.transfer.energy.EnergyHandler() {
    @Override public long getAmountAsLong(){
     var bank=controller();return bank==null?0L:bank.amount;
    }
    @Override public long getCapacityAsLong(){
     var bank=controller();return bank==null?0L:bank.capacity;
    }
    @Override public int insert(int offered,net.neoforged.neoforge.transfer.transaction.TransactionContext tx){
     if(mode()!=PowerbankBlock.Mode.INPUT||offered<=0)return 0;
     PowerbankBlockEntity b=controller();
     if(b==null||!b.formed)return 0;
     int taken=(int)Math.min(Math.min((long)offered,MAX_IO),b.capacity-b.amount);
     if(taken>0){b.journal.updateSnapshots(tx);b.amount+=taken;}
     return taken;
    }
    @Override public int extract(int demand,net.neoforged.neoforge.transfer.transaction.TransactionContext tx){
     if(mode()!=PowerbankBlock.Mode.OUTPUT||demand<=0)return 0;
     PowerbankBlockEntity b=controller();
     if(b==null||!b.formed)return 0;
     int taken=(int)Math.min(Math.min((long)demand,MAX_IO),b.amount);
     if(taken>0){b.journal.updateSnapshots(tx);b.amount-=taken;}
     return taken;
    }
   };
 public net.neoforged.neoforge.transfer.energy.EnergyHandler energyPort(){
  return mode()==PowerbankBlock.Mode.CONTROLLER?null:energyPort;
 }
 @Override protected void saveAdditional(ValueOutput out){
  super.saveAdditional(out);
  out.putLong("bankOwner",linked);
  if(mode()==PowerbankBlock.Mode.CONTROLLER){
   out.putLong("bankAmount",amount);out.putLong("bankCapacity",capacity);
  }
 }
 @Override protected void loadAdditional(ValueInput in){
  super.loadAdditional(in);
  linked=in.getLongOr("bankOwner",NONE);
  amount=Math.max(0L,Math.min(PowerbankGeometry.MAX_FE,in.getLongOr("bankAmount",0L)));
  capacity=Math.max(0L,Math.min(PowerbankGeometry.MAX_FE,in.getLongOr("bankCapacity",0L)));
  formed=false; // Must revalidate after restart, no stale port access.
 }
}
''')
write("powerbank/PowerbankCapabilities.java",r'''package dev.obsidiannetwork.powerbank;
import dev.obsidiannetwork.registry.ModBlockEntities;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.capabilities.RegisterCapabilitiesEvent;
@EventBusSubscriber(modid="obsidiannetwork")
public final class PowerbankCapabilities {
 private PowerbankCapabilities(){}
 @SubscribeEvent public static void register(RegisterCapabilitiesEvent event){
  event.registerBlockEntity(Capabilities.Energy.BLOCK,ModBlockEntities.POWERBANK.get(),
     (port,side)->port.energyPort());
 }
}
''')
textures={
"powerbank_casing":"minecraft:block/deepslate_tiles",
"powerbank_glass":"minecraft:block/light_blue_stained_glass",
"powerbank_controller":"minecraft:block/sea_lantern",
"powerbank_input_port":"minecraft:block/redstone_block",
"powerbank_output_port":"minecraft:block/copper_block"}
for field,name,mode in items:
 resource(f"assets/obsidiannetwork/blockstates/{name}.json",{"variants":{"":{"model":f"obsidiannetwork:block/{name}"}}})
 resource(f"assets/obsidiannetwork/models/block/{name}.json",{"parent":"minecraft:block/cube_all","textures":{"all":textures[name]}})
 resource(f"assets/obsidiannetwork/items/{name}.json",{"model":{"type":"minecraft:model","model":f"obsidiannetwork:block/{name}"}})
 resource(f"data/obsidiannetwork/loot_table/blocks/{name}.json",{
  "type":"minecraft:block","pools":[{"rolls":1,"entries":[{"type":"minecraft:item","name":"obsidiannetwork:"+name}]}]})
 t=R/"data/minecraft/tags/block/mineable/pickaxe.json"
 tags=json.loads(t.read_text(encoding="utf-8"));assert "obsidiannetwork:"+name not in tags["values"]
 tags["values"].append("obsidiannetwork:"+name);t.write_text(json.dumps(tags,indent=2)+"\n",encoding="utf-8")
 resource(f"data/obsidiannetwork/recipe/{name}.json",{
  "type":"minecraft:crafting_shaped","category":"misc","pattern":["III","CRC","III"],
  "key":{"I":"minecraft:iron_ingot","C":"obsidiannetwork:reactor_casing",
         "R":"minecraft:diamond" if mode=="CONTROLLER" else "minecraft:redstone"},
  "result":{"id":"obsidiannetwork:"+name,"count":4 if name=="powerbank_casing" else 1}})
for lang,labels in {
 "en_us":["Powerbank Casing","Powerbank Glass","Powerbank Controller","Powerbank Input Port","Powerbank Output Port"],
 "de_de":["Powerbank-Hülle","Powerbank-Glas","Powerbank-Steuerung","Powerbank-Eingang","Powerbank-Ausgang"]
}.items():
 p=R/f"assets/obsidiannetwork/lang/{lang}.json"
 obj=json.loads(p.read_text(encoding="utf-8"))
 for (_,name,_),label in zip(items,labels):
  key="block.obsidiannetwork."+name;assert key not in obj
  obj[key]=label
 p.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("V174_POWERBANK_429_PASS: genuine 3x3x3..12 multiblock, 10..100b FE, transactional port IO")
