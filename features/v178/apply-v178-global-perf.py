#!/usr/bin/env python3
"""V178 regression-safe whole-mod hotpath reductions.
No mechanics, transactions, draw quality, storage or power balances change.
Run AFTER all v177 injectors. Fail closed if an upstream source changed.
"""
import os
from pathlib import Path
R=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def edit(rel,old,new):
 p=R/rel
 source=p.read_text(encoding="utf-8")
 assert source.count(old)==1,("V178_PERF_SOURCE_DRIFT",rel,source.count(old),old[:100])
 p.write_text(source.replace(old,new,1),encoding="utf-8")

# Power Monitor: 16k-node topology walks must not allocate one Direction[]
# per visited cable. Preserve original six-face order and loaded-only checks.
edit("power/V176PowerNetworkGraph.java",
 ''' private static final int MAX_NODES=16_384;''',
 ''' private static final Direction[] FACES=Direction.values(); // V178_PERF_GRAPH_FACES
 private static final int MAX_NODES=16_384;''')
edit("power/V176PowerNetworkGraph.java",
 '''   for(Direction face:Direction.values()){''',
 '''   for(Direction face:FACES){''')
edit("power/V176PowerNetworkGraph.java",
 ''' private static String path(ServerLevel level,BlockPos at){
  if(!level.hasChunkAt(at))return "";
  var id=BuiltInRegistries.BLOCK.getKey(level.getBlockState(at).getBlock());
  return id.getNamespace().equals("obsidiannetwork")?id.getPath():"";
 }''',
 ''' private static String path(ServerLevel level,BlockPos at){
  if(!level.hasChunkAt(at))return "";
  return pathLoaded(level,at);
 }
 // Call only after the caller has already checked the chunk is loaded.
 private static String pathLoaded(ServerLevel level,BlockPos at){
  var id=BuiltInRegistries.BLOCK.getKey(level.getBlockState(at).getBlock());
  return id.getNamespace().equals("obsidiannetwork")?id.getPath():"";
 }''')
edit("power/V176PowerNetworkGraph.java",
 '''if(!visited.contains(adjoining)&&world.hasChunkAt(adjoining)
        &&CARRIERS.contains(path(world,adjoining)))todo.add(adjoining);''',
 '''if(!visited.contains(adjoining)&&world.hasChunkAt(adjoining)
        &&CARRIERS.contains(pathLoaded(world,adjoining)))todo.add(adjoining);''')

# Armor Station: reject remote players before doing four armor-tier lookups.
# The same first in-range wearer is selected; the same 400k FE budget applies.
edit("powerarmor/V177ArmorStationCharge.java",
 '''   if(!player.isAlive()||!PowerArmorRuntime.full(player))continue;
   // Same bounding volume as the established integrity repair/paste service.
   if(Math.abs(player.getX()-(pos.getX()+.5D))>1D
       ||Math.abs(player.getZ()-(pos.getZ()+.5D))>1D
       ||player.getY()<pos.getY()
       ||player.getY()>pos.getY()+2.5D)continue;''',
 '''   // V178_PERF_STATION_PROXIMITY_FIRST: server.player list order unchanged.
   if(!player.isAlive())continue;
   if(Math.abs(player.getX()-(pos.getX()+.5D))>1D
       ||Math.abs(player.getZ()-(pos.getZ()+.5D))>1D
       ||player.getY()<pos.getY()
       ||player.getY()>pos.getY()+2.5D)continue;
   if(!PowerArmorRuntime.full(player))continue;''')

# Voice scan: no list allocation or entity queries if all five categories
# are disabled. The loaded-only AABB and exact distance predicate remain.
edit("client/V177JarvisClient.java",
 ''' private static void scan(LocalPlayer p){
  var mc=Minecraft.getInstance();''',
 ''' private static void scan(LocalPlayer p){
  if(!V177JarvisSettings.on("hostiles")
    &&!V177JarvisSettings.on("passives")
    &&!V177JarvisSettings.on("players")
    &&!V177JarvisSettings.on("bosses")
    &&!V177JarvisSettings.on("projectile"))return; // V178_PERF_IDLE_SCAN_SKIP
  var mc=Minecraft.getInstance();''')
edit("client/V177JarvisClient.java",
 '''  var all=mc.level.getEntitiesOfClass(Entity.class,range,
      e->e!=p&&e.isAlive()&&e.distanceToSqr(p)<=radius*radius);''',
 '''  var all=mc.level.getEntitiesOfClass(Entity.class,range,
      e->e!=p&&e.isAlive()
        &&(e instanceof Player||e instanceof Monster||e instanceof Animal
             ||e instanceof EnderDragon||e instanceof WitherBoss
             ||e instanceof Projectile)
        &&e.distanceToSqr(p)<=radius*radius); // V178_PERF_ENTITY_TYPE_PREFILTER''')

print("V178_WHOLE_MOD_SAFE_HOTPATH_PASS")
