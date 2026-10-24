#!/usr/bin/env python3
"""v1.7.2: unlimited, cross-dimension Power Armor Recall with original-location fallback.

A durable SavedData index tracks each real owner-tagged standing suit, including
its dimension. NeoForge tickets temporarily load source chunks across dimensions.
Only an ITEMLESS animated GeckoLib visual flies from ~16 blocks toward the player.
The original four equipment stacks remain on the original ArmorStand until the
visual arrives and the existing transactional finishEntering routine commits.
On any failure the visual is removed and ALL real equipment stays at the source.
"""
import os,json
from pathlib import Path
java=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
assets=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
def write(name,data):
 p=java/name
 assert not p.exists(),name
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(data,encoding="utf-8")
def edit(name,a,b):
 p=java/name;s=p.read_text(encoding="utf-8")
 assert s.count(a)==1,(name,"anchor",s.count(a),a[:90])
 p.write_text(s.replace(a,b,1),encoding="utf-8")

write("powerarmor/PowerArmorRecallIndex.java",r'''package dev.obsidiannetwork.powerarmor;
import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import java.util.*;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.saveddata.SavedDataType;

/** V172_DURABLE_SUIT_INDEX: locations, never actual ItemStacks. */
public final class PowerArmorRecallIndex extends SavedData {
 public record Location(String owner,String suit,String dimension,double x,double y,double z){
  public static final Codec<Location> CODEC=RecordCodecBuilder.create(i->i.group(
   Codec.STRING.fieldOf("owner").forGetter(Location::owner),
   Codec.STRING.fieldOf("suit").forGetter(Location::suit),
   Codec.STRING.fieldOf("dimension").forGetter(Location::dimension),
   Codec.DOUBLE.fieldOf("x").forGetter(Location::x),
   Codec.DOUBLE.fieldOf("y").forGetter(Location::y),
   Codec.DOUBLE.fieldOf("z").forGetter(Location::z)
  ).apply(i,Location::new));
  public UUID suitUUID(){return UUID.fromString(suit);}
 }
 public static final SavedDataType<PowerArmorRecallIndex> TYPE=new SavedDataType<>(
  Identifier.fromNamespaceAndPath("obsidiannetwork","power_armor_recall_index"),
  PowerArmorRecallIndex::new,
  Location.CODEC.listOf().xmap(PowerArmorRecallIndex::new,PowerArmorRecallIndex::all));
 private final Map<String,Location> entries=new LinkedHashMap<>();
 public PowerArmorRecallIndex(){}
 private PowerArmorRecallIndex(List<Location> loaded){
  for(Location e:loaded)entries.putIfAbsent(e.suit(),e);
 }
 public static PowerArmorRecallIndex get(MinecraftServer server){
  return server.getDataStorage().computeIfAbsent(TYPE);
 }
 public List<Location> all(){return List.copyOf(entries.values());}
 public List<Location> owned(UUID player){
  List<Location> found=new ArrayList<>();
  for(Location e:entries.values())if(e.owner().equals(player.toString()))found.add(e);
  return found;
 }
 public void index(ArmorStand suit,ServerLevel dimension,UUID owner){
  Location loc=new Location(owner.toString(),suit.getUUID().toString(),
    dimension.dimension().identifier().toString(),suit.getX(),suit.getY(),suit.getZ());
  if(!loc.equals(entries.put(loc.suit(),loc)))setDirty();
 }
 public void remove(UUID suit){
  if(entries.remove(suit.toString())!=null)setDirty();
 }
}
''')

write("powerarmor/PowerArmorRecallTickets.java",r'''package dev.obsidiannetwork.powerarmor;
import java.util.UUID;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.world.chunk.TicketController;
import net.neoforged.neoforge.common.world.chunk.RegisterTicketControllersEvent;
/** V172_SOURCE_TICKET: temporarily load original suit, even in other dimensions. */
@EventBusSubscriber(modid="obsidiannetwork")
public final class PowerArmorRecallTickets {
 private static final TicketController CONTROLLER=new TicketController(
  Identifier.fromNamespaceAndPath("obsidiannetwork","armor_recall"));
 private PowerArmorRecallTickets(){}
 @SubscribeEvent public static void register(RegisterTicketControllersEvent e){
  e.register(CONTROLLER);
 }
 public static boolean ticket(ServerLevel level,UUID owner,int x,int z,boolean add){
  return CONTROLLER.forceChunk(level,owner,x,z,add,false);
 }
}
''')

# Export existing loss-safe transaction for remote, owner-checked invocation.
edit("powerarmor/PowerArmorSuitWorld.java",
 ''' private static void finishEntering(ArmorStand stand,ServerPlayer player){''',
 ''' // V172_REMOTE_ENTRY: only called after authenticated recall flight. The
 // existing finishEntering still owns all backup, anti-dup and rollback work.
 public static boolean recallEquip(ArmorStand stand,ServerPlayer player){
  if(stand==null||stand.isRemoved()||!mine(stand,player)||!full(stand))return false;
  if(ACTIVE.containsKey(player.getUUID())||PowerArmorRuntime.full(player))return false;
  if(ArmorLoadoutData.get(player.level().getServer()).has(player))return false;
  finishEntering(stand,player);
  return PowerArmorRuntime.full(player)&&stand.isRemoved();
 }
 private static void finishEntering(ArmorStand stand,ServerPlayer player){''')
# Existing decorative mannequin is otherwise automatically removed in 23 ticks.
edit("powerarmor/PowerArmorVisualEntity.java",
 '''  if(!level().isClientSide()&&tickCount>23)discard();''',
 '''  if(!level().isClientSide()&&tickCount>23
    &&(!entityTags().contains("xsxlabs_power_armor_recall_visual_v172")
    ||!PowerArmorRecall.isVisualActive(getUUID())))discard();''')

visual_cases="\n".join(
 f"   case {k} -> dev.obsidiannetwork.ObsidianNetwork.ARMOR_VISUAL_ENTITY_MK{k}.get();"
 for k in range(2,25))
core=r'''package dev.obsidiannetwork.powerarmor;
import java.util.*;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;
import net.neoforged.neoforge.event.entity.EntityLeaveLevelEvent;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/** V172_UNLIMITED_CROSS_DIM_RECALL:
 * Original suit NEVER MOVES during flight, never clones stacks.
 * Fail / timeout / disconnect / obstructed -> original stand stays intact.
 */
@EventBusSubscriber(modid="obsidiannetwork")
public final class PowerArmorRecall {
 private static final String MARKER="xsxlabs_power_armor_suit_v17";
 private static final String OWNER="xsxlabs_power_armor_owner_";
 private static final String VISUAL="xsxlabs_power_armor_recall_visual_v172";
 private static final int MAX_PREPARE=160,MAX_FLIGHT=160;
 private static final double SPEED=.72D;
 private record Flight(PowerArmorRecallIndex.Location loc,UUID visual,int ticks,boolean ready){}
 private static final Map<UUID,Flight> ACTIVE=new HashMap<>();
 private PowerArmorRecall(){}
 /** Abandoned flight visuals disappear after server restart. */
 public static boolean isVisualActive(UUID visual){
  for(Flight f:ACTIVE.values())if(visual.equals(f.visual()))return true;
  return false;
 }
 @SubscribeEvent public static void startup(ServerStartedEvent event){
  // V172_SERVER_RESTART_GUARD: no flight can survive a server restart.
  // Keep the saved suit locations; only volatile flight state is cleared.
  ACTIVE.clear();
  // Tickets persist through crashes; clear old recall-only chunk tickets.
  var server=event.getServer();
  for(var loc:PowerArmorRecallIndex.get(server).all()){
   ServerLevel old=source(server,loc);
   if(old==null)continue;
   BlockPos bp=BlockPos.containing(loc.x(),loc.y(),loc.z());
   PowerArmorRecallTickets.ticket(old,UUID.fromString(loc.owner()),
       bp.getX()>>4,bp.getZ()>>4,false);
  }
 }
 private static void tell(ServerPlayer p,String message){
  p.sendSystemMessage(Component.literal("Power Armor Recall: "+message));
 }
 private static ServerLevel source(MinecraftServer server,PowerArmorRecallIndex.Location loc){
  try{
   return server.getLevel(ResourceKey.create(Registries.DIMENSION,
     Identifier.parse(loc.dimension())));
  }catch(IllegalArgumentException ex){return null;}
 }
 private static boolean owned(ArmorStand stand,UUID owner){
  return stand!=null&&!stand.isRemoved()&&stand.entityTags().contains(MARKER)
    &&stand.entityTags().contains(OWNER+owner)&&PowerArmorSuitWorld.full(stand);
 }
 private static void release(ServerPlayer player,Flight flight){
  ServerLevel world=source(player.level().getServer(),flight.loc());
  if(world!=null){
   BlockPos pos=BlockPos.containing(flight.loc().x(),flight.loc().y(),flight.loc().z());
   PowerArmorRecallTickets.ticket(world,player.getUUID(),pos.getX()>>4,pos.getZ()>>4,false);
  }
  if(flight.visual()!=null){
   // V172_DIMENSION_CLEANUP: the player can leave through a portal mid-flight.
   // Remove the cosmetic visual from its original level, not just the new level.
   for(ServerLevel dimension:player.level().getServer().getAllLevels()){
    Entity v=dimension.getEntity(flight.visual());
    if(v!=null&&!v.isRemoved())v.discard();
   }
  }
  ACTIVE.remove(player.getUUID());
 }
 private static void abort(ServerPlayer player,Flight flight,String reason){
  release(player,flight);
  tell(player,reason+" Original suit is still at its former position.");
 }
 private static EntityType<PowerArmorVisualEntity> kind(int tier){
  return switch(tier){
   default -> dev.obsidiannetwork.ObsidianNetwork.ARMOR_VISUAL_ENTITY_MK1.get();
VISUAL_CASES
  };
 }
 private static boolean locate(ServerPlayer p,PowerArmorVisualEntity visual){
  Vec3 forward=p.getLookAngle();
  forward=new Vec3(forward.x,0D,forward.z);
  if(forward.lengthSqr()<.001D)forward=new Vec3(1D,0D,0D);
  forward=forward.normalize();
  // V172_TRUE_16_BLOCK_LIMIT: the whole 3D distance must be <=16,
  // including vertical offset (the old 16 horizontal + height exceeded it).
  // Search different bearings/heights; never teleport inside solid blocks.
  for(int a=0;a<8;a++){
   double angle=a*Math.PI/4D;
   Vec3 dir=new Vec3(forward.x*Math.cos(angle)-forward.z*Math.sin(angle),
                     0D,forward.x*Math.sin(angle)+forward.z*Math.cos(angle));
   for(int height:new int[]{2,5,9}){
    double radius=Math.sqrt(256D-(double)height*height)-0.25D;
    Vec3 dest=p.position().add(dir.scale(radius)).add(0D,height,0D);
    if(dest.distanceToSqr(p.position())>256D)continue;
    if(!p.level().hasChunkAt(BlockPos.containing(dest)))continue;
    visual.setPos(dest.x,dest.y,dest.z);
    if(p.level().noCollision(visual,visual.getBoundingBox()))return true;
   }
  }
  return false;
 }
 /** Only server may choose the source, destination and transfer. */
 public static int request(ServerPlayer player){
  if(player.isSpectator()||!player.isAlive()||PowerArmorRuntime.full(player)){
   tell(player,"cannot recall while wearing Power Armor or spectating.");return 0;
  }
  if(ArmorLoadoutData.get(player.level().getServer()).has(player)){
   tell(player,"unresolved original-armor backup; no action taken.");return 0;
  }
  if(ACTIVE.containsKey(player.getUUID())){
   tell(player,"your suit is already on its way.");return 0;
  }
  var matches=PowerArmorRecallIndex.get(player.level().getServer()).owned(player.getUUID());
  if(matches.size()!=1){
   tell(player,matches.isEmpty()?
    "no indexed suit; load older v1.7 suit's chunk once to register it.":
    "several owned suits indexed; refusing ambiguous recall.");
   return 0;
  }
  var loc=matches.get(0);
  ServerLevel world=source(player.level().getServer(),loc);
  if(world==null){tell(player,"original dimension is unavailable.");return 0;}
  BlockPos bp=BlockPos.containing(loc.x(),loc.y(),loc.z());
  // NeoForge source ticket supports unloaded chunks and remote dimensions.
  boolean ticketed=PowerArmorRecallTickets.ticket(world,player.getUUID(),
    bp.getX()>>4,bp.getZ()>>4,true);
  if(!ticketed&&!world.hasChunkAt(bp)){
   tell(player,"unable to load original suit chunk.");return 0;
  }
  ACTIVE.put(player.getUUID(),new Flight(loc,null,0,false));
  tell(player,"signal acquired. Suit approaching from about 16 blocks.");
  return 1;
 }
 /** Auto-register legacy suits when their chunks are first opened. */
 @SubscribeEvent public static void join(EntityJoinLevelEvent e){
  if(!(e.getLevel() instanceof ServerLevel world)
    ||!(e.getEntity() instanceof ArmorStand stand)
    ||!stand.entityTags().contains(MARKER)||!PowerArmorSuitWorld.full(stand))return;
  for(String tag:stand.entityTags())if(tag.startsWith(OWNER)){
   try{
    PowerArmorRecallIndex.get(world.getServer()).index(stand,world,
      UUID.fromString(tag.substring(OWNER.length())));
   }catch(IllegalArgumentException ignored){}
   break;
  }
 }
 @SubscribeEvent public static void leave(EntityLeaveLevelEvent e){
  if(!(e.getLevel() instanceof ServerLevel world)
     ||!(e.getEntity() instanceof ArmorStand stand)
     ||!stand.entityTags().contains(MARKER))return;
  // V172_STALE_INDEX_GUARD: suit activation discards the world entity
  // while it still contains all four armor pieces. Unloading a chunk
  // must NOT erase the durable cross-dimension location entry.
  var reason=stand.getRemovalReason();
  if(reason!=null&&reason.shouldDestroy())
   PowerArmorRecallIndex.get(world.getServer()).remove(stand.getUUID());
 }
 @SubscribeEvent public static void logout(PlayerEvent.PlayerLoggedOutEvent e){
  if(e.getEntity() instanceof ServerPlayer player){
   Flight f=ACTIVE.get(player.getUUID());
   if(f!=null)release(player,f);
  }
 }
 @SubscribeEvent public static void tick(PlayerTickEvent.Post e){
  if(!(e.getEntity() instanceof ServerPlayer player))return;
  Flight f=ACTIVE.get(player.getUUID());if(f==null)return;
  ServerLevel world=source(player.level().getServer(),f.loc());
  if(world==null){abort(player,f,"source dimension unavailable.");return;}
  Entity entity=world.getEntity(f.loc().suitUUID());
  ArmorStand stand=entity instanceof ArmorStand a?a:null;
  if(!f.ready()){
   if(stand==null){
    if(f.ticks()>=MAX_PREPARE){abort(player,f,"source chunk timed out.");return;}
    ACTIVE.put(player.getUUID(),new Flight(f.loc(),null,f.ticks()+1,false));
    return;
   }
   if(!owned(stand,player.getUUID())||PowerArmorRuntime.full(player)){
    abort(player,f,"source suit invalid or no longer owned.");return;
   }
   int tier=PowerArmorRuntime.tier(stand.getItemBySlot(EquipmentSlot.HEAD),0);
   if(tier<1||tier>24){abort(player,f,"invalid MK tier.");return;}
   PowerArmorVisualEntity visual=new PowerArmorVisualEntity(kind(tier),player.level());
   visual.addTag(VISUAL);
   visual.setNoGravity(true);
   visual.begin(false);
   if(!locate(player,visual)||!player.level().addFreshEntity(visual)){
    abort(player,f,"no safe 16-block arrival location.");return;
   }
   ACTIVE.put(player.getUUID(),new Flight(f.loc(),visual.getUUID(),0,true));
   return;
  }
  Entity display=player.level().getEntity(f.visual());
  if(!(display instanceof PowerArmorVisualEntity visual)||visual.isRemoved()){
   abort(player,f,"flight animation unavailable.");return;
  }
  if(!owned(stand,player.getUUID())||!player.isAlive()||player.isSpectator()
    ||PowerArmorRuntime.full(player)
    ||ArmorLoadoutData.get(player.level().getServer()).has(player)){
   abort(player,f,"source or player changed during recall.");return;
  }
  if(f.ticks()>MAX_FLIGHT){abort(player,f,"flight timeout.");return;}
  Vec3 delta=player.position().subtract(visual.position());
  double distance=delta.length();
  if(distance<=2.5D){
   // Commit equipment transfer ONLY after visual arrival.
   boolean success=PowerArmorSuitWorld.recallEquip(stand,player);
   if(success)PowerArmorRecallIndex.get(player.level().getServer()).remove(stand.getUUID());
   release(player,f);
   tell(player,success?"suit engaged safely.":
     "entry failed; your suit is intact at the old location.");
   return;
  }
  Vec3 move=delta.scale(Math.min(SPEED,distance-2D)/distance);
  Vec3 next=visual.position().add(move);
  if(!player.level().hasChunkAt(BlockPos.containing(next))
      ||!player.level().noCollision(visual,visual.getBoundingBox().move(move))){
   abort(player,f,"flight path blocked or chunk unloaded.");return;
  }
  visual.setPos(next.x,next.y,next.z);
  float yaw=(float)Math.toDegrees(Math.atan2(-move.x,move.z));
  visual.setYRot(yaw);
  visual.setYBodyRot(yaw);
  visual.setYHeadRot(yaw);
  if(f.ticks()%3==0)player.level().sendParticles(ParticleTypes.END_ROD,
    visual.getX(),visual.getY()+.7D,visual.getZ(),3,.18D,.2D,.18D,.02D);
  ACTIVE.put(player.getUUID(),new Flight(f.loc(),f.visual(),f.ticks()+1,true));
 }
}
'''.replace("VISUAL_CASES",visual_cases)
write("powerarmor/PowerArmorRecall.java",core)

write("powerarmor/PowerArmorRecallPayload.java",r'''package dev.obsidiannetwork.powerarmor;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;
public record PowerArmorRecallPayload() implements CustomPacketPayload {
 public static final Type<PowerArmorRecallPayload> TYPE=new Type<>(
  Identifier.fromNamespaceAndPath("obsidiannetwork","power_armor_recall"));
 public static final StreamCodec<RegistryFriendlyByteBuf,PowerArmorRecallPayload> STREAM_CODEC=
  StreamCodec.unit(new PowerArmorRecallPayload());
 @Override public Type<? extends CustomPacketPayload> type(){return TYPE;}
 @EventBusSubscriber(modid="obsidiannetwork")
 public static final class Handler {
  private Handler(){}
  @SubscribeEvent public static void register(RegisterPayloadHandlersEvent e){
   e.registrar("1").playToServer(TYPE,STREAM_CODEC,
     (payload,context)->{
      if(context.player() instanceof ServerPlayer p)PowerArmorRecall.request(p);
     });
  }
 }
}
''')
write("powerarmor/PowerArmorRecallKeyClient.java",r'''package dev.obsidiannetwork.powerarmor;
import com.mojang.blaze3d.platform.InputConstants;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import net.neoforged.neoforge.client.event.RegisterKeyMappingsEvent;
import org.lwjgl.glfw.GLFW;
/** V172_RECALL_KEY: R, rebindable under Controls; V remains armor exit. */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class PowerArmorRecallKeyClient {
 private PowerArmorRecallKeyClient(){}
 private static final KeyMapping RECALL=new KeyMapping(
   "key.obsidiannetwork.power_armor_recall",
   InputConstants.Type.KEYSYM,GLFW.GLFW_KEY_R,KeyMapping.Category.MISC);
 @SubscribeEvent public static void register(RegisterKeyMappingsEvent e){e.register(RECALL);}
 @SubscribeEvent public static void tick(ClientTickEvent.Post e){
  while(RECALL.consumeClick()){
   Minecraft mc=Minecraft.getInstance();
   if(mc.player==null||mc.screen!=null)continue;
   net.neoforged.neoforge.client.network.ClientPacketDistributor.sendToServer(
     new PowerArmorRecallPayload());
  }
 }
}
''')
edit("powerarmor/PowerArmorCommands.java",
 '''   .then(Commands.literal("status").executes(c->PowerArmorSuitWorld.status(c.getSource().getPlayerOrException())))''',
 '''   .then(Commands.literal("status").executes(c->PowerArmorSuitWorld.status(c.getSource().getPlayerOrException())))
   .then(Commands.literal("recall").executes(c->PowerArmorRecall.request(c.getSource().getPlayerOrException())))''')
for lang,label in (("de_de","Power Armor herbeirufen"),("en_us","Recall Power Armor")):
 path=assets/"lang"/(lang+".json");d=json.loads(path.read_text(encoding="utf-8"))
 assert "key.obsidiannetwork.power_armor_recall" not in d
 d["key.obsidiannetwork.power_armor_recall"]=label
 path.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

assert "V172_UNLIMITED_CROSS_DIM_RECALL" in core
assert "PowerArmorRecallTickets.ticket(world,player.getUUID()" in core
assert "PowerArmorSuitWorld.recallEquip(stand,player)" in core
assert "nearby" not in core and "MAX_RANGE" not in core
assert "On any failure" in __doc__
print("V172_UNLIMITED_CROSS_DIM_RECALL PASS: indexed cross-dimension/any-distance, 16-block GeckoLib flight, native source backup remains until safe final entry")
