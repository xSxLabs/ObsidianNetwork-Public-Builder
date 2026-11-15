#!/usr/bin/env python3
"""v1.7.8: FTB-style claim rectangle UX with bounded server-side ticket tasks.

Original implementation: user interfaces emulate documented interactions, no FTB code copied.
Applied AFTER apply-v178-claims.py (and before map-gui patch).
"""
import os
from pathlib import Path
root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def rep(s,old,new):
 assert s.count(old)==1,("V178_FTB_BATCH_SOURCE_DRIFT",old[:120],s.count(old))
 return s.replace(old,new,1)

claim=root/"claims/V178Claims.java"
s=claim.read_text(encoding="utf8")
s=rep(s,
''' private static boolean edit(ServerPlayer player,String action,int cx,int cz){
  if(!(player.level() instanceof ServerLevel level))return false;''',
''' private static boolean edit(ServerPlayer player,String action,int cx,int cz){
  return edit(player,action,cx,cz,false);
 }
 private static boolean edit(ServerPlayer player,String action,int cx,int cz,boolean quiet){
  if(!(player.level() instanceof ServerLevel level))return false;''')
s=rep(s,
'''  dirty=true;
  tell(player,action+" ["+cx+","+cz+"] | "+
     OWNED_COUNT.getOrDefault(id,0)+"/"+MAX_CLAIMS+" claimed, "+
     LOADED_COUNT.getOrDefault(id,0)+"/"+MAX_LOADED+" loaded.");
  // Keep the map centered after changing a cell at its border.
  Long center=REQUEST_CENTERS.get(id);
  if(center==null)send(player,cx,cz);
  else send(player,(int)(center>>32),(int)(long)center);
  return true;''',
'''  dirty=true;
  if(!quiet){
   tell(player,action+" ["+cx+","+cz+"] | "+
       OWNED_COUNT.getOrDefault(id,0)+"/"+MAX_CLAIMS+" claimed, "+
       LOADED_COUNT.getOrDefault(id,0)+"/"+MAX_LOADED+" loaded.");
   Long center=REQUEST_CENTERS.get(id);
   if(center==null)send(player,cx,cz);
   else send(player,(int)(center>>32),(int)(long)center);
  }
  return true;''')
s=rep(s,
''' private static final Map<UUID,Long> REQUEST_CENTERS=new HashMap<>();''',
''' private static final Map<UUID,Long> REQUEST_CENTERS=new HashMap<>();
 // FTB-style rectangular mouse drag batches, 8 changes/player/tick,
 // and 64 changes per entire server tick. No per-cell packets or file writes.
 private static final Map<UUID,Batch> BATCHES=new LinkedHashMap<>();
 private static final Map<UUID,Long> LAST_BATCH=new HashMap<>();
 private static final class Batch {
  final String action,dimension;
  final int x,z,width,height;
  int index,changed;
  Batch(String a,String d,int x0,int z0,int w,int h){
   action=a;dimension=d;x=x0;z=z0;width=w;height=h;
  }
 }
 public static void queueBatch(ServerPlayer player,int mode,int x1,int z1,int x2,int z2){
  if(!(player.level() instanceof ServerLevel level))return;
  if(mode<0||mode>3)return;
  int lowX=Math.min(x1,x2),lowZ=Math.min(z1,z2);
  int highX=Math.max(x1,x2),highZ=Math.max(z1,z2);
  if(highX-lowX>=25||highZ-lowZ>=25)return;
  if(Math.abs((long)lowX)>1875000||Math.abs((long)highX)>1875000
     ||Math.abs((long)lowZ)>1875000||Math.abs((long)highZ)>1875000)return;
  int px=player.blockPosition().getX()>>4,pz=player.blockPosition().getZ()>>4;
  if(Math.abs((long)lowX-px)>256||Math.abs((long)highX-px)>256
      ||Math.abs((long)lowZ-pz)>256||Math.abs((long)highZ-pz)>256)return;
  UUID id=player.getUUID();
  long now=level.getGameTime(),prev=LAST_BATCH.getOrDefault(id,Long.MIN_VALUE);
  if(prev!=Long.MIN_VALUE&&now>=prev&&now-prev<5)return;
  if(BATCHES.containsKey(id))return;
  LAST_BATCH.put(id,now);
  String action=switch(mode){case 0->"claim";case 1->"unclaim";
                             case 2->"load";default->"unload";};
  BATCHES.put(id,new Batch(action,dimension(level),lowX,lowZ,
                highX-lowX+1,highZ-lowZ+1));
 }
 private static void runBatches(MinecraftServer server){
  int global=64;
  var it=BATCHES.entrySet().iterator();
  while(it.hasNext()&&global>0){
   var entry=it.next();Batch b=entry.getValue();
   ServerPlayer p=server.getPlayerList().getPlayer(entry.getKey());
   if(p==null||!(p.level() instanceof ServerLevel level)
      ||!dimension(level).equals(b.dimension)){it.remove();continue;}
   int perPlayer=0;
   while(global>0&&perPlayer++<8&&b.index<b.width*b.height){
    int cx=b.x+b.index%b.width,cz=b.z+b.index/b.width;
    b.index++;global--;
    if(edit(p,b.action,cx,cz,true))b.changed++;
   }
   if(b.index>=b.width*b.height){
    Long center=REQUEST_CENTERS.get(entry.getKey());
    if(center==null)send(p,b.x,b.z);
    else send(p,(int)(center>>32),(int)(long)center);
    tell(p,b.action+" finished: "+b.changed+" chunks changed | "+
       OWNED_COUNT.getOrDefault(entry.getKey(),0)+"/"+MAX_CLAIMS+" claimed, "+
       LOADED_COUNT.getOrDefault(entry.getKey(),0)+"/"+MAX_LOADED+" loaded");
    it.remove();
   }
  }
 }
''')
s=rep(s,
''' @SubscribeEvent public static void autosave(ServerTickEvent.Post event){
  if(active==event.getServer()&&dirty&&event.hasTime()
     &&event.getServer().getTickCount()%40==0)save();
 }''',
''' @SubscribeEvent public static void autosave(ServerTickEvent.Post event){
  if(active!=event.getServer())return;
  if(!BATCHES.isEmpty())runBatches(event.getServer());
  if(dirty&&event.hasTime()&&event.getServer().getTickCount()%40==0)save();
 }''')
s=rep(s,
'''  CLAIMS.clear();TRUSTED.clear();OWNED_COUNT.clear();LOADED_COUNT.clear();REQUEST_TICKS.clear();REQUEST_CENTERS.clear();''',
'''  CLAIMS.clear();TRUSTED.clear();OWNED_COUNT.clear();LOADED_COUNT.clear();REQUEST_TICKS.clear();REQUEST_CENTERS.clear();BATCHES.clear();LAST_BATCH.clear();''')
s=rep(s,
'''    TRUSTED.clear();OWNED_COUNT.clear();LOADED_COUNT.clear();REQUEST_TICKS.clear();REQUEST_CENTERS.clear();dirty=false;}''',
'''    TRUSTED.clear();OWNED_COUNT.clear();LOADED_COUNT.clear();REQUEST_TICKS.clear();REQUEST_CENTERS.clear();BATCHES.clear();LAST_BATCH.clear();dirty=false;}''')
claim.write_text(s,encoding="utf8")

packet=root/"claims/V178ClaimsBatch.java"
assert not packet.exists(),"V178_BATCH_DUPLICATE"
packet.write_text(r'''package dev.obsidiannetwork.claims;

import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;

/** Server authority validates each rectangle; no chunk data sent to clients. */
@EventBusSubscriber(modid="obsidiannetwork")
public record V178ClaimsBatch(int mode,int x1,int z1,int x2,int z2)
  implements CustomPacketPayload{
 public static final Type<V178ClaimsBatch> TYPE=new Type<>(
     Identifier.fromNamespaceAndPath("obsidiannetwork","v178_claims_batch"));
 public static final StreamCodec<RegistryFriendlyByteBuf,V178ClaimsBatch> CODEC=
  StreamCodec.of((b,p)->{b.writeVarInt(p.mode);b.writeVarInt(p.x1);
                        b.writeVarInt(p.z1);b.writeVarInt(p.x2);b.writeVarInt(p.z2);},
                 b->new V178ClaimsBatch(b.readVarInt(),b.readVarInt(),
                     b.readVarInt(),b.readVarInt(),b.readVarInt()));
 @Override public Type<? extends CustomPacketPayload> type(){return TYPE;}
 @SubscribeEvent public static void register(RegisterPayloadHandlersEvent e){
  e.registrar("1").playToServer(TYPE,CODEC,(p,c)->{
   if(c.player() instanceof ServerPlayer player)
    V178Claims.queueBatch(player,p.mode(),p.x1(),p.z1(),p.x2(),p.z2());
  });
 }
}
''',encoding="utf8")
print("V178_FTB_BATCH_ASYNC_CLAIM_CHUNKLOADING_INSTALLED")
