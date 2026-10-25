#!/usr/bin/env python3
"""v1.7.3 Build200: permanent Portal A destinations / short-lived Portal B ingress.

Portal A is a real, breakable owner-tagged block and is indexed in SavedData.
Only the server selects saved anchors, places B and performs cross-dimension
teleports. B is transient, not craftable, does not persist a target, and
is removed after successful transport or a 60-second lifetime.
"""
import os,json
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
D=Path(os.environ["V1_RESOURCE_ROOT"])/"data/obsidiannetwork"
def edit(rel,old,new):
 p=J/rel
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,(rel,old[:120],s.count(old))
 p.write_text(s.replace(old,new,1),encoding="utf-8")
def java(rel,src):
 p=J/rel;p.parent.mkdir(parents=True,exist_ok=True)
 assert not p.exists(),p
 p.write_text(src,encoding="utf-8")
def js(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

edit("ObsidianNetwork.java",
 'ITEMS.registerSimpleBlockItem("network_signal_receiver",NETWORK_SIGNAL_RECEIVER);',
 '''ITEMS.registerSimpleBlockItem("network_signal_receiver",NETWORK_SIGNAL_RECEIVER);
    // V173_PORTAL_A_B: independent transport, no inventory or FE bridging.
    public static final DeferredBlock<dev.obsidiannetwork.portal.PortalGateBlock> NETWORK_PORTAL_A =
      BLOCKS.registerBlock("network_portal_a",
        p -> new dev.obsidiannetwork.portal.PortalGateBlock(p,false),
        p -> p.mapColor(MapColor.COLOR_PURPLE).strength(3.0F,20.0F).noOcclusion());
    public static final DeferredItem<BlockItem> NETWORK_PORTAL_A_ITEM =
      ITEMS.registerSimpleBlockItem("network_portal_a",NETWORK_PORTAL_A);
    public static final DeferredBlock<dev.obsidiannetwork.portal.PortalGateBlock> NETWORK_PORTAL_B =
      BLOCKS.registerBlock("network_portal_b",
        p -> new dev.obsidiannetwork.portal.PortalGateBlock(p,true),
        p -> p.mapColor(MapColor.COLOR_BLUE).strength(-1.0F,3600000.0F).noOcclusion());''')
edit("ObsidianNetwork.java",
 '            output.accept((ItemLike)NETWORK_SIGNAL_RECEIVER_ITEM.get());',
 '''            output.accept((ItemLike)NETWORK_SIGNAL_RECEIVER_ITEM.get());
            output.accept((ItemLike)NETWORK_PORTAL_A_ITEM.get());''')
edit("registry/ModBlockEntities.java",
 '   public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<dev.obsidiannetwork.blockentity.NetworkSignalRelayBlockEntity>> NETWORK_SIGNAL_RELAY =',
 '''   public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<dev.obsidiannetwork.portal.PortalGateBlockEntity>> NETWORK_PORTAL =
       TYPES.register("network_portal",()->new BlockEntityType(
         dev.obsidiannetwork.portal.PortalGateBlockEntity::new,
         new Block[]{(Block)ObsidianNetwork.NETWORK_PORTAL_A.get(),
                     (Block)ObsidianNetwork.NETWORK_PORTAL_B.get()}));
   public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<dev.obsidiannetwork.blockentity.NetworkSignalRelayBlockEntity>> NETWORK_SIGNAL_RELAY =''')

java("portal/PortalIndex.java",r'''package dev.obsidiannetwork.portal;
import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import java.util.*;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.saveddata.SavedDataType;

/** V173_PORTAL_INDEX: persisted dimension-aware A positions, NEVER B targets. */
public final class PortalIndex extends SavedData {
 public record Anchor(String owner,String dimension,int x,int y,int z,boolean selected){
  public static final Codec<Anchor> CODEC=RecordCodecBuilder.create(i->i.group(
    Codec.STRING.fieldOf("owner").forGetter(Anchor::owner),
    Codec.STRING.fieldOf("dimension").forGetter(Anchor::dimension),
    Codec.INT.fieldOf("x").forGetter(Anchor::x),
    Codec.INT.fieldOf("y").forGetter(Anchor::y),
    Codec.INT.fieldOf("z").forGetter(Anchor::z),
    Codec.BOOL.fieldOf("selected").forGetter(Anchor::selected)
  ).apply(i,Anchor::new));
  public BlockPos pos(){return new BlockPos(x,y,z);}
  public Anchor withSelected(boolean chosen){return new Anchor(owner,dimension,x,y,z,chosen);}
  public String key(){return dimension+"#"+x+","+y+","+z;}
 }
 public static final SavedDataType<PortalIndex> TYPE=new SavedDataType<>(
   Identifier.fromNamespaceAndPath("obsidiannetwork","portal_a_destinations"),
   PortalIndex::new, Anchor.CODEC.listOf().xmap(PortalIndex::new,PortalIndex::all));
 private final Map<String,Anchor> saved=new LinkedHashMap<>();
 public PortalIndex(){}
 private PortalIndex(List<Anchor> data){for(Anchor a:data)saved.put(a.key(),a);}
 public static PortalIndex get(MinecraftServer server){return server.getDataStorage().computeIfAbsent(TYPE);}
 public List<Anchor> all(){return List.copyOf(saved.values());}
 public List<Anchor> owned(UUID player){
  List<Anchor> items=new ArrayList<>();
  for(Anchor a:saved.values())if(a.owner().equals(player.toString()))items.add(a);
  return items;
 }
 public Anchor selected(UUID player){
  List<Anchor> items=owned(player);
  if(items.isEmpty())return null;
  for(Anchor a:items)if(a.selected())return a;
  return items.get(0);
 }
 public void register(ServerLevel level,BlockPos pos,UUID player){
  String dim=level.dimension().identifier().toString();
  Anchor a=new Anchor(player.toString(),dim,pos.getX(),pos.getY(),pos.getZ(),true);
  for(Anchor old:owned(player))saved.put(old.key(),old.withSelected(false));
  saved.put(a.key(),a);setDirty();
 }
 public void remove(ServerLevel level,BlockPos pos){
  String key=level.dimension().identifier()+"#"+pos.getX()+","+pos.getY()+","+pos.getZ();
  if(saved.remove(key)!=null)setDirty();
 }
 public Anchor cycle(UUID owner){
  List<Anchor> list=owned(owner);
  if(list.isEmpty())return null;
  int idx=-1;
  for(int i=0;i<list.size();i++)if(list.get(i).selected()){idx=i;break;}
  Anchor chosen=list.get((idx+1)%list.size());
  for(Anchor a:list)saved.put(a.key(),a.withSelected(a.key().equals(chosen.key())));
  setDirty();
  return chosen;
 }
}
''')

java("portal/PortalGateBlock.java",r'''package dev.obsidiannetwork.portal;
import com.mojang.serialization.MapCodec;
import dev.obsidiannetwork.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;
import org.jetbrains.annotations.Nullable;

/** V173_PORTAL_FRAME: walk-through visual aperture (2-block-high render shape). */
public final class PortalGateBlock extends BaseEntityBlock {
 private final boolean temporary;
 private static final MapCodec<PortalGateBlock> A=simpleCodec(p->new PortalGateBlock(p,false));
 private static final MapCodec<PortalGateBlock> B=simpleCodec(p->new PortalGateBlock(p,true));
 public PortalGateBlock(Properties p,boolean temporary){super(p);this.temporary=temporary;}
 @Override protected MapCodec<? extends BaseEntityBlock> codec(){return temporary?B:A;}
 @Override public RenderShape getRenderShape(BlockState s){return RenderShape.MODEL;}
 @Override public VoxelShape getCollisionShape(BlockState s,BlockGetter l,BlockPos p,CollisionContext c){return Shapes.empty();}
 @Override public VoxelShape getShape(BlockState s,BlockGetter l,BlockPos p,CollisionContext c){
  return box(1,0,6,15,32,10);
 }
 @Nullable @Override public BlockEntity newBlockEntity(BlockPos p,BlockState s){
  return new PortalGateBlockEntity(p,s);
 }
 @Override public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level,BlockState s,BlockEntityType<T> type){
  return level.isClientSide()?null:createTickerHelper(type,ModBlockEntities.NETWORK_PORTAL.get(),PortalGateBlockEntity::tick);
 }
 @Override public void setPlacedBy(Level l,BlockPos p,BlockState s,@Nullable LivingEntity e,ItemStack stack){
  super.setPlacedBy(l,p,s,e,stack);
  if(!temporary && l instanceof ServerLevel sl && e instanceof Player player &&
     l.getBlockEntity(p) instanceof PortalGateBlockEntity be){
   be.assignAnchor(player.getUUID());
   PortalIndex.get(sl.getServer()).register(sl,p,player.getUUID());
  }
 }
 @Override protected void affectNeighborsAfterRemoval(BlockState state,ServerLevel level,BlockPos pos,boolean piston){
  if(!temporary)PortalIndex.get(level.getServer()).remove(level,pos);
  super.affectNeighborsAfterRemoval(state,level,pos,piston);
 }
}
''')

java("portal/PortalGateBlockEntity.java",r'''package dev.obsidiannetwork.portal;
import dev.obsidiannetwork.ObsidianNetwork;
import dev.obsidiannetwork.registry.ModBlockEntities;
import java.util.Set;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/** V173_PORTAL_ONE_SHOT: B only transports its owner to an existing real A. */
public final class PortalGateBlockEntity extends BlockEntity {
 private String owner="";
 private PortalIndex.Anchor target; // never serialized: reloaded B expires safely
 private int lifetime=0;
 public PortalGateBlockEntity(BlockPos pos,BlockState state){
  super(ModBlockEntities.NETWORK_PORTAL.get(),pos,state);
 }
 public void assignAnchor(UUID player){owner=player.toString();setChanged();}
 public void bindTemporary(UUID player,PortalIndex.Anchor anchor){
  owner=player.toString();target=anchor;lifetime=0;setChanged();
 }
 @Override protected void saveAdditional(ValueOutput out){
  super.saveAdditional(out);
  if(getBlockState().is(ObsidianNetwork.NETWORK_PORTAL_A.get()))out.putString("owner",owner);
 }
 @Override protected void loadAdditional(ValueInput in){
  super.loadAdditional(in);
  owner=in.getStringOr("owner","");
  target=null; // prevents stale B links across chunk loads / server restarts
 }
 public static void tick(Level l,BlockPos pos,BlockState state,PortalGateBlockEntity be){
  if(!(l instanceof ServerLevel level)||!state.is(ObsidianNetwork.NETWORK_PORTAL_B.get()))return;
  if(be.target==null||be.owner.isEmpty()||++be.lifetime>1200){
   level.setBlockAndUpdate(pos,Blocks.AIR.defaultBlockState());
   return;
  }
  for(ServerPlayer player:level.players()){
   if(!be.owner.equals(player.getUUID().toString())||player.isSpectator())continue;
   // Only stepping into B counts; merely spawning B must not teleport instantly.
   if(Math.abs(player.getX()-(pos.getX()+0.5))>0.52 ||
      Math.abs(player.getZ()-(pos.getZ()+0.5))>0.52 ||
      player.getY()<pos.getY()-0.35 ||player.getY()>pos.getY()+1.85)continue;
   try{
    PortalIndex.Anchor anchor=be.target;
    ServerLevel dest=level.getServer().getLevel(
      ResourceKey.create(Registries.DIMENSION,Identifier.parse(anchor.dimension())));
    if(dest==null){player.sendSystemMessage(Component.literal("Portal A dimension unavailable."));return;}
    BlockPos exit=anchor.pos();
    // Destination chunk is loaded only upon actual authorized entry.
    dest.getChunkAt(exit);
    if(!dest.getBlockState(exit).is(ObsidianNetwork.NETWORK_PORTAL_A.get()) ||
        !(dest.getBlockEntity(exit) instanceof PortalGateBlockEntity other) ||
        !be.owner.equals(other.owner)){
     PortalIndex.get(level.getServer()).remove(dest,exit);
     player.sendSystemMessage(Component.literal("Portal A no longer exists. Select another target."));
     level.setBlockAndUpdate(pos,Blocks.AIR.defaultBlockState());return;
    }
    if(!dest.getBlockState(exit.above()).isAir()){
     player.sendSystemMessage(Component.literal("Portal A exit obstructed."));return;
    }
    if(player.teleportTo(dest,exit.getX()+0.5,exit.getY()+0.05,exit.getZ()+0.5,
         Set.of(),player.getYRot(),player.getXRot(),true)){
     level.setBlockAndUpdate(pos,Blocks.AIR.defaultBlockState());
    }
   }catch(IllegalArgumentException ex){
    level.setBlockAndUpdate(pos,Blocks.AIR.defaultBlockState());
   }
   return;
  }
 }
}
''')

java("portal/PortalActionPayload.java",r'''package dev.obsidiannetwork.portal;
import dev.obsidiannetwork.ObsidianNetwork;
import net.minecraft.core.BlockPos;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.chat.Component;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.block.Blocks;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;

/** V173_PORTAL_ACTIONS: no client-provided dimension, position or owner. */
public final class PortalActionPayload {
 private PortalActionPayload(){}
 public record Cycle() implements CustomPacketPayload {
  public static final Type<Cycle> TYPE=new Type<>(
    Identifier.fromNamespaceAndPath("obsidiannetwork","portal_cycle_a"));
  public static final StreamCodec<RegistryFriendlyByteBuf,Cycle> CODEC=StreamCodec.unit(new Cycle());
  @Override public Type<? extends CustomPacketPayload> type(){return TYPE;}
 }
 public record Spawn() implements CustomPacketPayload {
  public static final Type<Spawn> TYPE=new Type<>(
    Identifier.fromNamespaceAndPath("obsidiannetwork","portal_spawn_b"));
  public static final StreamCodec<RegistryFriendlyByteBuf,Spawn> CODEC=StreamCodec.unit(new Spawn());
  @Override public Type<? extends CustomPacketPayload> type(){return TYPE;}
 }
 @EventBusSubscriber(modid="obsidiannetwork")
 public static final class Handler {
  private Handler(){}
  @SubscribeEvent public static void register(RegisterPayloadHandlersEvent e){
   var net=e.registrar("1");
   net.playToServer(Cycle.TYPE,Cycle.CODEC,(payload,context)->{
    if(context.player() instanceof ServerPlayer player)cycle(player);
   });
   net.playToServer(Spawn.TYPE,Spawn.CODEC,(payload,context)->{
    if(context.player() instanceof ServerPlayer player)spawn(player);
   });
  }
 }
 private static void tell(ServerPlayer player,String text){player.sendSystemMessage(Component.literal(text));}
 public static void cycle(ServerPlayer player){
  var index=PortalIndex.get(player.level().getServer());
  var chosen=index.cycle(player.getUUID());
  if(chosen==null){tell(player,"No Portal A placed. Place a Network Portal A first.");return;}
  tell(player,"Portal A selected: "+chosen.dimension()+" ["+chosen.x()+", "+chosen.y()+", "+chosen.z()+"] ("+
     index.owned(player.getUUID()).size()+" saved)");
 }
 public static void spawn(ServerPlayer player){
  if(player.isSpectator())return;
  var index=PortalIndex.get(player.level().getServer());
  var a=index.selected(player.getUUID());
  if(a==null){tell(player,"Place a Portal A before summoning Portal B.");return;}
  ServerLevel level=player.level();
  BlockPos pos=player.blockPosition().relative(player.getDirection(),2);
  // Position selected server-side. Never replace blocks, fluids or a player's headspace.
  if(!level.getBlockState(pos).isAir()||!level.getBlockState(pos.above()).isAir() ||
      level.getBlockState(pos.below()).isAir() ||!level.getWorldBorder().isWithinBounds(pos)){
   tell(player,"Portal B needs two free blocks and solid ground two blocks in front of you.");return;
  }
  if(!level.setBlockAndUpdate(pos,ObsidianNetwork.NETWORK_PORTAL_B.get().defaultBlockState()))return;
  if(level.getBlockEntity(pos) instanceof PortalGateBlockEntity be){
   be.bindTemporary(player.getUUID(),a);
   tell(player,"Portal B opened -> "+a.dimension()+" ["+a.x()+", "+a.y()+", "+a.z()+"]. Enter to travel.");
  }else{
   level.setBlockAndUpdate(pos,Blocks.AIR.defaultBlockState());
  }
 }
}
''')

java("portal/PortalKeysClient.java",r'''package dev.obsidiannetwork.portal;
import com.mojang.blaze3d.platform.InputConstants;
import dev.obsidiannetwork.powerarmor.PowerArmorExitKeyClient;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import net.neoforged.neoforge.client.event.RegisterKeyMappingsEvent;
import net.neoforged.neoforge.client.network.ClientPacketDistributor;
import org.lwjgl.glfw.GLFW;

/** V173_PORTAL_KEYS: rebindable, existing xSxLabs category (L and B). */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class PortalKeysClient {
 private PortalKeysClient(){}
 private static final KeyMapping SELECT=new KeyMapping(
  "key.obsidiannetwork.portal_select_a",InputConstants.Type.KEYSYM,GLFW.GLFW_KEY_L,
  PowerArmorExitKeyClient.CATEGORY);
 private static final KeyMapping SPAWN=new KeyMapping(
  "key.obsidiannetwork.portal_spawn_b",InputConstants.Type.KEYSYM,GLFW.GLFW_KEY_B,
  PowerArmorExitKeyClient.CATEGORY);
 @SubscribeEvent public static void register(RegisterKeyMappingsEvent e){
  e.register(SELECT);e.register(SPAWN);
 }
 @SubscribeEvent public static void tick(ClientTickEvent.Post e){
  Minecraft mc=Minecraft.getInstance();
  while(SELECT.consumeClick())if(mc.player!=null&&mc.screen==null)
   ClientPacketDistributor.sendToServer(new PortalActionPayload.Cycle());
  while(SPAWN.consumeClick())if(mc.player!=null&&mc.screen==null)
   ClientPacketDistributor.sendToServer(new PortalActionPayload.Spawn());
 }
}
''')

# Frames protrude one block above their footprint; the space must be clear.
# Vanilla textures avoid resource-pack missing-texture regressions.
for name,glass in (("network_portal_a","minecraft:block/purple_stained_glass"),
                   ("network_portal_b","minecraft:block/light_blue_stained_glass")):
 def part(frm,to,tex):
  return {"from":frm,"to":to,"faces":{f:{"texture":"#"+tex} for f in
           ("north","south","east","west","up","down")}}
 model={"render_type":"minecraft:translucent",
        "textures":{"particle":"minecraft:block/obsidian","frame":"minecraft:block/obsidian","window":glass},
        "elements":[
         part([1,0,6],[3,31,10],"frame"),
         part([13,0,6],[15,31,10],"frame"),
         part([3,27,6],[13,31,10],"frame"),
         part([3,0,6],[13,4,10],"frame"),
         part([3,4,7.5],[13,27,8.5],"window")]}
 js(R/"models/block"/(name+".json"),model)
 js(R/"blockstates"/(name+".json"),{"variants":{"":{"model":"obsidiannetwork:block/"+name}}})
js(R/"items/network_portal_a.json",{"model":{"type":"minecraft:model","model":"obsidiannetwork:block/network_portal_a"}})
js(D/"loot_table/blocks/network_portal_a.json",
   {"type":"minecraft:block","pools":[{"rolls":1,"entries":[{"type":"minecraft:item","name":"obsidiannetwork:network_portal_a"}]}]})
js(D/"recipe/network_portal_a.json",{
 "type":"minecraft:crafting_shaped","category":"misc",
 "pattern":["OEO","ENE","ODO"],
 "key":{"O":"minecraft:obsidian","E":"minecraft:ender_pearl",
        "N":"minecraft:nether_star","D":"minecraft:diamond_block"},
 "result":{"id":"obsidiannetwork:network_portal_a","count":1}})
for lang,names in (("de_de",("Portal A auswählen (nächstes)","Temporäres Portal B erzeugen")),
                   ("en_us",("Select next Portal A","Summon temporary Portal B"))):
 p=R/"lang"/(lang+".json");data=json.loads(p.read_text(encoding="utf-8"))
 data["block.obsidiannetwork.network_portal_a"]="Netzwerkportal A" if lang=="de_de" else "Network Portal A"
 data["block.obsidiannetwork.network_portal_b"]="Netzwerkportal B" if lang=="de_de" else "Network Portal B"
 data["key.obsidiannetwork.portal_select_a"]=names[0]
 data["key.obsidiannetwork.portal_spawn_b"]=names[1]
 js(p,data)
print("V173_PORTAL_A_B_BUILD200_PASS")
