#!/usr/bin/env python3
"""v1.7.6 central Power Monitor + independent Reactor/Powerbank switches.

A network's *loaded* cable topology authorizes the visible list and all switch
actions server-side. No arbitrary client target is trusted. Do not force-load
chunks, and do not auto-discover devices in another player's cable network.
"""
import os,json
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])
def edit(path,old,new):
 p=J/path;s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("V176_POWER_TERMINAL_DRIFT",path,old[:110],s.count(old))
 p.write_text(s.replace(old,new,1),encoding="utf-8")
def add(path,src):
 p=J/path;p.parent.mkdir(parents=True,exist_ok=True)
 assert not p.exists(),("V176_POWER_TERMINAL_DUPLICATE",path)
 p.write_text(src,encoding="utf-8")
def asset(path,d):
 p=R/path;p.parent.mkdir(parents=True,exist_ok=True)
 assert not p.exists(),("V176_POWER_TERMINAL_ASSET_DUPLICATE",path)
 p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

edit("ObsidianNetwork.java",
 '   public static final DeferredBlock<dev.obsidiannetwork.reactor.ReactorPortBlock> REACTOR_NETWORK_PORT =',
 '''   public static final DeferredBlock<dev.obsidiannetwork.power.V176PowerTerminalBlock> V176_POWER_TERMINAL =
       BLOCKS.registerBlock("power_terminal",dev.obsidiannetwork.power.V176PowerTerminalBlock::new,
         p -> p.mapColor(MapColor.METAL).strength(3.5F,9.0F).requiresCorrectToolForDrops());
   public static final DeferredItem<BlockItem> V176_POWER_TERMINAL_ITEM =
       ITEMS.registerSimpleBlockItem("power_terminal",V176_POWER_TERMINAL);
   public static final DeferredBlock<dev.obsidiannetwork.reactor.ReactorPortBlock> REACTOR_NETWORK_PORT =''')
edit("ObsidianNetwork.java",
 "            output.accept((ItemLike)REACTOR_NETWORK_PORT_ITEM.get());",
 "            output.accept((ItemLike)REACTOR_NETWORK_PORT_ITEM.get());\n"+
 "            output.accept((ItemLike)V176_POWER_TERMINAL_ITEM.get());")
edit("registry/ModBlockEntities.java",
 "   // V174_REACTOR_CONTROLLER_BE: only the controller owns runtime fuel/FE.",
 '''   public static final DeferredHolder<BlockEntityType<?>,BlockEntityType<dev.obsidiannetwork.power.V176PowerTerminalBlockEntity>> V176_POWER_TERMINAL =
     TYPES.register("power_terminal",()->new BlockEntityType(
       dev.obsidiannetwork.power.V176PowerTerminalBlockEntity::new,
       new Block[]{(Block)ObsidianNetwork.V176_POWER_TERMINAL.get()}));
   // V174_REACTOR_CONTROLLER_BE: only the controller owns runtime fuel/FE.''')

add("power/V176PowerNetworkGraph.java",'''package dev.obsidiannetwork.power;

import dev.obsidiannetwork.reactor.ReactorPortBlockEntity;
import dev.obsidiannetwork.powerbank.PowerbankBlockEntity;
import dev.obsidiannetwork.powerbank.PowerbankBlock;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.level.ServerLevel;
import java.nio.charset.StandardCharsets;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.HashMap;
import java.util.List;
import java.util.Set;
import java.util.Map;
import java.util.UUID;

/** Loaded-only traversal. Same live connectivity authorizes both UI and clicks. */
public final class V176PowerNetworkGraph {
 private V176PowerNetworkGraph(){}
 private static final int MAX_NODES=16_384;
 private static final int MAX_DEVICES=512;
 private static final Set<String> CARRIERS=Set.of(
   "network_cable","conduit_bundle","power_terminal",
   "reactor_network_port","powerbank_network_port");
 private static String path(ServerLevel level,BlockPos at){
  if(!level.hasChunkAt(at))return "";
  var id=BuiltInRegistries.BLOCK.getKey(level.getBlockState(at).getBlock());
  return id.getNamespace().equals("obsidiannetwork")?id.getPath():"";
 }
 public record Scan(String network,List<V176PowerMonitorRules.Device> devices,
                    Map<BlockPos,BlockPos> controllers,boolean truncated){}
 public static Scan scan(ServerLevel world,BlockPos terminal){
  String network=world.dimension().toString()+"/"+terminal.asLong();
  if(!path(world,terminal).equals("power_terminal"))
   return new Scan(network,List.of(),Map.of(),false);
  var todo=new ArrayDeque<BlockPos>();todo.add(terminal);
  var visited=new HashSet<BlockPos>();
  var controllers=new HashMap<BlockPos,BlockPos>();
  var items=new ArrayList<V176PowerMonitorRules.Device>();
  var seenDevices=new HashSet<BlockPos>();
  boolean truncated=false;
  while(!todo.isEmpty()){
   if(visited.size()>=MAX_NODES){truncated=true;break;}
   BlockPos next=todo.removeFirst();
   if(!visited.add(next))continue;
   String name=path(world,next);
   if(!CARRIERS.contains(name))continue;
   if(name.equals("reactor_network_port")
       && world.getBlockEntity(next) instanceof ReactorPortBlockEntity port){
    var controller=port.xsxNetworkController();
    if(controller!=null&&controller.xsxNetworkFormed()
       &&seenDevices.add(controller.getBlockPos())){
     BlockPos cp=controller.getBlockPos();
     controllers.put(next,cp);
     var device=new V176PowerMonitorRules.Device(
       UUID.nameUUIDFromBytes(("reactor:"+world.dimension()+":"+cp.asLong())
            .getBytes(StandardCharsets.UTF_8)),
       network,V176PowerMonitorRules.DeviceType.REACTOR,"Reactor "+cp.toShortString(),
       world.dimension().toString(),cp.asLong(),true,true,
       controller.xsxNetworkEnabled(),controller.xsxNetworkStoredFe(),
       controller.xsxNetworkCapacityFe(),controller.xsxNetworkInputFePerTick(),
       controller.xsxNetworkOutputFePerTick());
     items.add(device);
    }
   }else if(name.equals("powerbank_network_port")
       && world.getBlockEntity(next) instanceof PowerbankBlockEntity port){
    var controller=port.xsxNetworkController();
    if(controller!=null&&controller.mode()==PowerbankBlock.Mode.CONTROLLER
       &&controller.xsxNetworkFormed()&&seenDevices.add(controller.getBlockPos())){
     BlockPos cp=controller.getBlockPos();
     controllers.put(next,cp);
     items.add(new V176PowerMonitorRules.Device(
       UUID.nameUUIDFromBytes(("powerbank:"+world.dimension()+":"+cp.asLong())
            .getBytes(StandardCharsets.UTF_8)),
       network,V176PowerMonitorRules.DeviceType.POWERBANK,"Powerbank "+cp.toShortString(),
       world.dimension().toString(),cp.asLong(),true,true,
       controller.xsxNetworkEnabled(),controller.xsxNetworkStoredFe(),
       controller.xsxNetworkCapacityFe(),controller.xsxNetworkInputFePerTick(),
       controller.xsxNetworkOutputFePerTick()));
    }
   }
   if(items.size()>=MAX_DEVICES){truncated=true;break;}
   for(Direction face:Direction.values()){
    BlockPos adjoining=next.relative(face);
    if(!visited.contains(adjoining)&&world.hasChunkAt(adjoining)
        &&CARRIERS.contains(path(world,adjoining)))todo.add(adjoining);
   }
  }
  return new Scan(network,V176PowerMonitorRules.visible(network,items),
          Map.copyOf(controllers),truncated);
 }
 public static boolean toggle(ServerLevel world,BlockPos terminal,BlockPos target,
                              net.minecraft.server.level.ServerPlayer player){
  if(player.distanceToSqr(terminal.getX()+.5,terminal.getY()+.5,terminal.getZ()+.5)>64D)
   return false;
  Scan snapshot=scan(world,terminal);
  V176PowerMonitorRules.Device device=null;
  for(var entry:snapshot.devices())if(entry.position()==target.asLong())device=entry;
  if(!V176PowerMonitorRules.canToggle(snapshot.network(),device,!player.isSpectator()))
   return false;
  if(world.getBlockEntity(target) instanceof dev.obsidiannetwork.reactor.ReactorControllerBlockEntity reactor){
   reactor.xsxNetworkSetEnabled(!reactor.xsxNetworkEnabled());
   return true;
  }
  if(world.getBlockEntity(target) instanceof PowerbankBlockEntity bank
     &&bank.mode()==PowerbankBlock.Mode.CONTROLLER){
   bank.xsxNetworkSetEnabled(!bank.xsxNetworkEnabled());
   return true;
  }
  return false;
 }
}
''')

add("power/V176PowerTerminalBlock.java",'''package dev.obsidiannetwork.power;
import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.level.block.entity.BlockEntityType;
import org.jetbrains.annotations.Nullable;
public final class V176PowerTerminalBlock extends BaseEntityBlock {
 private static final MapCodec<V176PowerTerminalBlock> CODEC=simpleCodec(V176PowerTerminalBlock::new);
 public V176PowerTerminalBlock(Properties props){super(props);}
 @Override protected MapCodec<? extends BaseEntityBlock> codec(){return CODEC;}
 @Override public RenderShape getRenderShape(BlockState s){return RenderShape.MODEL;}
 @Nullable @Override public BlockEntity newBlockEntity(BlockPos pos,BlockState state){
  return new V176PowerTerminalBlockEntity(pos,state);
 }
 @Nullable @Override public <T extends BlockEntity> BlockEntityTicker<T> getTicker(
      Level l,BlockState s,BlockEntityType<T> t){
  return l.isClientSide()?null:createTickerHelper(t,
       dev.obsidiannetwork.registry.ModBlockEntities.V176_POWER_TERMINAL.get(),
       V176PowerTerminalBlockEntity::serverTick);
 }
 private InteractionResult open(Level l,BlockPos pos,Player player){
  if(player instanceof ServerPlayer p && l.getBlockEntity(pos) instanceof V176PowerTerminalBlockEntity){
   p.openMenu(new SimpleMenuProvider((id,inv,u)->
       ChestMenu.threeRows(id,inv),
       Component.literal("xSxLabs Power Monitor @"+pos.getX()+","+pos.getY()+","+pos.getZ())));
  }
  return InteractionResult.SUCCESS;
 }
 @Override protected InteractionResult useWithoutItem(BlockState s,Level l,BlockPos p,Player u,BlockHitResult hit){
  return open(l,p,u);
 }
 @Override protected InteractionResult useItemOn(ItemStack item,BlockState s,Level l,
     BlockPos p,Player u,InteractionHand h,BlockHitResult hit){
  return h==InteractionHand.MAIN_HAND?open(l,p,u):InteractionResult.PASS;
 }
}
''')

add("power/V176PowerTerminalBlockEntity.java",'''package dev.obsidiannetwork.power;
import dev.obsidiannetwork.registry.ModBlockEntities;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.core.HolderLookup;

public final class V176PowerTerminalBlockEntity extends BlockEntity {
 private List<V176PowerMonitorRules.Device> devices=List.of();
 private boolean truncated;
 private int revision;
 public V176PowerTerminalBlockEntity(BlockPos p,BlockState s){
  super(ModBlockEntities.V176_POWER_TERMINAL.get(),p,s);
 }
 public List<V176PowerMonitorRules.Device> devices(){return devices;}
 public boolean truncated(){return truncated;}
 @Override protected void saveAdditional(ValueOutput out){
  super.saveAdditional(out);
  out.putInt("xsxDeviceCount",devices.size());
  out.putBoolean("xsxTruncated",truncated);
  out.putInt("xsxRevision",revision);
  for(int i=0;i<devices.size();i++){
   var d=devices.get(i);String k="xsxD"+i;
   out.putString(k+"id",d.id().toString());
   out.putString(k+"net",d.network());
   out.putInt(k+"type",d.type().ordinal());
   out.putString(k+"label",d.label());
   out.putString(k+"dim",d.dimension());
   out.putLong(k+"pos",d.position());
   out.putBoolean(k+"online",d.online());
   out.putBoolean(k+"formed",d.formed());
   out.putBoolean(k+"enabled",d.enabled());
   out.putLong(k+"amount",d.storedFe());
   out.putLong(k+"capacity",d.capacityFe());
   out.putLong(k+"in",d.inputFePerTick());
   out.putLong(k+"out",d.outputFePerTick());
  }
 }
 @Override protected void loadAdditional(ValueInput in){
  super.loadAdditional(in);
  truncated=in.getBooleanOr("xsxTruncated",false);
  revision=in.getIntOr("xsxRevision",0);
  var found=new ArrayList<V176PowerMonitorRules.Device>();
  int length=Math.min(512,Math.max(0,in.getIntOr("xsxDeviceCount",0)));
  for(int i=0;i<length;i++)try{
   String k="xsxD"+i;
   int type=in.getIntOr(k+"type",-1);
   if(type<0||type>1)continue;
   found.add(new V176PowerMonitorRules.Device(
    java.util.UUID.fromString(in.getStringOr(k+"id","")),
    in.getStringOr(k+"net",""),V176PowerMonitorRules.DeviceType.values()[type],
    in.getStringOr(k+"label",""),in.getStringOr(k+"dim",""),
    in.getLongOr(k+"pos",0),in.getBooleanOr(k+"online",false),
    in.getBooleanOr(k+"formed",false),in.getBooleanOr(k+"enabled",false),
    in.getLongOr(k+"amount",0),in.getLongOr(k+"capacity",0),
    in.getLongOr(k+"in",0),in.getLongOr(k+"out",0)));
  }catch(RuntimeException ignored){}
  devices=List.copyOf(found);
 }
 @Override public CompoundTag getUpdateTag(HolderLookup.Provider lookup){
  return saveWithoutMetadata(lookup);
 }
 @Override public Packet<ClientGamePacketListener> getUpdatePacket(){
  return ClientboundBlockEntityDataPacket.create(this);
 }
 public static void serverTick(Level level,BlockPos at,BlockState state,V176PowerTerminalBlockEntity be){
  if(!(level instanceof ServerLevel world)||world.getGameTime()%20L!=0)return;
  var result=V176PowerNetworkGraph.scan(world,at);
  if(!result.devices().equals(be.devices)||result.truncated()!=be.truncated){
   be.devices=result.devices();
   be.truncated=result.truncated();
   be.revision++;
   be.setChanged();
   world.sendBlockUpdated(at,state,state,3);
  }
 }
}
''')

add("power/V176PowerMonitorCommands.java",'''package dev.obsidiannetwork.power;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;

/** CLI bridge used ONLY by a real Power Terminal GUI, verified on server. */
@EventBusSubscriber(modid="obsidiannetwork")
public final class V176PowerMonitorCommands {
 private V176PowerMonitorCommands(){}
 @SubscribeEvent public static void register(RegisterCommandsEvent event){
  event.getDispatcher().register(Commands.literal("powerterminal")
    .then(Commands.literal("toggle")
      .then(Commands.argument("tx",IntegerArgumentType.integer())
       .then(Commands.argument("ty",IntegerArgumentType.integer())
        .then(Commands.argument("tz",IntegerArgumentType.integer())
         .then(Commands.argument("dx",IntegerArgumentType.integer())
          .then(Commands.argument("dy",IntegerArgumentType.integer())
           .then(Commands.argument("dz",IntegerArgumentType.integer())
             .executes(c->{
                var p=c.getSource().getPlayerOrException();
                if(!(p.level() instanceof ServerLevel world))return 0;
                BlockPos terminal=new BlockPos(IntegerArgumentType.getInteger(c,"tx"),
                  IntegerArgumentType.getInteger(c,"ty"),IntegerArgumentType.getInteger(c,"tz"));
                BlockPos device=new BlockPos(IntegerArgumentType.getInteger(c,"dx"),
                  IntegerArgumentType.getInteger(c,"dy"),IntegerArgumentType.getInteger(c,"dz"));
                boolean done=V176PowerNetworkGraph.toggle(world,terminal,device,p);
                if(!done)p.displayClientMessage(Component.literal(
                      "Power Monitor: device unavailable or not on this network"),true);
                return done?1:0;
             })))))))));
 }
}
''')

asset("assets/obsidiannetwork/blockstates/power_terminal.json",
      {"variants":{"":{"model":"obsidiannetwork:block/power_terminal"}}})
asset("assets/obsidiannetwork/models/block/power_terminal.json",
      {"parent":"minecraft:block/cube_all",
       "textures":{"all":"minecraft:block/respawn_anchor_side0"}})
asset("assets/obsidiannetwork/items/power_terminal.json",
      {"model":{"type":"minecraft:model","model":"obsidiannetwork:block/power_terminal"}})
asset("data/obsidiannetwork/loot_table/blocks/power_terminal.json",
      {"type":"minecraft:block","pools":[{"rolls":1,
        "entries":[{"type":"minecraft:item","name":"obsidiannetwork:power_terminal"}]}]})
asset("data/obsidiannetwork/recipe/power_terminal.json",
      {"type":"minecraft:crafting_shaped","pattern":["GEG","RCR","GEG"],
       "key":{"G":"minecraft:gold_ingot","E":"minecraft:ender_pearl",
         "R":"minecraft:redstone_block","C":"minecraft:comparator"},
       "result":{"id":"obsidiannetwork:power_terminal","count":1}})
for lang,name in (("de_de","Power Monitor"),("en_us","Power Monitor")):
 p=R/f"assets/obsidiannetwork/lang/{lang}.json"
 t=json.loads(p.read_text(encoding="utf-8"))
 assert "block.obsidiannetwork.power_terminal" not in t
 t["block.obsidiannetwork.power_terminal"]=name
 p.write_text(json.dumps(t,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("V176_POWER_MONITOR_WORLD_BLOCK_NETWORK_GRAPH_GUI_BACKEND_SWITCHES_PASS")
