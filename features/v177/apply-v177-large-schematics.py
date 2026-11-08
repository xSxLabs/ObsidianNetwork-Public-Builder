#!/usr/bin/env python3
"""v1.7.7: 30 million blocks, server-only WorldEdit .schem import, async captures.

Store a private per-world .schem copy: never serialize millions of blocks into
an ItemStack, GUI packet or global saved-data tag. The item carries just an ID
and dimensions. All world reads are 2048 blocks/player/tick; file IO is async.
"""
import os
from pathlib import Path
root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def rep(rel,old,new):
 p=root/rel;s=p.read_text(encoding="utf8")
 assert s.count(old)==1,("V177_SCHEM_SOURCE_DRIFT",rel,old[:110],s.count(old))
 p.write_text(s.replace(old,new,1),encoding="utf8")
def emit(rel,src):
 p=root/rel;p.parent.mkdir(parents=True,exist_ok=True)
 assert not p.exists(),("V177_SCHEM_ALREADY_PRESENT",rel)
 p.write_text(src,encoding="utf8")

# The B378 mod-default was 1,048,576, hard-capped 16,777,216.
# Both were user-requested replaced with a simple 30-million ceiling on v177.
rep("item/NetworkBlueprintItem.java",
 '''public static final int MAX_BLOCKS=Math.max(4096,
     Math.min(16777216,Integer.getInteger("xsxlabs.blueprint.maxBlocks",1048576)));''',
 '''// V177: absolute 30-million-voxel ceiling for both selector and importer.
 public static final int MAX_BLOCKS=30_000_000;''')
# Giant imported/captured plans always remain server-side.
rep("item/NetworkBlueprintItem.java",
 ''' public static List<String> blocks(ItemStack item){
  String str=read(item,"xsxlabs_blocks");''',
 ''' public static List<String> blocks(ItemStack item){
  if(!read(item,"xsxlabs_schem_id").isBlank())
   return dev.obsidiannetwork.schematic.V177SchematicStore.blocks(item);
  String str=read(item,"xsxlabs_blocks");''')
# Preserve complete blockstate properties in the imported .schem, without
# expanding 30 million Java strings when printing.
rep("blockentity/NetworkDeviceBlockEntity.java",
 '''  BlockState targetState=block.defaultBlockState();''',
 '''  BlockState targetState=dev.obsidiannetwork.schematic.V177SchematicStore.state(
      blueprint,index,block.defaultBlockState());''')

# Ensure the existing positioned-blueprint useOn sees loaded externally-backed plans.
# Quill is async and never allocates 30 million strings on a server tick.
quill=root/"item/NetworkSchematicQuillItem.java"
qs=quill.read_text(encoding="utf8")
begin=qs.find(" @Override public InteractionResult useOn(UseOnContext context){")
assert begin>=0,"V177_QUILL_USEON_MISSING"
end=qs.rfind("\n }\n}")
assert end>begin,("V177_QUILL_END_DRIFT",qs[-320:])
new_method=r''' @Override public InteractionResult useOn(UseOnContext context){
  if(!(context.getLevel() instanceof ServerLevel level))return InteractionResult.SUCCESS;
  if(!(context.getPlayer() instanceof net.minecraft.server.level.ServerPlayer player))
   return InteractionResult.PASS;
  ItemStack quill=context.getItemInHand();
  String dim=level.dimension().identifier().toString();
  BlockPos point=context.getClickedPos();
  String corner=NetworkBlueprintItem.read(quill,"xsxlabs_first");
  if(corner.isBlank()||!corner.startsWith(dim+"|")){
   NetworkBlueprintItem.write(quill,"xsxlabs_first",
      dim+"|"+point.getX()+"|"+point.getY()+"|"+point.getZ());
   player.sendOverlayMessage(Component.literal("Schematic: first corner set."));
   return InteractionResult.SUCCESS;
  }
  String[] xyz=corner.substring(dim.length()+1).split("[|]");
  if(xyz.length!=3)return InteractionResult.FAIL;
  try{
   BlockPos first=new BlockPos(Integer.parseInt(xyz[0]),
        Integer.parseInt(xyz[1]),Integer.parseInt(xyz[2]));
   return dev.obsidiannetwork.schematic.V177SchematicCapture.start(
       player,context.getHand(),first,point)
      ?InteractionResult.SUCCESS:InteractionResult.FAIL;
  }catch(NumberFormatException ex){return InteractionResult.FAIL;}
 }'''
quill.write_text(qs[:begin]+new_method+qs[end+3:],encoding="utf8")

emit("schematic/V177SchematicStore.java",r'''package dev.obsidiannetwork.schematic;

import dev.obsidiannetwork.item.NetworkBlueprintItem;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.*;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.Property;
import net.minecraft.world.level.storage.LevelResource;
import net.neoforged.neoforge.server.ServerLifecycleHooks;

/** Server-owned blueprints: dimension-scoped world files, no item NBT arrays. */
public final class V177SchematicStore {
 private V177SchematicStore(){}
 public static final int MAX=30_000_000;
 public static final long MAX_COMPRESSED_BYTES=512L*1024*1024;
 public static final long MAX_NBT_BYTES=768L*1024*1024;
 private static final Map<String,Plan> CACHE=new ConcurrentHashMap<>();
 public record Plan(int width,int height,int length,int[] indices,
                    String[] blockIds,BlockState[] states){
  public int volume(){return indices.length;}
  public String block(int index){return blockIds[indices[index]];}
  public BlockState state(int index){return states[indices[index]];}
 }
 /** Not under the client/game installation directory; this is the server CWD. */
 public static Path imports(MinecraftServer server) throws IOException {
  Path path=server.getServerDirectory().resolve("xsxschematics").normalize();
  Files.createDirectories(path);
  return path.toRealPath();
 }
 /** Private immutable copies persist with the WORLD (not the shared server dir). */
 public static Path copies(MinecraftServer server) throws IOException {
  Path path=server.getWorldPath(LevelResource.ROOT).resolve("data")
    .resolve("xsxschematics").normalize();
  Files.createDirectories(path);
  return path.toRealPath();
 }
 public static Path importedFile(MinecraftServer server,String name)throws IOException{
  if(name==null||!name.matches("[A-Za-z0-9_-]{1,100}"))
   throw new IOException("Invalid schematic name (letters, numbers, - and _ only)");
  Path directory=imports(server),file=directory.resolve(name+".schem");
  if(Files.isSymbolicLink(file)||!Files.isRegularFile(file)||!file.toRealPath().getParent().equals(directory))
   throw new IOException("Schematic not found in server xsxschematics folder");
  if(Files.size(file)>MAX_COMPRESSED_BYTES)
   throw new IOException("Schematic file is over 512 MiB");
  return file;
 }
 public static Path privateFile(MinecraftServer server,String id)throws IOException{
  if(id==null||!id.matches("[0-9a-f-]{36}"))
   throw new IOException("Invalid blueprint ID");
  Path directory=copies(server),file=directory.resolve(id+".schem");
  if(Files.exists(file)&&Files.isSymbolicLink(file))throw new IOException("Symlink forbidden");
  return file;
 }
 public static String freshId(){return UUID.randomUUID().toString();}
 public static void cache(String id,Plan plan){CACHE.put(id,plan);}
 public static void clear(String id){CACHE.remove(id);}
 public static Plan lookup(String id){
  if(id==null||id.isBlank())return null;
  Plan plan=CACHE.get(id);
  if(plan!=null)return plan;
  MinecraftServer server=ServerLifecycleHooks.getCurrentServer();
  if(server==null)return null; // client never touches server-only files
  try{
   Path file=privateFile(server,id);
   if(!Files.isRegularFile(file)||Files.size(file)>MAX_COMPRESSED_BYTES)return null;
   Plan loaded=read(file);
   Plan prior=CACHE.putIfAbsent(id,loaded);
   return prior==null?loaded:prior;
  }catch(Exception ex){return null;}
 }
 public static List<String> blocks(ItemStack item){
  Plan p=lookup(NetworkBlueprintItem.read(item,"xsxlabs_schem_id"));
  if(p==null)return List.of();
  return new AbstractList<>(){
   @Override public int size(){return p.volume();}
   @Override public String get(int i){return p.block(i);}
  };
 }
 public static BlockState state(ItemStack item,int index,BlockState fallback){
  String id=NetworkBlueprintItem.read(item,"xsxlabs_schem_id");
  if(id.isBlank())return fallback;
  Plan p=lookup(id);
  return p!=null&&index>=0&&index<p.volume()?p.state(index):fallback;
 }
 public static void attach(ItemStack stack,String id,Plan plan){
  NetworkBlueprintItem.write(stack,"xsxlabs_schem_id",id);
  NetworkBlueprintItem.write(stack,"xsxlabs_size",
      plan.width()+","+plan.height()+","+plan.length());
 }
 private static int side(CompoundTag tag,String key){
  if(tag.getInt(key).isPresent())return tag.getIntOr(key,0);
  return Short.toUnsignedInt(tag.getShortOr(key,(short)0));
 }
 @SuppressWarnings({"unchecked","rawtypes"})
 private static BlockState toState(String raw){
  int bracket=raw.indexOf('[');
  String key=bracket<0?raw:raw.substring(0,bracket);
  Identifier id=Identifier.tryParse(key);
  if(id==null||!BuiltInRegistries.BLOCK.containsKey(id))return Blocks.AIR.defaultBlockState();
  var block=BuiltInRegistries.BLOCK.getValue(id);
  if(block==null)return Blocks.AIR.defaultBlockState();
  BlockState value=block.defaultBlockState();
  if(bracket<0||!raw.endsWith("]"))return value;
  String fields=raw.substring(bracket+1,raw.length()-1);
  for(String pair:fields.split(",")){
   int sep=pair.indexOf('=');
   if(sep<1)continue;
   Property property=block.getStateDefinition().getProperty(pair.substring(0,sep).trim());
   if(property!=null){
    var option=property.getValue(pair.substring(sep+1).trim());
    if(option.isPresent())value=value.setValue(property,(Comparable)option.get());
   }
  }
  return value;
 }
 public static Plan read(Path file)throws IOException{
  // The accounter rejects decompression bombs and maliciously deep NBT.
  CompoundTag root;
  try{root=NbtIo.readCompressed(file,NbtAccounter.create(MAX_NBT_BYTES));}
  catch(RuntimeException ex){throw new IOException("Invalid or oversized NBT",ex);}
  CompoundTag schem=root.contains("Schematic")?
       root.getCompoundOrEmpty("Schematic"):root;
  int version=schem.getIntOr("Version",0);
  if(version!=2&&version!=3)
   throw new IOException("Only Sponge WorldEdit .schem v2/v3 supported");
  int sx=side(schem,"Width"),sy=side(schem,"Height"),sz=side(schem,"Length");
  long total=(long)sx*sy*sz;
  if(sx<=0||sy<=0||sz<=0||total>MAX)
   throw new IOException("Schematic volume exceeds 30,000,000 blocks");
  CompoundTag body=version==3?schem.getCompoundOrEmpty("Blocks"):schem;
  CompoundTag palette=body.getCompoundOrEmpty("Palette");
  if(palette.size()<1||palette.size()>65536)throw new IOException("Invalid palette");
  String[] names=new String[palette.size()];
  for(String name:palette.keySet()){
   int id=palette.getIntOr(name,-1);
   if(id<0||id>=names.length||names[id]!=null)
    throw new IOException("Invalid or duplicate palette ID");
   names[id]=name;
  }
  String[] ids=new String[names.length];
  BlockState[] states=new BlockState[names.length];
  for(int i=0;i<names.length;i++){
   if(names[i]==null)throw new IOException("Sparse palette");
   states[i]=toState(names[i]);
   ids[i]=BuiltInRegistries.BLOCK.getKey(states[i].getBlock()).toString();
  }
  byte[] bytes=body.getByteArray(version==3?"Data":"BlockData")
      .orElseThrow(()->new IOException("Missing varint block data"));
  int[] indices=new int[(int)total];int cursor=0;
  for(int cell=0;cell<indices.length;cell++){
   int acc=0,shift=0,part;
   do{
    if(cursor>=bytes.length||shift>28)throw new IOException("Truncated/invalid varint");
    part=bytes[cursor++]&255;
    acc|=(part&127)<<shift;
    shift+=7;
   }while((part&128)!=0);
   if(acc<0||acc>=names.length)throw new IOException("Palette index out of bounds");
   indices[cell]=acc;
  }
  if(cursor!=bytes.length)throw new IOException("Trailing block data");
  // Untrusted block-entity inventories, entities and biomes deliberately excluded.
  return new Plan(sx,sy,sz,indices,ids,states);
 }
 public static String serialize(BlockState state){
  var key=BuiltInRegistries.BLOCK.getKey(state.getBlock()).toString();
  if(state.getProperties().isEmpty())return key;
  var join=new java.util.StringJoiner(",","[","]");
  for(var property:state.getProperties())
   join.add(property.getName()+"="+state.getValue(property).toString());
  return key+join;
 }
 public static CompoundTag buildSpongeV2(int width,int height,int length,
                           Map<String,Integer> palette,byte[] data){
  CompoundTag root=new CompoundTag(),colors=new CompoundTag();
  root.putInt("Version",2);
  root.putInt("DataVersion",0);
  root.putShort("Width",(short)width);
  root.putShort("Height",(short)height);
  root.putShort("Length",(short)length);
  for(var p:palette.entrySet())colors.putInt(p.getKey(),p.getValue());
  root.put("Palette",colors);
  root.putInt("PaletteMax",palette.size());
  root.putByteArray("BlockData",data);
  return root;
 }
 public static void writeVarint(ByteArrayOutputStream output,int index){
  do{
   int next=index&127;index>>>=7;
   output.write(next|(index==0?0:128));
  }while(index!=0);
 }
}
''')

emit("schematic/V177SchematicCommand.java",r'''package dev.obsidiannetwork.schematic;

import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.suggestion.Suggestions;
import com.mojang.brigadier.suggestion.SuggestionsBuilder;
import com.mojang.brigadier.suggestion.SuggestionProvider;
import java.nio.file.*;
import java.util.concurrent.CompletableFuture;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import dev.obsidiannetwork.ObsidianNetwork;

/** Server-only /xsxschematic load NAME; importing never blocks the tick loop. */
@EventBusSubscriber(modid="obsidiannetwork")
public final class V177SchematicCommand {
 private V177SchematicCommand(){}
 @SubscribeEvent public static void serverStarted(ServerStartedEvent event){
  try{V177SchematicStore.imports(event.getServer());}
  catch(Exception ex){System.err.println("[xSxLabs] xsxschematics folder: "+ex.getMessage());}
 }
 @SubscribeEvent public static void commands(RegisterCommandsEvent event){
  event.getDispatcher().register(Commands.literal("xsxschematic")
    .then(Commands.literal("load")
      .then(Commands.argument("name",StringArgumentType.word())
        .suggests((context,builder)->{
         try{
          MinecraftServer server=context.getSource().getServer();
          try(var stream=Files.list(V177SchematicStore.imports(server))){
           stream.filter(p->p.getFileName().toString().endsWith(".schem"))
             .limit(1024).forEach(p->builder.suggest(p.getFileName().toString()
                .replaceFirst("\\.schem$","")));
          }
         }catch(Exception ignored){}
         return builder.buildFuture();
        })
        .executes(context->load(context.getSource().getPlayerOrException(),
             StringArgumentType.getString(context,"name"))))));
 }
 private static int load(ServerPlayer player,String name){
  ItemStack held=player.getMainHandItem();
  if(!(held.is(ObsidianNetwork.NETWORK_SCHEMATIC_QUILL.get())
    ||held.is(ObsidianNetwork.NETWORK_BLUEPRINT.get()))
    ||!dev.obsidiannetwork.item.NetworkBlueprintItem.read(held,"xsxlabs_blocks").isBlank()
    ||!dev.obsidiannetwork.item.NetworkBlueprintItem.read(held,"xsxlabs_schem_id").isBlank()){
   player.sendSystemMessage(Component.literal(
       "Hold an EMPTY Schematic & Quill or an empty Blueprint in your main hand."));
   return 0;
  }
  MinecraftServer server=player.level().getServer();
  Path source,privateTarget;
  String id=V177SchematicStore.freshId();
  try{
   source=V177SchematicStore.importedFile(server,name);
   privateTarget=V177SchematicStore.privateFile(server,id);
  }catch(Exception ex){
   player.sendSystemMessage(Component.literal("Schematic: "+ex.getMessage()));return 0;
  }
  final ItemStack original=held; // only mutate original if it is still held later
  final InteractionHand hand=InteractionHand.MAIN_HAND;
  player.sendSystemMessage(Component.literal("Importing "+name+".schem from server xsxschematics..."));
  CompletableFuture.supplyAsync(()->{
   try{
    var parsed=V177SchematicStore.read(source); // safe bounds and v2/v3 validation
    Files.copy(source,privateTarget,StandardCopyOption.COPY_ATTRIBUTES);
    return parsed;
   }catch(Exception ex){throw new java.util.concurrent.CompletionException(ex);}
  }).whenComplete((plan,error)->server.execute(()->{
   if(error!=null){
    player.sendSystemMessage(Component.literal("Schematic import failed: "+
      (error.getCause()!=null?error.getCause().getMessage():error.getMessage())));
    try{Files.deleteIfExists(privateTarget);}catch(Exception ignored){}
    return;
   }
   V177SchematicStore.cache(id,plan);
   if(player.getItemInHand(hand)!=original){
    player.sendSystemMessage(Component.literal(
       "Schematic imported, but your held item changed. Import discarded."));
    V177SchematicStore.clear(id);
    try{Files.deleteIfExists(privateTarget);}catch(Exception ignored){}
    return;
   }
   ItemStack finished=new ItemStack(ObsidianNetwork.NETWORK_BLUEPRINT.get());
   V177SchematicStore.attach(finished,id,plan);
   player.setItemInHand(hand,finished);
   player.sendSystemMessage(Component.literal("Loaded "+name+": "+
      plan.width()+" x "+plan.height()+" x "+plan.length()+" ("+
      plan.volume()+" blocks). Right-click to position the blueprint; use the Network Printer to build."));
  }));
  return 1;
 }
}
''')

emit("schematic/V177SchematicCapture.java",r'''package dev.obsidiannetwork.schematic;

import dev.obsidiannetwork.ObsidianNetwork;
import dev.obsidiannetwork.item.NetworkBlueprintItem;
import java.io.ByteArrayOutputStream;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.CompletableFuture;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.NbtIo;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;

/** 2-corner Schematic & Quill: 2,048 source voxels per player/server tick. */
@EventBusSubscriber(modid="obsidiannetwork")
public final class V177SchematicCapture {
 private V177SchematicCapture(){}
 private static final int PER_TICK=2048;
 private static final Map<UUID,Task> TASKS=new HashMap<>();
 private static final class Task {
  final ServerPlayer player;
  final InteractionHand hand;
  final ItemStack source;
  final int x,y,z,sx,sy,sz,volume;
  final java.util.LinkedHashMap<String,Integer> palette=new LinkedHashMap<>();
  final ByteArrayOutputStream stream=new ByteArrayOutputStream(8192);
  int next=0;
  Task(ServerPlayer p,InteractionHand h,ItemStack stack,
       int x,int y,int z,int sx,int sy,int sz){
   player=p;hand=h;source=stack;this.x=x;this.y=y;this.z=z;
   this.sx=sx;this.sy=sy;this.sz=sz;volume=(int)((long)sx*sy*sz);
  }
 }
 public static boolean start(ServerPlayer player,InteractionHand hand,
                             BlockPos first,BlockPos second){
  if(TASKS.containsKey(player.getUUID())){
   player.sendOverlayMessage(Component.literal("Schematic: capture already running."));
   return false;
  }
  long sx=Math.abs((long)second.getX()-first.getX())+1,
       sy=Math.abs((long)second.getY()-first.getY())+1,
       sz=Math.abs((long)second.getZ()-first.getZ())+1;
  long count=sx*sy*sz;
  if(count<=0||count>V177SchematicStore.MAX||sx>32767||sy>32767||sz>32767){
   player.sendSystemMessage(Component.literal("Selection too large. Maximum 30,000,000 blocks."));
   return false;
  }
  Task task=new Task(player,hand,player.getItemInHand(hand),
      Math.min(first.getX(),second.getX()),
      Math.min(first.getY(),second.getY()),
      Math.min(first.getZ(),second.getZ()),
      (int)sx,(int)sy,(int)sz);
  TASKS.put(player.getUUID(),task);
  player.sendSystemMessage(Component.literal("Schematic capture started: "+
      count+" blocks, 2,048 per tick. Keep the Quill in hand."));
  return true;
 }
 @SubscribeEvent public static void tick(PlayerTickEvent.Post event){
  if(!(event.getEntity() instanceof ServerPlayer player))return;
  Task t=TASKS.get(player.getUUID());
  if(t==null)return;
  if(!player.isAlive()||player.getItemInHand(t.hand)!=t.source){
   TASKS.remove(player.getUUID());
   player.sendSystemMessage(Component.literal("Schematic capture cancelled: Quill changed."));
   return;
  }
  var world=player.level();
  int loadedChunks=0;
  for(int budget=0;budget<PER_TICK&&t.next<t.volume;budget++){
   int index=t.next++;
   int x=index%t.sx;
   int z=(index/t.sx)%t.sz;
   int y=index/(t.sx*t.sz);
   BlockPos pos=new BlockPos(t.x+x,t.y+y,t.z+z);
   if(!world.getWorldBorder().isWithinBounds(pos)
       ||!world.isInWorldBounds(pos)){
    TASKS.remove(player.getUUID());
    player.sendSystemMessage(Component.literal(
       "Schematic capture cancelled: selection outside world bounds."));
    return;
   }
   if(!world.hasChunkAt(pos)){
    // Explicit capture may span thousands of chunks. Load at MOST one new
    // chunk per player per tick; never scan 30m blocks on one server tick.
    if(loadedChunks>=1){t.next--;break;}
    world.getChunk(pos.getX()>>4,pos.getZ()>>4);
    loadedChunks++;
    if(!world.hasChunkAt(pos)){
     TASKS.remove(player.getUUID());
     player.sendSystemMessage(Component.literal("Schematic chunk could not be loaded."));
     return;
    }
   }
   var state=world.getBlockState(pos);
   if(world.getBlockEntity(pos)!=null||!state.getFluidState().isEmpty()
      ||state.getDestroySpeed(world,pos)<0)
    state=Blocks.AIR.defaultBlockState();
   String key=V177SchematicStore.serialize(state);
   Integer code=t.palette.get(key);
   if(code==null){code=t.palette.size();t.palette.put(key,code);}
   V177SchematicStore.writeVarint(t.stream,code);
  }
  if(t.next%65536<PER_TICK)
   player.sendOverlayMessage(Component.literal("Schematic capture: "+
      (100L*t.next/t.volume)+"%"));
  if(t.next<t.volume)return;
  TASKS.remove(player.getUUID());
  String id=V177SchematicStore.freshId();
  Path dest;
  try{dest=V177SchematicStore.privateFile(world.getServer(),id);}
  catch(Exception ex){
   player.sendSystemMessage(Component.literal("Schematic save failed: "+ex.getMessage()));
   return;
  }
  var root=V177SchematicStore.buildSpongeV2(t.sx,t.sy,t.sz,
       t.palette,t.stream.toByteArray());
  var server=world.getServer();
  player.sendSystemMessage(Component.literal("Capture complete. Saving compressed blueprint..."));
  CompletableFuture.runAsync(()->{
   try{NbtIo.writeCompressed(root,dest);}
   catch(Exception ex){throw new java.util.concurrent.CompletionException(ex);}
  }).whenComplete((ignored,error)->server.execute(()->{
   if(error!=null){
    player.sendSystemMessage(Component.literal("Schematic save failed: "+error.getMessage()));
    try{Files.deleteIfExists(dest);}catch(Exception ex){}
    return;
   }
   if(player.getItemInHand(t.hand)!=t.source){
    player.sendSystemMessage(Component.literal("Schematic saved, but Quill was swapped; not applied."));
    return;
   }
   ItemStack result=new ItemStack(ObsidianNetwork.NETWORK_BLUEPRINT.get());
   NetworkBlueprintItem.write(result,"xsxlabs_schem_id",id);
   NetworkBlueprintItem.write(result,"xsxlabs_size",t.sx+","+t.sy+","+t.sz);
   player.setItemInHand(t.hand,result);
   player.sendSystemMessage(Component.literal("Blueprint saved: "+
     t.volume+" blocks. Right-click to position for the Network Printer."));
  }));
 }
}
''')
print("V177_LARGE_SCHEMATICS_SERVER_ONLY_COMMAND_30M_ASYNC_CAPTURE_INSTALLED")

# The B398 WIP freeze hides the Quill/Blueprint/Printer even in Creative and
# removes its crafting recipes. In 1.7.7 these features are user-requested.
# Re-expose ONLY these three, keep unfinished Hologram Terminal hidden.
main=root/"ObsidianNetwork.java"
source=main.read_text(encoding="utf8")
marker='            output.accept((ItemLike)NETWORK_PLANTER_ITEM.get());'
assert source.count(marker)==1,"V177_SCHEM_CREATIVE_DRIFT"
source=source.replace(marker,marker+'''
            output.accept((ItemLike)NETWORK_PRINTER_ITEM.get());
            output.accept((ItemLike)NETWORK_SCHEMATIC_QUILL.get());
            output.accept((ItemLike)NETWORK_BLUEPRINT.get());''',1)
main.write_text(source,encoding="utf8")
jei=root/"compat/jei/WipItemsJeiPlugin.java"
jeis=jei.read_text(encoding="utf8")
assert jeis.count("NETWORK_SCHEMATIC_QUILL.get()")==1,"V177_SCHEM_JEI_DRIFT"
# Retain the WIP filter for the *unfinished* Hologram Terminal only.
start=jeis.index("        java.util.List.of(")
end=jeis.index("\n        )",start)
jeis=jeis[:start]+'''        java.util.List.of(
          new net.minecraft.world.item.ItemStack(
              dev.obsidiannetwork.ObsidianNetwork.NETWORK_HOLOGRAM_TERMINAL_ITEM.get())'''+jeis[end:]
jei.write_text(jeis,encoding="utf8")
import json
data=Path(os.environ["V1_RESOURCE_ROOT"])/"data/obsidiannetwork/recipe"
assert not (data/"network_schematic_quill.json").exists()
assert not (data/"network_printer.json").exists()
data.mkdir(parents=True,exist_ok=True)
(data/"network_schematic_quill.json").write_text(json.dumps({
 "type":"minecraft:crafting_shaped","pattern":["PFP","BIB","PFP"],
 "key":{"P":"minecraft:paper","F":"minecraft:feather",
        "B":"minecraft:book","I":"minecraft:ink_sac"},
 "result":{"id":"obsidiannetwork:network_schematic_quill","count":1}},indent=2)+"\n",encoding="utf8")
(data/"network_printer.json").write_text(json.dumps({
 "type":"minecraft:crafting_shaped","pattern":["IRI","RDR","IRI"],
 "key":{"I":"minecraft:iron_ingot","R":"minecraft:redstone",
        "D":"minecraft:diamond"},
 "result":{"id":"obsidiannetwork:network_printer","count":1}},indent=2)+"\n",encoding="utf8")
print("V177_SCHEM_QUILL_PRINTER_REEXPOSED_IN_CREATIVE_JEI_AND_RECIPES")
