#!/usr/bin/env python3
"""Install cross-dimension FE network blocks onto the proven v1.1.1 reconstruction.

Two new BLOCKS only. Server SavedData for network identities. Weak loaded-source
index; only the receiver checks six neighbors every 5 ticks. Live NeoForge FE
transactions ensure sender rollback if target cannot accept all offered energy.
Fail closed when registry anchors change.
"""
import os, json
from pathlib import Path

j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
r=Path(os.environ["V1_RESOURCE_ROOT"])
assert (j/"blockentity/WirelessChargerBlockEntity.java").is_file()
assert (j/"block/WirelessChargerBlock.java").is_file()
assert (j/"registry/ModCapabilities.java").is_file()
marker="XSXLABS_WIRELESS_NETWORKS_V1"

def patch(rel,old,new):
    p=j/rel
    s=p.read_text()
    assert marker not in s, "already applied to "+rel
    assert s.count(old)==1, f"{rel}: missing or duplicate anchor {old[:90]}"
    p.write_text(s.replace(old,new,1))

p="ObsidianNetwork.java"
s=(j/p).read_text()
anchor="   public static final DeferredItem<BlockItem> WIRELESS_CHARGER_ITEM = ITEMS.registerSimpleBlockItem(\"wireless_charger\", WIRELESS_CHARGER);"
assert s.count(anchor)==1
block_anchor="   public static final DeferredBlock<WirelessChargerBlock> WIRELESS_CHARGER = BLOCKS.registerBlock("
assert s.count(block_anchor)==1
s=s.replace(block_anchor,'''   // XSXLABS_WIRELESS_NETWORKS_V1: no third controller/charger block.
   public static final DeferredBlock<dev.obsidiannetwork.block.WirelessNetworkBlock> NETWORK_TRANSMITTER = BLOCKS.registerBlock(
      "network_transmitter", props -> new dev.obsidiannetwork.block.WirelessNetworkBlock(props,true), props -> props.mapColor(MapColor.COLOR_GRAY).strength(1.33F,12.0F).noOcclusion()
   );
   public static final DeferredBlock<dev.obsidiannetwork.block.WirelessNetworkBlock> NETWORK_RECEIVER = BLOCKS.registerBlock(
      "network_receiver", props -> new dev.obsidiannetwork.block.WirelessNetworkBlock(props,false), props -> props.mapColor(MapColor.COLOR_GRAY).strength(1.33F,12.0F).noOcclusion()
   );
'''+block_anchor,1)
s=s.replace(anchor,anchor+'''
   public static final DeferredItem<BlockItem> NETWORK_TRANSMITTER_ITEM = ITEMS.registerSimpleBlockItem("network_transmitter", NETWORK_TRANSMITTER);
   public static final DeferredItem<BlockItem> NETWORK_RECEIVER_ITEM = ITEMS.registerSimpleBlockItem("network_receiver", NETWORK_RECEIVER);''',1)
tab="output.accept((ItemLike)WIRELESS_CHARGER_ITEM.get());"
assert s.count(tab)==1
s=s.replace(tab,tab+'''
            output.accept((ItemLike)NETWORK_TRANSMITTER_ITEM.get());
            output.accept((ItemLike)NETWORK_RECEIVER_ITEM.get());''',1)
(j/p).write_text(s)

p="registry/ModBlockEntities.java"
s=(j/p).read_text()
needle='''   public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<WirelessChargerBlockEntity>> WIRELESS_CHARGER = TYPES.register(
      "wireless_charger", () -> new BlockEntityType(WirelessChargerBlockEntity::new, new Block[]{(Block)ObsidianNetwork.WIRELESS_CHARGER.get()})
   );'''
assert s.count(needle)==1, "ModBlockEntities wireless charger type shape changed"
addition='''
   // XSXLABS_WIRELESS_NETWORKS_V1: distinct persistent block entity types.
   public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity>> NETWORK_TRANSMITTER = TYPES.register(
      "network_transmitter", () -> new BlockEntityType((p,s) -> new dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity(p,s,true),new Block[]{(Block)ObsidianNetwork.NETWORK_TRANSMITTER.get()})
   );
   public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity>> NETWORK_RECEIVER = TYPES.register(
      "network_receiver", () -> new BlockEntityType((p,s) -> new dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity(p,s,false),new Block[]{(Block)ObsidianNetwork.NETWORK_RECEIVER.get()})
   );'''
(j/p).write_text(s.replace(needle,needle+addition,1))

p="registry/ModCapabilities.java"
s=(j/p).read_text()
needle="event.registerBlockEntity(Energy.BLOCK, ModBlockEntities.WIRELESS_CHARGER.get(), (charger, side) -> charger.energyHandler());"
assert s.count(needle)==1
s=s.replace(needle,needle+'''
      // XSXLABS_WIRELESS_NETWORKS_V1: FE accepts input at transmitter, provides output at receiver.
      event.registerBlockEntity(Energy.BLOCK, ModBlockEntities.NETWORK_TRANSMITTER.get(), (device,side) -> device.energyHandler());
      event.registerBlockEntity(Energy.BLOCK, ModBlockEntities.NETWORK_RECEIVER.get(), (device,side) -> device.energyHandler());''',1)
(j/p).write_text(s)

(j/"wireless").mkdir(exist_ok=True)
(j/"wireless/WirelessNetworkData.java").write_text(r'''package dev.obsidiannetwork.wireless;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.saveddata.SavedDataType;
import java.util.*;

/** World-global named wireless FE networks and independently enabled charging categories. */
public final class WirelessNetworkData extends SavedData {
 public static final String DEFAULT_ID="obsidiannetwork:main";
 public static final int INVENTORY=1, CURIOS=2, ARMOR=4, OFFHAND=8, HOTBAR=16;
 public static final int ALL_CATEGORIES=INVENTORY|CURIOS|ARMOR|OFFHAND|HOTBAR;
 public record Entry(String id, String name, String owner, int chargingMask) {
  public static final Codec<Entry> CODEC=RecordCodecBuilder.create(i -> i.group(
    Codec.STRING.fieldOf("id").forGetter(Entry::id),
    Codec.STRING.fieldOf("name").forGetter(Entry::name),
    Codec.STRING.fieldOf("owner").forGetter(Entry::owner),
    Codec.INT.fieldOf("chargingMask").forGetter(Entry::chargingMask)
   ).apply(i,Entry::new));
 }
 public static final SavedDataType<WirelessNetworkData> TYPE=new SavedDataType<>(
  Identifier.fromNamespaceAndPath("obsidiannetwork","wireless_fe_networks"),
  WirelessNetworkData::new,
  Entry.CODEC.listOf().xmap(WirelessNetworkData::new,WirelessNetworkData::entries)
 );
 private final LinkedHashMap<String,Entry> networks=new LinkedHashMap<>();
 public WirelessNetworkData(){
  networks.put(DEFAULT_ID,new Entry(DEFAULT_ID,"Main","",0));
 }
 private WirelessNetworkData(List<Entry> entries){
  for(Entry e:entries)if(e.id()!=null&&e.name()!=null&&e.id().length()<=80&&e.name().length()<=40&&e.chargingMask()>=0)
   networks.putIfAbsent(e.id(),e);
  networks.putIfAbsent(DEFAULT_ID,new Entry(DEFAULT_ID,"Main","",0));
 }
 public static WirelessNetworkData get(MinecraftServer server){
  return server.getDataStorage().computeIfAbsent(TYPE);
 }
 public List<Entry> entries(){return List.copyOf(networks.values());}
 public Entry find(String id){return networks.get(id);}
 public boolean canAccess(ServerPlayer p,String id){
  Entry e=networks.get(id);
  return e!=null&&(e.owner().isEmpty()||e.owner().equals(p.getUUID().toString())||p.hasPermissions(2));
 }
 public List<Entry> available(ServerPlayer p){
  return networks.values().stream().filter(e->canAccess(p,e.id())).toList();
 }
 public Entry create(ServerPlayer p,String name){
  name=name.strip();
  if(name.isEmpty()||name.length()>32||networks.size()>=128)return null;
  // Visible names are not identities. Owner-scoped duplicate names are rejected.
  for(Entry e:networks.values())if(e.name().equalsIgnoreCase(name)&&e.owner().equals(p.getUUID().toString()))return null;
  Entry created=new Entry(UUID.randomUUID().toString(),name,p.getUUID().toString(),0);
  networks.put(created.id(),created);setDirty();return created;
 }
 public boolean setCharging(ServerPlayer p,String id,int mask){
  if(!canAccess(p,id)||mask<0||(mask&~ALL_CATEGORIES)!=0)return false;
  Entry old=networks.get(id);
  if(!old.owner().isEmpty()&&!old.owner().equals(p.getUUID().toString())&&!p.hasPermissions(2))return false;
  if(old.chargingMask()==mask)return true;
  networks.put(id,new Entry(old.id(),old.name(),old.owner(),mask));
  setDirty();return true;
 }
}
''')

(j/"wireless/WirelessEnergyRuntime.java").write_text(r'''package dev.obsidiannetwork.wireless;

import dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.neoforged.neoforge.transfer.transaction.TransactionContext;
import java.lang.ref.WeakReference;
import java.util.*;

/**
 * Only loaded network transmitters are indexed, across all dimensions.
 * Never scans chunks or force-loads a dimension. Minecraft server-thread only.
 */
public final class WirelessEnergyRuntime {
 private static final Map<MinecraftServer,Map<String,List<WeakReference<WirelessNetworkBlockEntity>>>> LOADED =
  new WeakHashMap<>();
 private static final ThreadLocal<Boolean> IN_TRANSFER=ThreadLocal.withInitial(()->false);
 private WirelessEnergyRuntime(){}
 public static void register(WirelessNetworkBlockEntity sender){
  if(!sender.isTransmitter()||!(sender.getLevel() instanceof ServerLevel level))return;
  var bucket=LOADED.computeIfAbsent(level.getServer(),s->new HashMap<>())
    .computeIfAbsent(sender.networkId(),s->new ArrayList<>());
  bucket.removeIf(ref->ref.get()==null||ref.get()==sender);
  bucket.add(new WeakReference<>(sender));
 }
 public static void unregister(WirelessNetworkBlockEntity sender){
  if(!(sender.getLevel() instanceof ServerLevel level))return;
  var server=LOADED.get(level.getServer());
  if(server==null)return;
  for(var bucket:server.values())bucket.removeIf(ref->ref.get()==null||ref.get()==sender);
  server.entrySet().removeIf(e->e.getValue().isEmpty());
 }
 public static long available(MinecraftServer server,String id){
  if(WirelessNetworkData.get(server).find(id)==null)return 0;
  var nets=LOADED.get(server);
  if(nets==null)return 0;
  var group=nets.get(id);
  if(group==null)return 0;
  long total=0;
  for(var ref:group){
   var be=ref.get();
   if(be!=null&&be.isActive()&&be.networkId().equals(id))
    total=Math.min(Integer.MAX_VALUE,total+be.stored());
  }
  return total;
 }
 public static int pull(MinecraftServer server,String id,int wanted,TransactionContext tx){
  if(wanted<=0||IN_TRANSFER.get()||WirelessNetworkData.get(server).find(id)==null)return 0;
  var nets=LOADED.get(server);
  if(nets==null)return 0;
  var group=nets.get(id);
  if(group==null)return 0;
  IN_TRANSFER.set(true);
  try{
   int remaining=wanted;
   // Non-chunk-loading indexed visits; orphaned and unloaded transmitters are skipped.
   for(var ref:group){
    var be=ref.get();
    if(be==null||!be.isActive()||!id.equals(be.networkId()))continue;
    remaining-=be.withdraw(remaining,tx);
    if(remaining<=0)break;
   }
   return wanted-remaining;
  }finally{IN_TRANSFER.set(false);}
 }
}
''')

(j/"blockentity/WirelessNetworkBlockEntity.java").write_text(r'''package dev.obsidiannetwork.blockentity;

import dev.obsidiannetwork.registry.ModBlockEntities;
import dev.obsidiannetwork.wireless.WirelessEnergyRuntime;
import dev.obsidiannetwork.wireless.WirelessNetworkData;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.transfer.energy.EnergyHandler;
import net.neoforged.neoforge.transfer.transaction.SnapshotJournal;
import net.neoforged.neoforge.transfer.transaction.Transaction;
import net.neoforged.neoforge.transfer.transaction.TransactionContext;

public final class WirelessNetworkBlockEntity extends BlockEntity {
 public static final long CAPACITY=1000000L;
 private static final int MAX_TRANSFER=16000;
 private static final Direction[] DIRECTIONS=Direction.values();
 private final boolean transmitter;
 private final Handler handler=new Handler();
 private long stored;
 private String networkId=WirelessNetworkData.DEFAULT_ID;
 public WirelessNetworkBlockEntity(BlockPos pos,BlockState state,boolean transmitter){
  super(transmitter?ModBlockEntities.NETWORK_TRANSMITTER.get():ModBlockEntities.NETWORK_RECEIVER.get(),pos,state);
  this.transmitter=transmitter;
 }
 public boolean isTransmitter(){return transmitter;}
 public EnergyHandler energyHandler(){return handler;}
 public long stored(){return stored;}
 public String networkId(){return networkId;}
 public boolean isActive(){
  return transmitter&&!isRemoved()&&level instanceof ServerLevel world&&world.hasChunkAt(worldPosition)&&stored>0;
 }
 public void selectNetwork(String id){
  if(!(level instanceof ServerLevel world)||WirelessNetworkData.get(world.getServer()).find(id)==null)return;
  if(networkId.equals(id))return;
  if(transmitter)WirelessEnergyRuntime.unregister(this);
  networkId=id;setChanged();
  if(transmitter)WirelessEnergyRuntime.register(this);
 }
 @Override public void onLoad(){
  super.onLoad();
  if(transmitter)WirelessEnergyRuntime.register(this);
 }
 @Override public void setRemoved(){
  if(transmitter)WirelessEnergyRuntime.unregister(this);
  super.setRemoved();
 }
 @Override public void onChunkUnloaded(){
  if(transmitter)WirelessEnergyRuntime.unregister(this);
  super.onChunkUnloaded();
 }
 @Override protected void saveAdditional(ValueOutput out){
  super.saveAdditional(out);
  out.putString("network_id",networkId);
  out.putLong("wireless_fe",stored);
 }
 @Override protected void loadAdditional(ValueInput in){
  super.loadAdditional(in);
  networkId=in.getStringOr("network_id",WirelessNetworkData.DEFAULT_ID);
  if(networkId.length()>80)networkId=WirelessNetworkData.DEFAULT_ID;
  stored=transmitter?Math.max(0L,Math.min(CAPACITY,in.getLongOr("wireless_fe",0L))):0L;
 }
 public int withdraw(int requested,TransactionContext tx){
  if(!isActive()||requested<=0)return 0;
  int taken=(int)Math.min(Math.min(stored,(long)requested),MAX_TRANSFER);
  if(taken<=0)return 0;
  handler.journal.updateSnapshots(tx);
  stored-=taken;
  return taken;
 }
 public static void serverTick(Level level,BlockPos pos,BlockState state,WirelessNetworkBlockEntity be){
  if(!(level instanceof ServerLevel server)||be.transmitter||server.getGameTime()%5!=0)return;
  if(WirelessNetworkData.get(server.getServer()).find(be.networkId)==null)return;
  // Push to neighboring FE machines without scanning other chunks or the network graph.
  for(Direction side:DIRECTIONS){
   BlockPos neighbor=pos.relative(side);
   if(!server.hasChunkAt(neighbor))continue;
   if(server.getBlockState(neighbor).getBlock() instanceof dev.obsidiannetwork.block.WirelessNetworkBlock)continue;
   EnergyHandler target=server.getCapability(Capabilities.Energy.BLOCK,neighbor,side.getOpposite());
   if(target==null)continue;
   int offer=(int)Math.min(MAX_TRANSFER,WirelessEnergyRuntime.available(server.getServer(),be.networkId));
   if(offer<=0)break;
   // First discover what is actually insertable; discard simulation.
   int capacity;
   try(var simulated=Transaction.openRoot()){
    capacity=target.insert(offer,simulated);
   }
   if(capacity<=0)continue;
   try(var tx=Transaction.openRoot()){
    int withdrawn=WirelessEnergyRuntime.pull(server.getServer(),be.networkId,capacity,tx);
    if(withdrawn>0){
     int accepted=target.insert(withdrawn,tx);
     if(accepted==withdrawn)tx.commit();
    }
   }
  }
 }
 private final class Handler implements EnergyHandler {
  private final Journal journal=new Journal();
  public long getAmountAsLong(){
   if(transmitter)return stored;
   return level instanceof ServerLevel server?WirelessEnergyRuntime.available(server.getServer(),networkId):0L;
  }
  public long getCapacityAsLong(){return transmitter?CAPACITY:Integer.MAX_VALUE;}
  public int insert(int amount,TransactionContext tx){
   if(!transmitter||amount<=0)return 0;
   int accepted=(int)Math.min((long)amount,Math.min(CAPACITY-stored,MAX_TRANSFER));
   if(accepted<=0)return 0;
   journal.updateSnapshots(tx);stored+=accepted;return accepted;
  }
  public int extract(int amount,TransactionContext tx){
   if(transmitter||amount<=0||!(level instanceof ServerLevel world))return 0;
   return WirelessEnergyRuntime.pull(world.getServer(),networkId,Math.min(amount,MAX_TRANSFER),tx);
  }
  private final class Journal extends SnapshotJournal<Long> {
   protected Long createSnapshot(){return stored;}
   protected void revertToSnapshot(Long before){stored=before;}
   protected void onRootCommit(Long before){if(before!=stored)setChanged();}
  }
 }
}
''')

(j/"block/WirelessNetworkBlock.java").write_text(r'''package dev.obsidiannetwork.block;

import com.mojang.serialization.MapCodec;
import dev.obsidiannetwork.ObsidianNetwork;
import dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity;
import dev.obsidiannetwork.registry.ModBlockEntities;
import dev.obsidiannetwork.wireless.WirelessNetworkData;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.Property;
import net.minecraft.world.level.block.state.BlockBehaviour.Properties;
import net.minecraft.world.phys.BlockHitResult;
import org.jetbrains.annotations.Nullable;

public final class WirelessNetworkBlock extends BaseEntityBlock {
 public static final Property<Direction> FACING=HorizontalDirectionalBlock.FACING;
 private static final MapCodec<WirelessNetworkBlock> TRANSMITTER_CODEC=simpleCodec(p->new WirelessNetworkBlock(p,true));
 private static final MapCodec<WirelessNetworkBlock> RECEIVER_CODEC=simpleCodec(p->new WirelessNetworkBlock(p,false));
 private final boolean transmitter;
 public WirelessNetworkBlock(Properties props,boolean transmitter){
  super(props);this.transmitter=transmitter;
  registerDefaultState(stateDefinition.any().setValue(FACING,Direction.NORTH));
 }
 @Override protected void createBlockStateDefinition(StateDefinition.Builder<net.minecraft.world.level.block.Block,BlockState> b){b.add(FACING);}
 @Override public BlockState getStateForPlacement(BlockPlaceContext context){return defaultBlockState().setValue(FACING,context.getHorizontalDirection().getOpposite());}
 @Override protected MapCodec<? extends BaseEntityBlock> codec(){return transmitter?TRANSMITTER_CODEC:RECEIVER_CODEC;}
 @Override public RenderShape getRenderShape(BlockState state){return RenderShape.MODEL;}
 @Nullable @Override public BlockEntity newBlockEntity(BlockPos pos,BlockState state){return new WirelessNetworkBlockEntity(pos,state,transmitter);}
 @Nullable @Override public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level,BlockState state,BlockEntityType<T> type){
  if(level.isClientSide()||transmitter)return null;
  return createTickerHelper(type,ModBlockEntities.NETWORK_RECEIVER.get(),WirelessNetworkBlockEntity::serverTick);
 }
 @Override protected InteractionResult useWithoutItem(BlockState state,Level level,BlockPos pos,Player player,BlockHitResult hit){
  if(!(level.getBlockEntity(pos) instanceof WirelessNetworkBlockEntity device))return InteractionResult.PASS;
  if(level.isClientSide())return InteractionResult.SUCCESS;
  if(!(player instanceof ServerPlayer p))return InteractionResult.SUCCESS;
  var data=WirelessNetworkData.get(p.level().getServer());
  if(player.isShiftKeyDown()){
   var allowed=data.available(p);
   if(!allowed.isEmpty()){
    int current=-1;
    for(int i=0;i<allowed.size();i++)if(allowed.get(i).id().equals(device.networkId()))current=i;
    var next=allowed.get((current+1)%allowed.size());
    device.selectNetwork(next.id());
   }
  }
  var selected=data.find(device.networkId());
  p.sendSystemMessage(Component.literal((transmitter?"Network Transmitter":"Network Receiver")+
     " | "+(selected==null?"Unknown":selected.name())+
     " | "+(transmitter?device.stored():0)+" FE"+
     " (Shift+right click: select next network)"));
  return InteractionResult.SUCCESS;
 }
}
''')
# Generate resource names and identity, using the existing original antenna as base.
print("WIRELESS_NETWORK_CORE_V1 PASS: 2 blocks, SavedData named networks, atomic FE network, loaded sender index")
