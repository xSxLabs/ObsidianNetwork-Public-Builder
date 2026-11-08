#!/usr/bin/env python3
"""v1.7.7 J.A.R.V.I.S. /sethome bridge, no optional dependency.

Tracks SUCCESSFUL third-party Brigadier /sethome and /delhome commands without
registering or overriding either command. Server-owned persistent player homes,
dimension-aware proximity and a single transition-only client payload.
Build-time source injection runs after apply-v177-jarvis-voice.py.
"""
import os
from pathlib import Path

ROOT = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork"

def patch(rel, old, new):
    file = ROOT / rel
    data = file.read_text(encoding="utf-8")
    assert data.count(old) == 1, ("V177_SETHOME_SOURCE_DRIFT", rel, data.count(old), old[:100])
    file.write_text(data.replace(old, new, 1), encoding="utf-8")

def add(rel, java):
    file = ROOT / rel
    file.parent.mkdir(parents=True, exist_ok=True)
    assert not file.exists(), ("V177_SETHOME_DUPLICATE", rel)
    file.write_text(java, encoding="utf-8")

patch("client/V177JarvisClient.java",
      " private static boolean nearHome=false;",
      " private static boolean nearHome=false;\n"
      " private static boolean nearCommandHome=false;\n"
      " public static void setNearCommandHome(boolean value){nearCommandHome=value;}\n")

patch("client/V177JarvisClient.java",
''' private static void checkHome(LocalPlayer p){
  if(!V177JarvisSettings.on("home"))return;
  // 26.1 replaced getSharedSpawnPos with synchronized respawn data.
  // /sethome is mod-specific and cannot be inferred from world spawn.
  var data=p.level().getRespawnData();
  if(data==null||!data.dimension().equals(p.level().dimension()))return;
  BlockPos home=data.pos();
  double distance=p.distanceToSqr(home.getX()+.5,home.getY()+.5,home.getZ()+.5);
  if(!nearHome&&distance<=64D){
   nearHome=true;
   enqueue(2,"Welcome home, sir.","Willkommen zu Hause, Sir.");
  }else if(nearHome&&distance>=144D)nearHome=false;
 }''',
''' private static void checkHome(LocalPlayer p){
  if(!V177JarvisSettings.on("home"))return;
  // Combine vanilla world spawn and successful third-party /sethome locations.
  // Per-server home locations never leak to the client, only a proximity flag.
  var data=p.level().getRespawnData();
  boolean atSpawn=false;
  boolean pastSpawn=true;
  if(data!=null&&data.dimension().equals(p.level().dimension())){
   BlockPos home=data.pos();
   double sq=p.distanceToSqr(home.getX()+.5,home.getY()+.5,home.getZ()+.5);
   atSpawn=sq<=64D;
   pastSpawn=sq>=144D;
  }
  if(!nearHome&&(nearCommandHome||atSpawn)){
   nearHome=true;
   enqueue(2,"Welcome home, sir.","Willkommen zu Hause, Sir.");
  }else if(nearHome&&!nearCommandHome&&!atSpawn&&pastSpawn)nearHome=false;
 }''')

patch("client/V177JarvisClient.java",
      '  if(mc.player==null){wasInArmor=false;return;}',
      '  if(mc.player==null){wasInArmor=false;nearHome=false;nearCommandHome=false;return;}')

add("powerarmor/V177HomeIndex.java",r'''package dev.obsidiannetwork.powerarmor;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import java.util.*;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.saveddata.SavedDataType;

/** Durable, world-local, player-owned locations observed from successful home commands. */
public final class V177HomeIndex extends SavedData {
 public record Home(String owner,String name,String dimension,int x,int y,int z) {
  public static final Codec<Home> CODEC=RecordCodecBuilder.create(i->i.group(
    Codec.STRING.fieldOf("owner").forGetter(Home::owner),
    Codec.STRING.fieldOf("name").forGetter(Home::name),
    Codec.STRING.fieldOf("dimension").forGetter(Home::dimension),
    Codec.INT.fieldOf("x").forGetter(Home::x),
    Codec.INT.fieldOf("y").forGetter(Home::y),
    Codec.INT.fieldOf("z").forGetter(Home::z)
   ).apply(i,Home::new));
 }
 public static final SavedDataType<V177HomeIndex> TYPE=new SavedDataType<>(
   Identifier.fromNamespaceAndPath("obsidiannetwork","jarvis_command_homes"),
   V177HomeIndex::new,
   Home.CODEC.listOf().xmap(V177HomeIndex::new,V177HomeIndex::all));
 private final Map<String,Home> entries=new LinkedHashMap<>();
 public V177HomeIndex(){}
 private V177HomeIndex(List<Home> loaded){
  for(Home home:loaded)entries.putIfAbsent(key(home.owner(),home.name()),home);
 }
 public static V177HomeIndex get(MinecraftServer server){
  return server.getDataStorage().computeIfAbsent(TYPE);
 }
 private static String key(String owner,String name){return owner+"/"+name;}
 private static String name(String value){
  String n=value==null?"home":value.trim().toLowerCase(Locale.ROOT);
  return n.isBlank()?"home":n.substring(0,Math.min(64,n.length()));
 }
 public List<Home> all(){return List.copyOf(entries.values());}
 public void record(ServerPlayer player,String homeName,BlockPos point,String dimension){
  String owner=player.getUUID().toString(),name=name(homeName);
  String key=key(owner,name);
  // Limit storage per player: even malformed third-party /sethome calls cannot
  // cause unlimited persisted player homes or server-side scanning.
  if(!entries.containsKey(key)&&entries.values().stream()
      .filter(h->h.owner().equals(owner)).count()>=64)return;
  Home updated=new Home(owner,name,dimension,point.getX(),point.getY(),point.getZ());
  if(!updated.equals(entries.put(key,updated)))setDirty();
 }
 public void delete(ServerPlayer player,String homeName){
  if(entries.remove(key(player.getUUID().toString(),name(homeName)))!=null)setDirty();
 }
 public boolean near(ServerPlayer player){
  String owner=player.getUUID().toString();
  String dim=player.level().dimension().identifier().toString();
  for(Home home:entries.values()){
   if(!home.owner().equals(owner)||!home.dimension().equals(dim))continue;
   if(player.distanceToSqr(home.x()+.5D,home.y()+.5D,home.z()+.5D)<=64D)return true;
  }
  return false;
 }
 public boolean outside(ServerPlayer player){
  String owner=player.getUUID().toString();
  String dim=player.level().dimension().identifier().toString();
  for(Home home:entries.values()){
   if(!home.owner().equals(owner)||!home.dimension().equals(dim))continue;
   if(player.distanceToSqr(home.x()+.5D,home.y()+.5D,home.z()+.5D)<144D)return false;
  }
  return true;
 }
}
''')

add("powerarmor/V177HomeProximityPayload.java",r'''package dev.obsidiannetwork.powerarmor;

import dev.obsidiannetwork.client.V177JarvisClient;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.Identifier;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;

/** Server -> client: one boolean on radius changes; no home coordinates. */
public record V177HomeProximityPayload(boolean near) implements CustomPacketPayload {
 public static final Type<V177HomeProximityPayload> TYPE=new Type<>(
   Identifier.fromNamespaceAndPath("obsidiannetwork","jarvis_home_proximity"));
 public static final StreamCodec<RegistryFriendlyByteBuf,V177HomeProximityPayload> STREAM_CODEC=
   StreamCodec.of(
     (buf,payload)->buf.writeBoolean(payload.near()),
     buf->new V177HomeProximityPayload(buf.readBoolean()));
 @Override public Type<? extends CustomPacketPayload> type(){return TYPE;}
 @EventBusSubscriber(modid="obsidiannetwork")
 public static final class Handler {
  private Handler(){}
  @SubscribeEvent public static void register(RegisterPayloadHandlersEvent event){
   event.registrar("1").playToClient(TYPE,STREAM_CODEC,
     (payload,context)->context.enqueueWork(()->
       V177JarvisClient.setNearCommandHome(payload.near())));
  }
 }
}
''')

add("powerarmor/V177HomeTracker.java",r'''package dev.obsidiannetwork.powerarmor;

import com.mojang.brigadier.ParseResults;
import java.util.Locale;
import java.util.WeakHashMap;
import net.minecraft.commands.CommandResultCallback;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.CommandEvent;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;
import net.neoforged.neoforge.network.PacketDistributor;

/**
 * Listen to successfully EXECUTED external home commands; never intercept,
 * register or replace /sethome, never change a command's return value.
 * Supports /sethome, /sethome <name>, /delhome, /delhome <name>,
 * and existing /home teleport destinations, including namespace-prefixed forms.
 */
@EventBusSubscriber(modid="obsidiannetwork")
public final class V177HomeTracker {
 private V177HomeTracker(){}
 private static final WeakHashMap<ServerPlayer,Boolean> PREVIOUS=new WeakHashMap<>();
 // /home may teleport after a configured warmup. Learn its ACTUAL destination
 // only after a successful command and a genuine player teleport.
 private record Pending(String name,String dimension,double x,double y,double z,int expires){}
 private static final WeakHashMap<ServerPlayer,Pending> PENDING=new WeakHashMap<>();
 @SubscribeEvent(priority=EventPriority.LOWEST)
 public static void command(CommandEvent event){
  if(event.isCanceled())return;
  ParseResults<CommandSourceStack> parsed=event.getParseResults();
  if(parsed.getReader().canRead())return; // invalid/incomplete input
  CommandSourceStack source=parsed.getContext().getSource();
  ServerPlayer player=source.getPlayer();
  if(player==null)return; // no console-driven or admin-created foreign homes
  String input=parsed.getReader().getString().strip();
  if(input.startsWith("/"))input=input.substring(1);
  if(input.isBlank())return;
  String[] parts=input.split("\\s+");
  String op=parts[0].toLowerCase(Locale.ROOT);
  // Recognize namespaced commands while never assuming which mod owns them.
  int colon=op.indexOf(':');
  if(colon>=0)op=op.substring(colon+1);
  int opIndex=0;
  if((op.equals("ftbessentials")||op.equals("essentials"))&&parts.length>1){
   op=parts[1].toLowerCase(Locale.ROOT);opIndex=1;
  }
  boolean set=op.equals("sethome");
  boolean delete=op.equals("delhome")||op.equals("deletehome");
  boolean travel=op.equals("home")||op.equals("gohome");
  if(!set&&!delete&&!travel)return;
  final String homeName=parts.length>opIndex+1?parts[opIndex+1]:"home";
  final BlockPos position=player.blockPosition().immutable();
  final String dimension=player.level().dimension().identifier().toString();
  final double x=player.getX(),y=player.getY(),z=player.getZ();
  CommandResultCallback observer=(success,result)->{
   if(!success||result<=0)return; // do not record rejected homes or denied commands
   V177HomeIndex homes=V177HomeIndex.get(player.level().getServer());
   if(set)homes.record(player,homeName,position,dimension);
   else if(delete)homes.delete(player,homeName);
   else{
    // Existing homes from external mods are learned by observing a real /home
    // teleport. Never store the command's starting location as its destination.
    String currentDimension=player.level().dimension().identifier().toString();
    if(!dimension.equals(currentDimension)||player.distanceToSqr(x,y,z)>64D)
     homes.record(player,homeName,player.blockPosition(),currentDimension);
    else PENDING.put(player,new Pending(homeName,dimension,x,y,z,player.tickCount+400));
   }
  };
  // Chain the ORIGINAL callback; do not steal other mods' command callbacks.
  parsed.getContext().withSource(source.withCallback(observer,CommandResultCallback::chain));
 }
 @SubscribeEvent public static void proximity(PlayerTickEvent.Post event){
  if(!(event.getEntity() instanceof ServerPlayer player))return;
  Pending pending=PENDING.get(player);
  if(pending!=null){
   if(player.tickCount>pending.expires())PENDING.remove(player);
   else if(!player.level().dimension().identifier().toString().equals(pending.dimension())
     ||player.distanceToSqr(pending.x(),pending.y(),pending.z())>64D){
    V177HomeIndex.get(player.level().getServer()).record(player,pending.name(),
      player.blockPosition(),player.level().dimension().identifier().toString());
    PENDING.remove(player);
   }
  }
  if(player.tickCount%20!=0)return; // max one lookup per player per second
  if(player.connection==null)return; // connection internals are protected in 26.1
  V177HomeIndex index=V177HomeIndex.get(player.level().getServer());
  // 26.1 keeps personal bed/respawn-anchor coordinates on ServerPlayer.
  // Include these in the same privacy-preserving, boolean-only proximity sync.
  boolean bedNear=false,bedOutside=true;
  var config=player.getRespawnConfig();
  if(config!=null&&config.respawnData()!=null
      &&config.respawnData().dimension().equals(player.level().dimension())){
   var bed=config.respawnData().pos();
   double sq=player.distanceToSqr(bed.getX()+.5D,bed.getY()+.5D,bed.getZ()+.5D);
   bedNear=sq<=64D;
   bedOutside=sq>=144D;
  }
  Boolean previous=PREVIOUS.get(player);
  boolean near=previous!=null&&previous&&(!index.outside(player)||!bedOutside);
  if(!near)near=index.near(player)||bedNear;
  if(previous==null||previous!=near){
   PREVIOUS.put(player,near);
   PacketDistributor.sendToPlayer(player,new V177HomeProximityPayload(near));
  }
 }
}
''')

print("V177_SETHOME_SUCCESS_CALLBACK_DURABLE_RADIUS_NO_COMMAND_OVERRIDE_INSTALLED")
