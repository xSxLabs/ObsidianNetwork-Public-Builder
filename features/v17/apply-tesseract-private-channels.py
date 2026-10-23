#!/usr/bin/env python3
"""Private, persistent owner-scoped Tesseract channels for v1.7.

Run AFTER the v1.1.1 Tesseract overlays, BEFORE final Java compilation.
Legacy block NBT is retained; unclaimed old Tesseracts are claimed by the
first player who opens them. Never join or expose another owner's channel.
"""
import os
from pathlib import Path

j=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def edit(rel, old, new, expected=1):
    p=j/rel
    s=p.read_text(encoding="utf-8")
    n=s.count(old)
    assert n==expected, f"TESSERACT_OWNER anchor drift {rel}: {old[:90]!r}, got {n}, expected {expected}"
    p.write_text(s.replace(old,new),encoding="utf-8")

# Persist owner-scoped channel rosters globally (across all dimensions),
# including channels with no currently loaded Tesseract. Tombstones prevent
# unloaded chunks resurrecting channels deleted by their owner.
(j/"tesseract").mkdir(exist_ok=True)
(j/"tesseract/TesseractChannelData.java").write_text(r'''package dev.obsidiannetwork.tesseract;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.saveddata.SavedDataType;
import java.util.*;

/** Owner UUID + transport tab + name is the channel identity, not name alone. */
public final class TesseractChannelData extends SavedData {
 public record Entry(String owner,int tab,String name,boolean enabled){
  public static final Codec<Entry> CODEC=RecordCodecBuilder.create(i->i.group(
   Codec.STRING.fieldOf("owner").forGetter(Entry::owner),
   Codec.INT.fieldOf("tab").forGetter(Entry::tab),
   Codec.STRING.fieldOf("name").forGetter(Entry::name),
   Codec.BOOL.fieldOf("enabled").forGetter(Entry::enabled)
  ).apply(i,Entry::new));
 }
 public static final SavedDataType<TesseractChannelData> TYPE=new SavedDataType<>(
  Identifier.fromNamespaceAndPath("obsidiannetwork","tesseract_private_channels"),
  TesseractChannelData::new,
  Entry.CODEC.listOf().xmap(TesseractChannelData::new,TesseractChannelData::entries));
 private final ArrayList<Entry> entries=new ArrayList<>();
 public TesseractChannelData(){}
 private TesseractChannelData(List<Entry> saved){
  for(Entry e:saved)if(e!=null&&valid(e.tab(),e.name())&&parse(e.owner())!=null
    &&find(e.owner(),e.tab(),e.name())<0&&entries.size()<2048)entries.add(e);
 }
 public static TesseractChannelData get(MinecraftServer server){
  return server.getDataStorage().computeIfAbsent(TYPE);
 }
 public List<Entry> entries(){return List.copyOf(entries);}
 private static UUID parse(String s){
  try{return UUID.fromString(s);}catch(IllegalArgumentException|NullPointerException e){return null;}
 }
 private static boolean valid(int tab,String name){
  return tab>=0&&tab<3&&name!=null&&!name.isBlank()
    &&name.length()<=48&&name.equals(name.trim());
 }
 private int find(String owner,int tab,String name){
  for(int i=0;i<entries.size();i++){
   Entry e=entries.get(i);
   if(e.tab()==tab&&e.owner().equals(owner)&&e.name().equalsIgnoreCase(name))return i;
  }
  return -1;
 }
 public boolean contains(UUID owner,int tab,String name){
  if(owner==null||!valid(tab,name))return false;
  int i=find(owner.toString(),tab,name);
  return i>=0&&entries.get(i).enabled();
 }
 public List<String> available(UUID owner,int tab){
  if(owner==null||tab<0||tab>=3)return List.of();
  TreeSet<String> names=new TreeSet<>(String.CASE_INSENSITIVE_ORDER);
  for(Entry e:entries)
   if(e.enabled()&&e.tab()==tab&&e.owner().equals(owner.toString()))names.add(e.name());
  return List.copyOf(names);
 }
 public boolean create(UUID owner,int tab,String name){
  if(owner==null||!valid(tab,name))return false;
  String who=owner.toString();
  int i=find(who,tab,name);
  if(i>=0){
   Entry old=entries.get(i);
   if(!old.enabled()){entries.set(i,new Entry(who,tab,name,true));setDirty();}
   return true;
  }
  if(entries.size()>=2048||available(owner,tab).size()>=128)return false;
  entries.add(new Entry(who,tab,name,true));setDirty();return true;
 }
 /** Legacy NBT import is idempotent and MUST NOT resurrect deleted names. */
 public boolean registerLegacy(UUID owner,int tab,String name){
  if(owner==null||!valid(tab,name))return false;
  int i=find(owner.toString(),tab,name);
  if(i>=0)return entries.get(i).enabled();
  return create(owner,tab,name);
 }
 public boolean delete(UUID owner,int tab,String name){
  if(owner==null||!valid(tab,name))return false;
  int i=find(owner.toString(),tab,name);
  if(i<0||!entries.get(i).enabled())return false;
  Entry old=entries.get(i);
  entries.set(i,new Entry(old.owner(),tab,old.name(),false));
  setDirty();return true;
 }
}
''',encoding="utf-8")

be="blockentity/TesseractBlockEntity.java"
edit(be,
 ' private final String[] channels={"","",""}; private boolean receiveMode=false;',
 ' private final String[] channels={"","",""}; private boolean receiveMode=false;\n'
 ' // XSXLABS_TESSERACT_PRIVATE_OWNER_V1: saved UUID, never client-asserted.\n'
 ' private java.util.UUID owner;')
edit(be,
 ' public boolean receiveMode(){return receiveMode;}',
 ''' public java.util.UUID ownerId(){return owner;}
 public boolean ownedBy(net.minecraft.server.level.ServerPlayer player){
  return owner!=null&&player!=null&&owner.equals(player.getUUID());
 }
 private boolean sameOwner(TesseractBlockEntity other){
  return owner!=null&&other!=null&&owner.equals(other.owner);
 }
 /** Legacy devices contain channel strings but no UUID. First opener claims. */
 public boolean claimOwner(net.minecraft.server.level.ServerPlayer player){
  if(player==null)return false;
  if(owner!=null)return ownedBy(player);
  owner=player.getUUID();
  setChanged();
  if(level instanceof ServerLevel sl)registerLegacyChannels(sl);
  return true;
 }
 private void registerLegacyChannels(ServerLevel server){
  if(owner==null)return;
  var data=dev.obsidiannetwork.tesseract.TesseractChannelData.get(server.getServer());
  for(int tab=0;tab<3;tab++)if(!channels[tab].isBlank()
      &&!data.registerLegacy(owner,tab,channels[tab])){
   // A tombstoned channel must not become active on chunk reload.
   channels[tab]="";setChanged();
  }
 }
 public static java.util.List<String> channels(ServerLevel level,int tab,java.util.UUID user){
  return dev.obsidiannetwork.tesseract.TesseractChannelData.get(level.getServer())
       .available(user,tab);
 }
 public boolean setOwnedChannel(net.minecraft.server.level.ServerPlayer player,int tab,String v){
  String value=clean(v);
  if(!ownedBy(player)||tab<0||tab>=3
    ||!dev.obsidiannetwork.tesseract.TesseractChannelData.get(
        player.level().getServer()).contains(owner,tab,value))return false;
  channels[tab]=value;setChanged();return true;
 }
 /** Delete only own named channel and unbind own loaded endpoints on all dimensions. */
 public static boolean deleteOwnedChannel(net.minecraft.server.level.ServerPlayer player,int tab,String raw){
  if(player==null||tab<0||tab>=3)return false;
  String value=clean(raw);
  if(!dev.obsidiannetwork.tesseract.TesseractChannelData.get(
      player.level().getServer()).delete(player.getUUID(),tab,value))return false;
  Set<TesseractBlockEntity> all=LIVE.get(player.level().getServer());
  if(all!=null)for(TesseractBlockEntity be:List.copyOf(all)){
   if(be!=null&&!be.isRemoved()&&be.owner!=null&&be.owner.equals(player.getUUID())
       &&be.channels[tab].equalsIgnoreCase(value)){
    be.channels[tab]="";be.setChanged();
   }
  }
  return true;
 }
 public boolean receiveMode(){return receiveMode;}''')
# The old public setter is not an authorization boundary; make it private.
edit(be,
 ' public void setChannel(int tab,String v){if(tab<0||tab>=3)return;channels[tab]=clean(v);setChanged();}',
 ' private void setChannel(int tab,String v){if(tab<0||tab>=3)return;channels[tab]=clean(v);setChanged();}')
edit(be,
 'if(!(l instanceof ServerLevel level)||level.getGameTime()%5!=0)return;',
 'if(!(l instanceof ServerLevel level)||level.getGameTime()%5!=0||be.owner==null)return;')
edit(be,
 'if(src==be||src.isRemoved()||src.receiveMode',
 'if(src==be||!be.sameOwner(src)||src.isRemoved()||src.receiveMode')
edit(be,
 'if(src==dst||src.isRemoved()||src.receiveMode',
 'if(src==dst||!dst.sameOwner(src)||src.isRemoved()||src.receiveMode',expected=2)
edit(be,
 'protected void saveAdditional(ValueOutput out){super.saveAdditional(out);',
 'protected void saveAdditional(ValueOutput out){super.saveAdditional(out);out.putString("xsxlabs_tesseract_owner",owner==null?"":owner.toString());')
edit(be,
 'protected void loadAdditional(ValueInput in){super.loadAdditional(in);',
 '''protected void loadAdditional(ValueInput in){super.loadAdditional(in);
  String savedOwner=in.getStringOr("xsxlabs_tesseract_owner","");
  try{owner=savedOwner.isBlank()?null:java.util.UUID.fromString(savedOwner);}
  catch(IllegalArgumentException e){owner=null;}''')
edit(be,
 'LIVE.computeIfAbsent(s.getServer(),k->Collections.newSetFromMap(new IdentityHashMap<>())).add(this);',
 'LIVE.computeIfAbsent(s.getServer(),k->Collections.newSetFromMap(new IdentityHashMap<>())).add(this);registerLegacyChannels(s);')

block="block/TesseractBlock.java"
edit(block,
 '  if(!l.isClientSide())player.openMenu(',
 '''  if(!l.isClientSide()){
   if(!(player instanceof net.minecraft.server.level.ServerPlayer sp)||!be.claimOwner(sp)){
    player.sendSystemMessage(Component.literal("This Tesseract belongs to another player."));
    return InteractionResult.FAIL;
   }
   player.openMenu(''')
edit(block,
 'else for(int t=0;t<3;t++)b.writeVarInt(0);});',
 'else for(int t=0;t<3;t++)b.writeVarInt(0);});}')
edit(block,
 'TesseractBlockEntity.channels(sl,t)',
 'TesseractBlockEntity.channels(sl,t,player.getUUID())')
edit(block,
 '@Override public void onPlace(',
 '''@Override public void setPlacedBy(Level level,BlockPos pos,BlockState state,
  net.minecraft.world.entity.LivingEntity placer,ItemStack stack){
  super.setPlacedBy(level,pos,state,placer,stack);
  if(!level.isClientSide()&&placer instanceof net.minecraft.server.level.ServerPlayer player
      &&level.getBlockEntity(pos) instanceof TesseractBlockEntity be)
   be.claimOwner(player);
 }
@Override public void onPlace(''')

# Closing the GUI after a claim must not leave an unauthorized server menu.
edit("menu/TesseractMenu.java",
 'public boolean stillValid(Player p){return p.distanceToSqr(pos.getCenter())<=64.0;}',
 '''public boolean stillValid(Player p){
  return p.distanceToSqr(pos.getCenter())<=64.0
    &&(be==null||(p instanceof net.minecraft.server.level.ServerPlayer sp&&be.ownedBy(sp)));
 }''')

# Never trust a client packet's channel string or world position as proof of ownership.
handler="network/TesseractChannelHandler.java"
edit(handler,
 'TesseractBlockEntity.createChannel(sp.level(),p.tab(),p.channel());be.setChannel(p.tab(),p.channel());',
 '''if(be.ownedBy(sp)&&dev.obsidiannetwork.tesseract.TesseractChannelData
 .get(sp.level().getServer()).create(sp.getUUID(),p.tab(),p.channel()))
  be.setOwnedChannel(sp,p.tab(),p.channel());''')
# A forged DELETE must never clear another owner's active endpoint.
delete="network/TesseractDeleteChannelHandler.java"
dp=j/delete
ds=dp.read_text(encoding="utf-8")
old='TesseractBlockEntity.deleteChannel(sp.level(),p.tab(),p.channel());'
assert ds.count(old)==1, "TESSERACT_OWNER delete payload changed: "+ds[:1200]
dp.write_text(ds.replace(old,'TesseractBlockEntity.deleteOwnedChannel(sp,p.tab(),p.channel());',1),encoding="utf-8")
# A forged SEND/RECEIVE switch must not mutate another owner's Tesseract.
mode="network/TesseractModeHandler.java"
mp=j/mode
ms=mp.read_text(encoding="utf-8")
old='be.setReceiveMode(p.receive());'
assert ms.count(old)==1 and 'instanceof ServerPlayer sp' in ms, "TESSERACT_OWNER mode handler changed: "+ms[:1200]
mp.write_text(ms.replace(old,'if(be.ownedBy(sp))be.setReceiveMode(p.receive());',1),encoding="utf-8")

# Strict source contract: live item, fluid and FE paths are scoped by UUID.
b=(j/be).read_text(encoding="utf-8")
assert b.count('!be.sameOwner(src)')==1
assert b.count('!dst.sameOwner(src)')==2
assert 'xsxlabs_tesseract_owner' in b and 'registerLegacyChannels(s)' in b
assert 'forceChunk(' in b and 'LIVE.get(level.getServer())' in b
assert 'TesseractChannelData.get' in b
assert 'channels(sl,t,player.getUUID())' in (j/block).read_text(encoding="utf-8")
assert 'be.ownedBy(sp)' in (j/handler).read_text(encoding="utf-8")
assert 'deleteOwnedChannel(sp' in dp.read_text(encoding="utf-8")
assert 'be.ownedBy(sp)' in mp.read_text(encoding="utf-8")
print("BUILD92_TESSERACT_PRIVATE_CHANNELS_PASS: owner persisted, per-player roster, packets auth, 3 FE/fluid/item guards, safe legacy claim")
