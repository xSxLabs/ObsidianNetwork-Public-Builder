#!/usr/bin/env python3
"""B1657: disk-region explored map archive and low-overhead claim interactions."""
import os
from pathlib import Path
root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def patch(path,old,new):
 s=path.read_text(encoding="utf-8")
 count=s.count(old)
 assert count==1,("B1657_FAIL_CLOSED_SOURCE_DRIFT",path.name,old[:90],count)
 path.write_text(s.replace(old,new,1),encoding="utf-8")

terrain=root/"client/V178TerrainMap.java"
patch(terrain,''' private static int roundRobin;''',r''' private static int roundRobin;
 // B1657_REGION_ARCHIVE: 1536 chunk render cache, separately persisted map
 // regions of 32x32 chunks. RAM is capped to 8 open regions (~512 KiB);
 // disk reads occur only in the client tick sample path, never during render.
 private static final int ARCHIVE_SPAN=32,MAX_OPEN_REGIONS=8;
 private static final int ARCHIVE_MAGIC=0x58535247;
 private static final class ArchiveRegion {
  final int rx,rz;
  final java.util.Map<Long,int[]> tiles=new java.util.HashMap<>();
  boolean dirty;
  ArchiveRegion(int rx,int rz){this.rx=rx;this.rz=rz;}
 }
 private static final java.util.LinkedHashMap<Long,ArchiveRegion> REGIONS=
     new java.util.LinkedHashMap<>(16,.75f,true);
 private static java.nio.file.Path regionPath(int rx,int rz){
  if(mapFile==null)return null;
  String base=mapFile.getFileName().toString();
  return mapFile.resolveSibling(base+"-r"+rx+"_"+rz+".bin");
 }
 private static boolean writeRegion(ArchiveRegion region){
  if(!region.dirty)return true;
  java.nio.file.Path destination=regionPath(region.rx,region.rz),tmp=null;
  if(destination==null)return false;
  try{
   java.nio.file.Files.createDirectories(destination.getParent());
   tmp=java.nio.file.Files.createTempFile(destination.getParent(),"xsx-region-",".tmp");
   try(var out=new java.io.DataOutputStream(new java.io.BufferedOutputStream(
       java.nio.file.Files.newOutputStream(tmp)))){
    out.writeInt(ARCHIVE_MAGIC);
    out.writeInt(region.tiles.size());
    for(var tile:region.tiles.entrySet()){
     out.writeLong(tile.getKey());
     for(int pixel:tile.getValue())out.writeInt(pixel);
    }
   }
   try{java.nio.file.Files.move(tmp,destination,
      java.nio.file.StandardCopyOption.REPLACE_EXISTING,
      java.nio.file.StandardCopyOption.ATOMIC_MOVE);}
   catch(java.nio.file.AtomicMoveNotSupportedException unsupported){
    java.nio.file.Files.move(tmp,destination,
      java.nio.file.StandardCopyOption.REPLACE_EXISTING);
   }
   region.dirty=false;
   return true;
  }catch(java.io.IOException error){
   System.err.println("[xSxLabs] explored region save failed: "+error);
   return false;
  }finally{
   if(tmp!=null)try{java.nio.file.Files.deleteIfExists(tmp);}
      catch(java.io.IOException ignored){}
  }
 }
 private static void flushRegions(){
  for(var region:REGIONS.values())writeRegion(region);
 }
 private static ArchiveRegion region(int cx,int cz){
  int rx=Math.floorDiv(cx,ARCHIVE_SPAN),rz=Math.floorDiv(cz,ARCHIVE_SPAN);
  long regionKey=pos(rx,rz);
  ArchiveRegion found=REGIONS.get(regionKey);
  if(found!=null)return found;
  // Never evict unsaved data if the filesystem is unavailable.
  if(REGIONS.size()>=MAX_OPEN_REGIONS){
   var it=REGIONS.entrySet().iterator();
   if(it.hasNext()){
    var oldest=it.next().getValue();
    if(!writeRegion(oldest))return null;
    it.remove();
   }
  }
  ArchiveRegion result=new ArchiveRegion(rx,rz);
  var file=regionPath(rx,rz);
  if(file!=null&&java.nio.file.Files.isRegularFile(file)){
   try(var input=new java.io.DataInputStream(new java.io.BufferedInputStream(
       java.nio.file.Files.newInputStream(file)))){
    if(input.readInt()!=ARCHIVE_MAGIC)
     throw new java.io.IOException("unknown explored region format");
    int count=input.readInt();
    if(count<0||count>ARCHIVE_SPAN*ARCHIVE_SPAN)
     throw new java.io.IOException("invalid explored region length");
    for(int i=0;i<count;i++){
     long key=input.readLong();
     if(Math.floorDiv((int)(key>>32),ARCHIVE_SPAN)!=rx
        ||Math.floorDiv((int)key,ARCHIVE_SPAN)!=rz)
      throw new java.io.IOException("explored tile outside region");
     int[] pixels=new int[RES*RES];
     for(int j=0;j<pixels.length;j++)pixels[j]=input.readInt();
     result.tiles.put(key,pixels);
    }
   }catch(java.io.IOException error){
    result.tiles.clear();
    System.err.println("[xSxLabs] explored region read failed: "+error);
   }
  }
  REGIONS.put(regionKey,result);
  return result;
 }
 private static int[] archiveLookup(int cx,int cz){
  ArchiveRegion r=region(cx,cz);
  return r==null?null:r.tiles.get(pos(cx,cz));
 }
 private static void archiveStore(int cx,int cz,int[] colors){
  ArchiveRegion r=region(cx,cz);
  if(r!=null&&r.tiles.putIfAbsent(pos(cx,cz),colors)==null)r.dirty=true;
 }
''')
patch(terrain,''' private static void flush(){
   if(!dirty||mapFile==null||mapDimension==null)return;''',
''' private static void flush(){
   flushRegions();
   if(!dirty||mapFile==null||mapDimension==null)return;''')
patch(terrain,'''  if(map.containsKey(key)||!world.hasChunk(cx,cz))return;''',
'''  if(map.containsKey(key))return;
  // B1657: restore previously explored tiles even when the chunk is unloaded.
  int[] explored=archiveLookup(cx,cz);
  if(explored!=null){map.put(key,explored);return;}
  if(!world.hasChunk(cx,cz))return;''')
patch(terrain,'''  map.put(key,colors);dirty=true;''',
'''  map.put(key,colors);archiveStore(cx,cz,colors);dirty=true;''')
patch(terrain,'''   flush();COLORS.clear();roundRobin=0;''',
'''   flush();REGIONS.clear();COLORS.clear();roundRobin=0;''')
patch(terrain,'''   flush();COLORS.clear();roundRobin=0;
   mapIdentity=null;mapFile=null;mapDimension=null;dirty=false;''',
'''   flush();REGIONS.clear();COLORS.clear();roundRobin=0;
   mapIdentity=null;mapFile=null;mapDimension=null;dirty=false;''') if False else None
# clear() still owns its own lifecycle; match its unique tail independently.
patch(terrain,'''   flush();COLORS.clear();roundRobin=0;
   mapIdentity=null;mapFile=null;mapDimension=null;dirty=false;''',
'''   flush();REGIONS.clear();COLORS.clear();roundRobin=0;
   mapIdentity=null;mapFile=null;mapDimension=null;dirty=false;''')
patch(terrain,'''     found.put(pos,pixels);''',
'''     found.put(pos,pixels);
     // One-time migration of old bounded explored cache into region files.
     archiveStore((int)(pos>>32),(int)pos,pixels);''')
# Verify core contract and do not allow disk access on rendering.
generated=terrain.read_text(encoding="utf-8")
for marker in ("B1657_REGION_ARCHIVE","archiveLookup(cx,cz)",
               "writeRegion(oldest)","flushRegions();",
               "Math.floorDiv(cx,ARCHIVE_SPAN)",
               "archiveStore((int)(pos>>32),(int)pos,pixels)"):
 assert marker in generated,("B1657_ARCHIVE_GATE",marker)
render=generated[generated.index(" public static void draw(ClientLevel world"):generated.index(" public static void drawClaim(")]
assert "region(" not in render and "java.nio.file.Files" not in render

claims=root/"claims/V178Claims.java"
patch(claims,''' // B1643: server-authoritative explosion block protection.''',
''' // B1657: intercept attack hooks and both 26.1 entity interaction stages
 // before tools can operate on protected blocks/animals/vehicles. These
 // checks are server-only hash lookups; no chunks are loaded.
 @SubscribeEvent public static void leftClickClaim(PlayerInteractEvent.LeftClickBlock event){
  if(event.getLevel() instanceof ServerLevel level
     &&event.getEntity() instanceof ServerPlayer player
     &&!mayModify(level,event.getPos(),player.getUUID()))
   event.setCanceled(true);
 }
 @SubscribeEvent public static void entityClickClaim(PlayerInteractEvent.EntityInteract event){
  if(event.getLevel() instanceof ServerLevel level
     &&event.getEntity() instanceof ServerPlayer player
     &&!mayModify(level,event.getPos(),player.getUUID()))
   event.setCanceled(true);
 }
 @SubscribeEvent public static void entityClickSpecificClaim(
     PlayerInteractEvent.EntityInteractSpecific event){
  if(event.getLevel() instanceof ServerLevel level
     &&event.getEntity() instanceof ServerPlayer player
     &&!mayModify(level,event.getPos(),player.getUUID()))
   event.setCanceled(true);
 }
 // B1643: server-authoritative explosion block protection.''')
generated=claims.read_text(encoding="utf-8")
for marker in ("leftClickClaim(PlayerInteractEvent.LeftClickBlock",
               "entityClickClaim(PlayerInteractEvent.EntityInteract event)",
               "PlayerInteractEvent.EntityInteractSpecific event)",
               "mayModify(level,event.getPos(),player.getUUID())"):
 assert marker in generated,("B1657_PROTECTION_GATE",marker)
print("B1657_ARCHIVE_AND_CLAIM_INTERACTION_GATES_PASS")
