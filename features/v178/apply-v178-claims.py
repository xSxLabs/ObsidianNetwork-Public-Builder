#!/usr/bin/env python3
"""v1.7.8 original chunk ownership, NeoForge force tickets and graphical map.

Server-authoritative claims, 2 independent configurable quotas, trusted player
UUIDs, world-scoped atomic persistence, zero per-tick world scans. The map
sends a bounded 25x25 ownership snapshot only on requests and changes.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def emit(rel,source):
 p=J/rel
 p.parent.mkdir(parents=True,exist_ok=True)
 assert not p.exists(),("V178_CLAIMS_DUPLICATE",rel)
 p.write_text(source,encoding="utf-8")

emit("claims/V178Claims.java",r'''package dev.obsidiannetwork.claims;

import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.storage.LevelResource;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.world.chunk.TicketController;
import net.neoforged.neoforge.common.world.chunk.RegisterTicketControllersEvent;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.event.server.ServerStoppedEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import net.neoforged.neoforge.event.level.BlockEvent;
import net.neoforged.neoforge.event.level.ExplosionEvent;
import net.neoforged.neoforge.event.level.PistonEvent;
import net.neoforged.neoforge.event.level.block.BreakBlockEvent;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;
import net.neoforged.neoforge.network.PacketDistributor;
import java.io.*;
import java.nio.file.*;
import java.util.*;

/** Each entry is looked up by dimension + packed chunk position in O(1).
 *  No server-tick sweeps and no automatic world generation.
 *  NeoForge ticket controller owns (and persists) loaded chunks, NOT vanilla
 *  /forceload, so it cannot override a player's vanilla chunk forcing.
 */
@EventBusSubscriber(modid="obsidiannetwork")
public final class V178Claims {
 private V178Claims(){}
 public static final int MAX_CLAIMS=Math.min(2048,Math.max(1,Integer.getInteger("xsxlabs.claims.max",256)));
 public static final int MAX_LOADED=Math.min(256,Math.max(0,Integer.getInteger("xsxlabs.claims.loaded",25)));
 public static final int VIEW_RADIUS=12; // Exactly 25x25, 625 byte payload.
 public static final TicketController TICKETS=new TicketController(
       Identifier.fromNamespaceAndPath("obsidiannetwork","v178_claims"));
 private record Claim(UUID owner,boolean loaded){}
 private static final Map<String,Map<Long,Claim>> CLAIMS=new HashMap<>();
 private static final Map<UUID,Set<UUID>> TRUSTED=new HashMap<>();
 private static final Map<UUID,Integer> OWNED_COUNT=new HashMap<>();
 private static final Map<UUID,Integer> LOADED_COUNT=new HashMap<>();
 private static MinecraftServer active;
 private static boolean dirty;
 private static final String FILE_NAME="xsxlabs-v178-claims.tsv";
 private static final Map<UUID,Long> REQUEST_TICKS=new HashMap<>();
 private static final Map<UUID,Long> REQUEST_CENTERS=new HashMap<>();
 public static void handleRequest(ServerPlayer p,int x,int z){
  if(!(p.level() instanceof ServerLevel level))return;
  if(Math.abs((long)x)>1875000||Math.abs((long)z)>1875000)return;
  int px=p.blockPosition().getX()>>4,pz=p.blockPosition().getZ()>>4;
  if(Math.abs((long)x-px)>256||Math.abs((long)z-pz)>256)return;
  long now=level.getGameTime();
  long prev=REQUEST_TICKS.getOrDefault(p.getUUID(),Long.MIN_VALUE);
  if(prev!=Long.MIN_VALUE&&now>=prev&&now-prev<20)return;
  REQUEST_TICKS.put(p.getUUID(),now);
  REQUEST_CENTERS.put(p.getUUID(),key(x,z));
  send(p,x,z);
 }

 private static String dimension(ServerLevel level){
  return level.dimension().identifier().toString();
 }
 private static long key(int x,int z){
  return ((long)x<<32)|(z&0xffffffffL);
 }
 private static Map<Long,Claim> map(ServerLevel level){
  return CLAIMS.computeIfAbsent(dimension(level),ignored->new HashMap<>());
 }
 private static Path path(MinecraftServer server){
  return server.getWorldPath(LevelResource.ROOT).resolve("data").resolve(FILE_NAME);
 }
 private static void count(UUID owner,int claimed,int loaded){
  OWNED_COUNT.merge(owner,claimed,Integer::sum);
  LOADED_COUNT.merge(owner,loaded,Integer::sum);
 }
 private static void ensure(ServerLevel level){
  if(active==level.getServer())return;
  CLAIMS.clear();TRUSTED.clear();OWNED_COUNT.clear();LOADED_COUNT.clear();REQUEST_TICKS.clear();REQUEST_CENTERS.clear();
  active=level.getServer();dirty=false;
  Path source=path(active);
  if(!Files.isRegularFile(source))return;
  try(BufferedReader reader=Files.newBufferedReader(source)){
   String line;int total=0;
   while((line=reader.readLine())!=null&&total++<524288){
    try{
     String[] s=line.split("\t",-1);
     if(s.length==4&&s[0].equals("T")){
      UUID owner=UUID.fromString(s[1]),other=UUID.fromString(s[2]);
      if(!owner.equals(other))TRUSTED.computeIfAbsent(owner,k->new HashSet<>()).add(other);
     }else if(s.length==6&&s[0].equals("C")){
      String dim=s[1];int x=Integer.parseInt(s[2]),z=Integer.parseInt(s[3]);
      UUID owner=UUID.fromString(s[4]);boolean loaded=s[5].equals("1");
      if(Math.abs((long)x)>1875000||Math.abs((long)z)>1875000)continue;
      if(OWNED_COUNT.getOrDefault(owner,0)>=MAX_CLAIMS)continue;
      if(loaded&&LOADED_COUNT.getOrDefault(owner,0)>=MAX_LOADED)loaded=false;
      var claims=CLAIMS.computeIfAbsent(dim,k->new HashMap<Long,Claim>());
      if(claims.putIfAbsent(key(x,z),new Claim(owner,loaded))==null)
       count(owner,1,loaded?1:0);
     }
    }catch(RuntimeException malformed){/* ignore invalid saved line */}
   }
  }catch(IOException ex){System.err.println("[xSxLabs] claim read failed: "+ex);}
 }
 private static void save(){
  if(active==null||!dirty)return;
  StringBuilder data=new StringBuilder(8192);
  for(var dim:CLAIMS.entrySet()){
   for(var entry:dim.getValue().entrySet()){
    long key=entry.getKey();Claim c=entry.getValue();
    data.append("C\t").append(dim.getKey()).append('\t')
      .append((int)(key>>32)).append('\t').append((int)key).append('\t')
      .append(c.owner()).append('\t').append(c.loaded()?1:0).append('\n');
   }
  }
  for(var owner:TRUSTED.entrySet())for(UUID other:owner.getValue())
   data.append("T\t").append(owner.getKey()).append('\t').append(other)
      .append("\t-\n");
  Path destination=path(active),temporary=null;
  try{
   Files.createDirectories(destination.getParent());
   temporary=Files.createTempFile(destination.getParent(),"xsx-claims-",".tmp");
   Files.writeString(temporary,data.toString());
   try{Files.move(temporary,destination,StandardCopyOption.REPLACE_EXISTING,
                  StandardCopyOption.ATOMIC_MOVE);}
   catch(AtomicMoveNotSupportedException ex){
    Files.move(temporary,destination,StandardCopyOption.REPLACE_EXISTING);
   }
   dirty=false;
  }catch(IOException ex){
   System.err.println("[xSxLabs] claim save failed: "+ex);
  }finally{
   if(temporary!=null)try{Files.deleteIfExists(temporary);}catch(IOException ignored){}
  }
 }
 public static UUID owner(ServerLevel level,BlockPos pos){
  ensure(level);
  Claim claim=map(level).get(key(pos.getX()>>4,pos.getZ()>>4));
  return claim==null?null:claim.owner();
 }
 public static boolean mayModify(ServerLevel level,BlockPos pos,UUID player){
  UUID owner=owner(level,pos);
  return owner==null||owner.equals(player)
      ||TRUSTED.getOrDefault(owner,Set.of()).contains(player);
 }
 public static boolean mayMachineMine(ServerLevel level,BlockPos pos,UUID owner){
  return owner!=null&&mayModify(level,pos,owner);
 }
 @SubscribeEvent public static void registerTickets(RegisterTicketControllersEvent event){
  event.register(TICKETS);
 }
 @SubscribeEvent public static void started(ServerStartedEvent event){
  for(ServerLevel level:event.getServer().getAllLevels()){
   ensure(level);
   for(var e:map(level).entrySet())if(e.getValue().loaded()){
    int x=(int)(e.getKey()>>32),z=(int)(long)e.getKey();
    TICKETS.forceChunk(level,e.getValue().owner(),x,z,true,true);
   }
  }
 }
 // Deferred save avoids synchronous disk IO on every map click.
 @SubscribeEvent public static void autosave(ServerTickEvent.Post event){
  if(active==event.getServer()&&dirty&&event.hasTime()
     &&event.getServer().getTickCount()%40==0)save();
 }
 @SubscribeEvent public static void stopped(ServerStoppedEvent event){
  if(active==event.getServer()){save();active=null;CLAIMS.clear();
    TRUSTED.clear();OWNED_COUNT.clear();LOADED_COUNT.clear();REQUEST_TICKS.clear();REQUEST_CENTERS.clear();dirty=false;}
 }
 @SubscribeEvent public static void breakBlock(BreakBlockEvent event){
  if(event.getLevel() instanceof ServerLevel level
    &&event.getPlayer() instanceof ServerPlayer player
    &&!mayModify(level,event.getPos(),player.getUUID()))
   event.setCanceled(true);
 }
 @SubscribeEvent public static void place(BlockEvent.EntityPlaceEvent event){
  if(!(event.getLevel() instanceof ServerLevel level))return;
  UUID responsible=event.getEntity() instanceof ServerPlayer player
    ?player.getUUID():null;
  // If an automation/fake entity can't prove ownership, never let it bypass
  // a claimed border. Unclaimed world behavior remains completely unchanged.
  UUID owner=owner(level,event.getPos());
  if(owner!=null&&(responsible==null||!mayModify(level,event.getPos(),responsible)))
   event.setCanceled(true);
 }
 @SubscribeEvent public static void interact(PlayerInteractEvent.RightClickBlock event){
  if(event.getLevel() instanceof ServerLevel level
     &&event.getEntity() instanceof ServerPlayer player
     &&!mayModify(level,event.getPos(),player.getUUID()))
   event.setCanceled(true);
 }
 // B1643: server-authoritative explosion block protection. No chunk loading,
 // no event cancellation affecting the rest of the explosion or unclaimed blocks.
 @SubscribeEvent public static void protectExplosion(ExplosionEvent.Detonate event){
  if(!(event.getLevel() instanceof ServerLevel level))return;
  ensure(level);
  Map<Long,Claim> claims=map(level);
  if(claims.isEmpty())return;
  event.getAffectedBlocks().removeIf(pos->
    claims.containsKey(key(pos.getX()>>4,pos.getZ()>>4)));
 }
 // B1643: fail-closed at piston claim borders; a moving piston must not
 // move blocks into or out of a claimed cell without an accountable player.
 @SubscribeEvent public static void protectPiston(PistonEvent.Pre event){
  if(!(event.getLevel() instanceof ServerLevel level))return;
  ensure(level);
  Map<Long,Claim> claims=map(level);
  if(claims.isEmpty())return;
  // B1645_PISTON_CHAIN_GUARD: a piston can move a chain of up to 12
  // blocks. Checking only the adjacent block leaves protected chunks open
  // to long pushes. Check both directions to cover sticky retraction too.
  // B1661_PISTON_SAME_OWNER: previous code canceled every piston wholly
  // inside a claimed area. Allow same-owner piston lines but fail closed if
  // any possible moved block crosses an owner/unclaimed claim boundary.
  // Conservative 25 hash lookups, no block reads and no chunk loading.
  BlockPos piston=event.getPos();
  Claim source=claims.get(key(piston.getX()>>4,piston.getZ()>>4));
  UUID sourceOwner=source==null?null:source.owner();
  for(int distance=-12;distance<=12;distance++){
   BlockPos affected=piston.relative(event.getDirection(),distance);
   Claim touched=claims.get(key(affected.getX()>>4,affected.getZ()>>4));
   UUID affectedOwner=touched==null?null:touched.owner();
   if(!Objects.equals(sourceOwner,affectedOwner)){
    event.setCanceled(true);
    return;
   }
  }
 }
 private static void tell(ServerPlayer p,String msg){
  p.sendSystemMessage(Component.literal("[xSxLabs Chunks] "+msg));
 }
 private static boolean edit(ServerPlayer player,String action,int cx,int cz){
  if(!(player.level() instanceof ServerLevel level))return false;
  ensure(level);
  if(Math.abs((long)cx)>1875000||Math.abs((long)cz)>1875000)return false;
  Map<Long,Claim> set=map(level);
  long k=key(cx,cz);Claim before=set.get(k);UUID id=player.getUUID();
  switch(action){
   case "claim" -> {
    if(before!=null||OWNED_COUNT.getOrDefault(id,0)>=MAX_CLAIMS)return false;
    set.put(k,new Claim(id,false));count(id,1,0);
   }
   case "unclaim" -> {
    if(before==null||!before.owner().equals(id))return false;
    if(before.loaded())TICKETS.forceChunk(level,id,cx,cz,false,true);
    set.remove(k);count(id,-1,before.loaded()?-1:0);
   }
   case "load" -> {
    if(before==null||!before.owner().equals(id)||before.loaded()
        ||LOADED_COUNT.getOrDefault(id,0)>=MAX_LOADED)return false;
    if(!TICKETS.forceChunk(level,id,cx,cz,true,true))return false;
    set.put(k,new Claim(id,true));count(id,0,1);
   }
   case "unload" -> {
    if(before==null||!before.owner().equals(id)||!before.loaded())return false;
    TICKETS.forceChunk(level,id,cx,cz,false,true);
    set.put(k,new Claim(id,false));count(id,0,-1);
   }
   default -> {return false;}
  }
  dirty=true;
  tell(player,action+" ["+cx+","+cz+"] | "+
     OWNED_COUNT.getOrDefault(id,0)+"/"+MAX_CLAIMS+" claimed, "+
     LOADED_COUNT.getOrDefault(id,0)+"/"+MAX_LOADED+" loaded.");
  // Keep the map centered after changing a cell at its border.
  Long center=REQUEST_CENTERS.get(id);
  if(center==null)send(player,cx,cz);
  else send(player,(int)(center>>32),(int)(long)center);
  return true;
 }
 public static void send(ServerPlayer p,int cx,int cz){
  if(!(p.level() instanceof ServerLevel level))return;
  ensure(level);
  byte[] statuses=new byte[(2*VIEW_RADIUS+1)*(2*VIEW_RADIUS+1)];
  var claims=map(level);
  for(int z=-VIEW_RADIUS;z<=VIEW_RADIUS;z++)
   for(int x=-VIEW_RADIUS;x<=VIEW_RADIUS;x++){
    Claim c=claims.get(key(cx+x,cz+z));
    if(c==null)continue;
    int status=c.owner().equals(p.getUUID())?1:
      TRUSTED.getOrDefault(c.owner(),Set.of()).contains(p.getUUID())?2:3;
    if(c.loaded())status|=4;
    statuses[(z+VIEW_RADIUS)*(2*VIEW_RADIUS+1)+x+VIEW_RADIUS]=(byte)status;
   }
  PacketDistributor.sendToPlayer(p,new V178ClaimsSnapshot(
       dimension(level),cx,cz,VIEW_RADIUS,statuses));
 }
 private static int run(ServerPlayer p,String action,int x,int z){
  if(action.equals("view")){send(p,x,z);return 1;}
  boolean ok=edit(p,action,x,z);
  if(!ok)tell(p,"Cannot "+action+" this chunk (ownership or quota).");
  return ok?1:0;
 }
 private static int own(ServerPlayer p,String action){
  return run(p,action,p.blockPosition().getX()>>4,p.blockPosition().getZ()>>4);
 }
 private static int trust(ServerPlayer p,String name,boolean trust){
  ensure((ServerLevel)p.level());
  ServerPlayer other=p.level().getServer().getPlayerList().getPlayerByName(name);
  UUID target=other==null?null:other.getUUID();
  // B1655: Offline removal accepts a previously trusted UUID; grants still
  // require an online player to avoid granting a mistyped identity.
  if(!trust&&target==null){
   try{target=UUID.fromString(name);}catch(IllegalArgumentException ignored){}
  }
  if(target==null||target.equals(p.getUUID())){
   tell(p,trust?"Player must be online.":"Enter an online player or trusted UUID.");
   return 0;
  }
  var trusted=TRUSTED.get(p.getUUID());
  if(!trust&&(trusted==null||!trusted.contains(target))){
   tell(p,"Player is not trusted.");return 0;
  }
  if(trusted==null)trusted=TRUSTED.computeIfAbsent(p.getUUID(),k->new HashSet<>());
  boolean changed=trust?trusted.add(target):trusted.remove(target);
  if(trusted.isEmpty())TRUSTED.remove(p.getUUID());
  if(!changed){tell(p,"Trust permissions already match.");return 0;}
  dirty=true;
  tell(p,(trust?"Trusted ":"Untrusted ")+(other!=null?other.getGameProfile().name():target));
  return 1;
 }
 // B1661_TRUST_ROSTER: owner-only, bounded audit of trusted UUIDs.
 // Members can be revoked offline using /xsxchunks untrust UUID.
 private static int listTrust(ServerPlayer p){
  ensure((ServerLevel)p.level());
  Set<UUID> trusted=TRUSTED.getOrDefault(p.getUUID(),Set.of());
  tell(p,"Trusted players: "+trusted.size());
  int displayed=0;
  for(UUID member:trusted){
   if(displayed++>=64)break;
   tell(p,"Trusted UUID: "+member);
  }
  if(trusted.size()>64)tell(p,"Showing first 64; untrust by UUID.");
  return 1;
 }
 @SubscribeEvent public static void commands(RegisterCommandsEvent event){
  var root=Commands.literal("xsxchunks");
  for(String action:new String[]{"claim","unclaim","load","unload","view"}){
   final String a=action;
   root.then(Commands.literal(a)
     .executes(c->own(c.getSource().getPlayerOrException(),a))
     .then(Commands.argument("x",IntegerArgumentType.integer(-1875000,1875000))
       .then(Commands.argument("z",IntegerArgumentType.integer(-1875000,1875000))
         .executes(c->run(c.getSource().getPlayerOrException(),a,
             IntegerArgumentType.getInteger(c,"x"),IntegerArgumentType.getInteger(c,"z"))))));
  }
  root.then(Commands.literal("trust").then(Commands.argument("player",StringArgumentType.word())
      .executes(c->trust(c.getSource().getPlayerOrException(),
          StringArgumentType.getString(c,"player"),true))));
  root.then(Commands.literal("untrust").then(Commands.argument("player",StringArgumentType.word())
      .executes(c->trust(c.getSource().getPlayerOrException(),
          StringArgumentType.getString(c,"player"),false))));
  root.then(Commands.literal("trusted")
      .executes(c->listTrust(c.getSource().getPlayerOrException())));
  event.getDispatcher().register(root);
 }
}
''')

emit("claims/V178ClaimsSnapshot.java",r'''package dev.obsidiannetwork.claims;

import io.netty.buffer.ByteBuf;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.Identifier;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;

/** Bounded 625-byte immutable ownership snapshot, not terrain or chunk data. */
@EventBusSubscriber(modid="obsidiannetwork")
public record V178ClaimsSnapshot(String dimension,int cx,int cz,int radius,
                                  byte[] statuses) implements CustomPacketPayload {
 public static final Type<V178ClaimsSnapshot> TYPE=new Type<>(
       Identifier.fromNamespaceAndPath("obsidiannetwork","v178_claims_snapshot"));
 public static final StreamCodec<RegistryFriendlyByteBuf,V178ClaimsSnapshot> CODEC=
     StreamCodec.of(
       (buf,msg)->{
        buf.writeUtf(msg.dimension,150);
        buf.writeVarInt(msg.cx);buf.writeVarInt(msg.cz);
        buf.writeVarInt(msg.radius);
        buf.writeByteArray(msg.statuses);
       },
       buf->{
        String dimension=buf.readUtf(150);
        int cx=buf.readVarInt(),cz=buf.readVarInt(),radius=buf.readVarInt();
        byte[] statuses=buf.readByteArray(625);
        if(radius!=12||statuses.length!=625)
         throw new IllegalArgumentException("invalid claims map payload");
        return new V178ClaimsSnapshot(dimension,cx,cz,radius,statuses);
       });
 @Override public Type<? extends CustomPacketPayload> type(){return TYPE;}
 @SubscribeEvent public static void payloads(RegisterPayloadHandlersEvent event){
  event.registrar("1").playToClient(TYPE,CODEC);
 }
}
''')

emit("claims/V178ClaimsRequest.java",r'''package dev.obsidiannetwork.claims;

import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;

@EventBusSubscriber(modid="obsidiannetwork")
public record V178ClaimsRequest(int cx,int cz) implements CustomPacketPayload{
 public static final Type<V178ClaimsRequest> TYPE=new Type<>(
   Identifier.fromNamespaceAndPath("obsidiannetwork","v178_claims_request"));
 public static final StreamCodec<RegistryFriendlyByteBuf,V178ClaimsRequest> CODEC=
  StreamCodec.of((buf,p)->{buf.writeVarInt(p.cx());buf.writeVarInt(p.cz());},
                 buf->new V178ClaimsRequest(buf.readVarInt(),buf.readVarInt()));
 @Override public Type<? extends CustomPacketPayload> type(){return TYPE;}
 @SubscribeEvent public static void payloads(RegisterPayloadHandlersEvent event){
  event.registrar("1").playToServer(TYPE,CODEC,(request,context)->{
   if(context.player() instanceof ServerPlayer player)
    V178Claims.handleRequest(player,request.cx(),request.cz());
  });
 }
}
''')

emit("client/V178ClaimsClient.java",r'''package dev.obsidiannetwork.client;

import dev.obsidiannetwork.claims.V178ClaimsSnapshot;
import com.mojang.blaze3d.platform.InputConstants;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.RegisterKeyMappingsEvent;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import net.neoforged.neoforge.client.event.RenderGuiEvent;
import net.neoforged.neoforge.client.network.event.RegisterClientPayloadHandlersEvent;
import org.lwjgl.glfw.GLFW;

/** An independently authored chunk-map interface. No per-frame terrain scan
 * and no chunk loads. Server sends 625 tiny status bytes on demand only.
 */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class V178ClaimsClient {
 private V178ClaimsClient(){}
 private static final KeyMapping WORLD_MAP=new KeyMapping(
   "key.obsidiannetwork.chunk_map",InputConstants.Type.KEYSYM,GLFW.GLFW_KEY_M,
     KeyMapping.Category.MISC);
 private static volatile V178ClaimsSnapshot last;
 private static int lastRequestX=Integer.MIN_VALUE,lastRequestZ=Integer.MIN_VALUE;
 private static long lastRequestTime=Long.MIN_VALUE;
 private static boolean minimap=true;
 private static boolean showGrid=true,showForceLoaded=true,showCoordinates=true;
 private static final KeyMapping TOGGLE_MINIMAP=new KeyMapping(
   "key.obsidiannetwork.toggle_claim_minimap",InputConstants.Type.KEYSYM,GLFW.GLFW_KEY_N,
     KeyMapping.Category.MISC);
 public static void toggleGrid(){showGrid=!showGrid;}
 public static void toggleForceLoaded(){showForceLoaded=!showForceLoaded;}
 public static void toggleCoordinates(){showCoordinates=!showCoordinates;}
 public static boolean gridEnabled(){return showGrid;}
 public static boolean forceLoadedEnabled(){return showForceLoaded;}
 public static boolean coordinatesEnabled(){return showCoordinates;}
 @SubscribeEvent public static void bindings(RegisterKeyMappingsEvent event){
  event.register(WORLD_MAP);
  event.register(TOGGLE_MINIMAP);
 }
 @SubscribeEvent public static void payload(RegisterClientPayloadHandlersEvent event){
  event.register(V178ClaimsSnapshot.TYPE,(message,context)->last=message);
 }
 public static V178ClaimsSnapshot snapshot(){return last;}
 public static void request(int x,int z){
  Minecraft mc=Minecraft.getInstance();
  if(mc.player==null||mc.player.connection==null)return;
  if(Math.abs((long)x)>1875000||Math.abs((long)z)>1875000)return;
  lastRequestX=x;lastRequestZ=z;
  lastRequestTime=mc.level==null?0:mc.level.getGameTime();
  net.neoforged.neoforge.client.network.ClientPacketDistributor.sendToServer(new dev.obsidiannetwork.claims.V178ClaimsRequest(x,z));
 }
 public static void command(String action,int x,int z){
  Minecraft mc=Minecraft.getInstance();
  if(mc.player==null||mc.player.connection==null)return;
  mc.player.connection.sendCommand("xsxchunks "+action+" "+x+" "+z);
 }
 public static byte state(V178ClaimsSnapshot snapshot,int x,int z){
  if(snapshot==null)return 0;
  int dx=x-snapshot.cx(),dz=z-snapshot.cz(),r=snapshot.radius();
  if(dx< -r||dx>r||dz< -r||dz>r)return 0;
  return snapshot.statuses()[(dz+r)*(r*2+1)+dx+r];
 }
 static int shade(int state){
  return switch(state&3){
   case 1->0xdd4eae7d; // owned
   case 2->0xdd65c9d7; // trusted
   case 3->0xddbd6868; // other
   default->0x99506b77;
  };
 }
 @SubscribeEvent public static void tick(ClientTickEvent.Post event){
  Minecraft mc=Minecraft.getInstance();
  if(mc.player==null||mc.level==null){
   last=null;lastRequestX=Integer.MIN_VALUE;lastRequestZ=Integer.MIN_VALUE;
   return;
  }
  while(TOGGLE_MINIMAP.consumeClick())minimap=!minimap;
  while(WORLD_MAP.consumeClick()){
   if(mc.screen instanceof V178ClaimsMapScreen)mc.setScreen(null);
   else mc.setScreen(new V178ClaimsMapScreen());
  }
  // Update ONLY on crossing a chunk boundary or every 100 ticks, and never
  // when another GUI is open; keep full-screen map requests user-driven.
  if(mc.screen!=null)return;
  int x=mc.player.blockPosition().getX()>>4,z=mc.player.blockPosition().getZ()>>4;
  long tick=mc.level.getGameTime();
  if(tick<lastRequestTime||tick-lastRequestTime>=100
       ||Math.abs(x-lastRequestX)>=3||Math.abs(z-lastRequestZ)>=3)
   request(x,z);
 }
 @SubscribeEvent public static void overlay(RenderGuiEvent.Post event){
  Minecraft mc=Minecraft.getInstance();
  if(!minimap||mc.player==null||mc.screen!=null||last==null)return;
  if(!mc.player.level().dimension().identifier().toString().equals(last.dimension()))return;
  int ox=mc.getWindow().getGuiScaledWidth()-99,oy=9;
  GuiGraphicsExtractor g=event.getGuiGraphics();
  g.fill(ox-2,oy-2,ox+91,oy+97,0xc0081d2b);
  g.text(mc.font,showCoordinates?"CLAIMS "+(mc.player.blockPosition().getX()>>4)+","+(mc.player.blockPosition().getZ()>>4):"CLAIMS M",ox+3,oy+2,0xffb2ecfa);
  int cx=mc.player.blockPosition().getX()>>4,cz=mc.player.blockPosition().getZ()>>4;
  for(int dz=-3;dz<=3;dz++)for(int dx=-3;dx<=3;dx++){
   int x=ox+4+(dx+3)*12,y=oy+15+(dz+3)*11;
   int s=Byte.toUnsignedInt(state(last,cx+dx,cz+dz));
   g.fill(x,y,x+11,y+10,showGrid?shade(s):0xbb203545);
   if(showForceLoaded&&(s&4)!=0)g.fill(x+7,y+1,x+10,y+4,0xffffff90);
  }
  g.fill(ox+43,oy+45,ox+48,oy+50,0xffffffff);
 }
}
''')

emit("client/V178ClaimsMapScreen.java",r'''package dev.obsidiannetwork.client;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import dev.obsidiannetwork.claims.V178ClaimsSnapshot;

/** Click chunk to claim/unclaim, right-click to load/unload. Panning reads
 * only server's bounded ownership map; terrain scans are deliberately absent.
 */
public final class V178ClaimsMapScreen extends Screen {
 private int cx,cz;
 private static final int TILE=13,DIAMETER=25;
 public V178ClaimsMapScreen(){super(Component.literal("xSxLabs | World Chunks"));}
 @Override protected void init(){
  var p=Minecraft.getInstance().player;
  if(p!=null&&cx==0&&cz==0){
   cx=p.blockPosition().getX()>>4;cz=p.blockPosition().getZ()>>4;
  }
  V178ClaimsClient.request(cx,cz);
 }
 @Override public void extractBackground(GuiGraphicsExtractor g,int mx,int my,float delta){
  super.extractBackground(g,mx,my,delta);
  int tile=tile(),w=DIAMETER*tile,x0=(width-w)/2,y0=(height-w)/2;
  g.fill(x0-7,y0-26,x0+w+7,y0+w+29,0xed0a1826);
  g.text(font,"xSxLabs CHUNK CLAIMS | "+cx+", "+cz,x0,y0-19,0xff8ce9f1);
  V178ClaimsSnapshot map=V178ClaimsClient.snapshot();
  boolean good=map!=null&&map.cx()==cx&&map.cz()==cz;
  for(int z=0;z<DIAMETER;z++)for(int x=0;x<DIAMETER;x++){
   int cxWorld=cx+x-12,czWorld=cz+z-12;
   int state=good?Byte.toUnsignedInt(V178ClaimsClient.state(map,cxWorld,czWorld)):0;
   int px=x0+x*tile,py=y0+z*tile;
   g.fill(px,py,px+tile-1,py+tile-1,V178ClaimsClient.gridEnabled()?V178ClaimsClient.shade(state):0xbb203545);
   if(V178ClaimsClient.forceLoadedEnabled()&&(state&4)!=0)g.fill(px+Math.max(1,tile-4),py+1,px+tile-1,py+4,0xffffe083);
  }
  g.fill(x0+12*tile+1,y0+12*tile+1,x0+13*tile-1,y0+13*tile-1,0xffffffff);
  g.text(font,"L: claim  R: force  Arrows: pan  1: grid  2: force  3: coords",x0,y0+w+7,0xffb7d1e4);
  g.text(font,"N: minimap on/off | Overlay: "+(V178ClaimsClient.gridEnabled()?"grid ":"")+(V178ClaimsClient.forceLoadedEnabled()?"force ":"")+(V178ClaimsClient.coordinatesEnabled()?"coords":""),
      x0,y0+w+17,0xffb7d1e4);
  if(!good)g.text(font,"Loading 25x25 chunk ownership...",x0+2,y0+3,0xffffd38b);
 }
 private int tile(){return Math.min(TILE,Math.max(4,(Math.min(width,height)-85)/DIAMETER));}
 @Override public boolean mouseClicked(net.minecraft.client.input.MouseButtonEvent e,boolean doubleClick){
  double mx=e.x(),my=e.y();int button=e.button();
  int tile=tile(),w=DIAMETER*tile,x0=(width-w)/2,y0=(height-w)/2;
  if(mx>=x0&&mx<x0+w&&my>=y0&&my<y0+w&&(button==0||button==1)){
   int x=cx-12+((int)mx-x0)/tile,z=cz-12+((int)my-y0)/tile;
   var map=V178ClaimsClient.snapshot();
   if(map==null||map.cx()!=cx||map.cz()!=cz)return true;
   int state=Byte.toUnsignedInt(V178ClaimsClient.state(map,x,z));
   if(button==0)V178ClaimsClient.command((state&3)==1?"unclaim":"claim",x,z);
   else if((state&3)==1)V178ClaimsClient.command((state&4)!=0?"unload":"load",x,z);
   V178ClaimsClient.request(cx,cz);
   return true;
  }
  return super.mouseClicked(e,doubleClick);
 }
 @Override public boolean keyPressed(net.minecraft.client.input.KeyEvent e){
  int key=e.key();
  if(key==org.lwjgl.glfw.GLFW.GLFW_KEY_1){V178ClaimsClient.toggleGrid();return true;}
  if(key==org.lwjgl.glfw.GLFW.GLFW_KEY_2){V178ClaimsClient.toggleForceLoaded();return true;}
  if(key==org.lwjgl.glfw.GLFW.GLFW_KEY_3){V178ClaimsClient.toggleCoordinates();return true;}
  if(key==org.lwjgl.glfw.GLFW.GLFW_KEY_LEFT)cx-=6;
  else if(key==org.lwjgl.glfw.GLFW.GLFW_KEY_RIGHT)cx+=6;
  else if(key==org.lwjgl.glfw.GLFW.GLFW_KEY_UP)cz-=6;
  else if(key==org.lwjgl.glfw.GLFW.GLFW_KEY_DOWN)cz+=6;
  else return super.keyPressed(e);
  V178ClaimsClient.request(cx,cz);return true;
 }
 @Override public boolean isPauseScreen(){return false;}
}
''')
print("V178_CLAIMS_SERVER_TICKETS_CLAIM_QUOTA_MINIMAP_WORLDMAP_INSTALLED")


# B1646: fluid-triggered block formation (lava/water cobblestone, obsidian,
# lava ignition) must not mutate a claimed destination without a player.
# This event does not cover ordinary fluid spread; that remains a separate
# protection task requiring a verified flow hook.
claim_path=J/"claims/V178Claims.java"
fluid_source=claim_path.read_text(encoding="utf8")
fluid_anchor=''' // B1643: server-authoritative explosion block protection. No chunk loading,'''
fluid_guard='''  // B1646_FLUID_FORMATION_GUARD: block formation caused by fluids has no
  // accountable player. Cancel only if the destination belongs to a claim;
  // unclaimed cobblestone/obsidian formation remains unchanged.
  @SubscribeEvent public static void protectFluidFormation(BlockEvent.FluidPlaceBlockEvent event){
   if(!(event.getLevel() instanceof ServerLevel level))return;
   ensure(level);
   BlockPos destination=event.getPos();
   if(map(level).containsKey(key(destination.getX()>>4,destination.getZ()>>4)))
    event.setCanceled(true);
  }
'''
assert fluid_source.count(fluid_anchor)==1,"V178_FLUID_FORMATION_ANCHOR_MISSING_OR_DUPLICATED"
assert "protectFluidFormation(" not in fluid_source,"V178_FLUID_FORMATION_ALREADY_PRESENT"
fluid_source=fluid_source.replace(fluid_anchor,fluid_guard+fluid_anchor,1)
assert fluid_source.count("BlockEvent.FluidPlaceBlockEvent event")==1,"V178_FLUID_FORMATION_DUPLICATE"
assert "if(map(level).containsKey(key(destination.getX()>>4,destination.getZ()>>4)))" in fluid_source,"V178_FLUID_FORMATION_CLAIM_CHECK_MISSING"
assert "event.setCanceled(true);" in fluid_guard,"V178_FLUID_FORMATION_CANCEL_MISSING"
claim_path.write_text(fluid_source,encoding="utf8")
print("V178_B1646_FLUID_FORMATION_GUARD_PASS")
