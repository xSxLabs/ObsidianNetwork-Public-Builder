#!/usr/bin/env python3
"""v1.7.3 B409: avoid 512-wire BFS on every item click, orient portal apertures."""
import json
import os
from pathlib import Path

root = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork"
assets = Path(os.environ["V1_RESOURCE_ROOT"]) / "assets/obsidiannetwork"
def rewrite(rel, before, after):
    p=root/rel
    src=p.read_text(encoding="utf-8")
    assert src.count(before)==1,(rel,"source drift",src.count(before),before[:90])
    p.write_text(src.replace(before,after,1),encoding="utf-8")

# B409_TERMINAL_BFS_TICK_CACHE: the remote wireless bridge was being scanned
# every time the terminal asks for a runtime. A single stack may perform
# several accessors, each scanning 512 cable nodes * 6 neighbours. One scan
# per device/level/server tick suffices; next tick always observes edits.
bridge=root/"network/NetworkSignalRelayBridge.java"
text=bridge.read_text(encoding="utf-8")
assert "V173_WIRELESS_CABLE_ENTRY_GUARD" in text
assert "B409_TERMINAL_BFS_TICK_CACHE" not in text
old=""" private static final ThreadLocal<Boolean> RESOLVING=ThreadLocal.withInitial(()->false);"""
new=""" private static final ThreadLocal<Boolean> RESOLVING=ThreadLocal.withInitial(()->false);
 // B409_TERMINAL_BFS_TICK_CACHE: main-thread read cache, per world and tick.
 // Never cache across ticks; inventory contents and storage operations are NOT cached.
 private static final java.util.Map<ServerLevel,TickLookups> LOOKUPS=
   java.util.Collections.synchronizedMap(new java.util.WeakHashMap<>());
 private static final class TickLookups {
  long tick=Long.MIN_VALUE;
  final java.util.Map<BlockPos,NetworkRuntime> results=new java.util.HashMap<>();
 }"""
assert text.count(old)==1
text=text.replace(old,new,1)
old="""  if(RESOLVING.get()||queried==null)return null;
  RESOLVING.set(true);
  try{"""
new="""  if(RESOLVING.get()||queried==null)return null;
  TickLookups lookups=LOOKUPS.computeIfAbsent(level,unused->new TickLookups());
  BlockPos cachePos=queried.immutable();
  long tick=level.getGameTime();
  if(lookups.tick!=tick){
   lookups.tick=tick;
   lookups.results.clear();
  }
  if(lookups.results.containsKey(cachePos)){
   NetworkRuntime known=lookups.results.get(cachePos);
   return known!=null&&known.powered()?known:null;
  }
  RESOLVING.set(true);
  try{"""
assert text.count(old)==1
text=text.replace(old,new,1)
old="""   if(queue.isEmpty())return null;"""
new="""   if(queue.isEmpty()){
    lookups.results.put(cachePos,null);
    return null;
   }"""
assert text.count(old)==1
text=text.replace(old,new,1)
old="""      if(rt!=null&&rt.powered())return rt;"""
new="""      if(rt!=null&&rt.powered()){
       lookups.results.put(cachePos,rt);
       return rt;
      }"""
assert text.count(old)==1
text=text.replace(old,new,1)
old="""   return null;
  }finally{RESOLVING.set(false);}
 }
 private static NetworkRuntime transmitterRuntime"""
# apply-wireless-link-status inserted sourceOnline before transmitterRuntime;
# locate the first resolve's return immediately before its finally.
needle="""   return null;
  }finally{RESOLVING.set(false);}
 }
"""
assert text.count(needle)==1,(text.count(needle),"expected resolve terminator")
text=text.replace(needle,"""   lookups.results.put(cachePos,null);
   return null;
  }finally{RESOLVING.set(false);}
 }
""",1)
assert text.count("B409_TERMINAL_BFS_TICK_CACHE")==1
bridge.write_text(text,encoding="utf-8")

# B409_PORTAL_FOUR_DIRECTIONS: preserve the existing 1x2 invisible logical
# portal block and its original saved ownership/anchor coordinates.
portal="portal/PortalGateBlock.java"
rewrite(portal,
 """import net.minecraft.world.level.block.state.BlockState;""",
 """import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.DirectionProperty;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.core.Direction;""")
rewrite(portal,
 """ private final boolean temporary;""",
 """ // B409_PORTAL_FOUR_DIRECTIONS: horizontal orientation persists in blockstate.
 public static final DirectionProperty FACING=BlockStateProperties.HORIZONTAL_FACING;
 private final boolean temporary;""")
rewrite(portal,
 """ public PortalGateBlock(Properties p,boolean temporary){super(p);this.temporary=temporary;}""",
 """ public PortalGateBlock(Properties p,boolean temporary){
  super(p);this.temporary=temporary;
  registerDefaultState(stateDefinition.any().setValue(FACING,Direction.NORTH));
 }
 @Override protected void createBlockStateDefinition(StateDefinition.Builder<Block,BlockState> builder){
  builder.add(FACING);
 }
 @Override public BlockState getStateForPlacement(BlockPlaceContext ctx){
  return defaultBlockState().setValue(FACING,ctx.getHorizontalDirection().getOpposite());
 }""")
rewrite(portal,
 """  return box(0,0,6,16,32,10);""",
 """  return s.getValue(FACING).getAxis()==Direction.Axis.X
      ?box(6,0,0,10,32,16):box(0,0,6,16,32,10);""")
# The virtual Portal-Gun membrane is not drawn by blockstate JSON, but by
# V173WorldGhostRenderer. Orient that rendering plane too (X/Z axis).
renderer="client/V173WorldGhostRenderer.java"
rewrite(renderer,
 """   double centerX=at.getX()+.5D,baseY=at.getY(),z=at.getZ()+.48D;""",
 """   // B409_PORTAL_RENDER_AXIS: face east/west => aperture runs along Z.
   boolean eastWest=physical.hasProperty(dev.obsidiannetwork.portal.PortalGateBlock.FACING)
       &&physical.getValue(dev.obsidiannetwork.portal.PortalGateBlock.FACING).getAxis()
         ==net.minecraft.core.Direction.Axis.X;
   double centerX=at.getX()+.5D,centerZ=at.getZ()+.5D,baseY=at.getY();
   double z=centerZ-.02D;""")
rewrite(renderer,
 """    drawSized(mc,ev,cam,glow,centerX-half,baseY+low,z,.043D,.063D,.075D);
    drawSized(mc,ev,cam,glow,centerX+half-.043D,baseY+low,z,.043D,.063D,.075D);
    double shift=.012D*Math.sin(now*.16D+i*.65D);
    drawSized(mc,ev,cam,(i+(int)(now/4L))%6<2?core:glow,
       centerX-inner/2D+shift,baseY+low,z+.012D,inner,.063D,.034D);""",
 """    drawSized(mc,ev,cam,glow,
       eastWest?centerX-.0375D:centerX-half,baseY+low,
       eastWest?centerZ-half:z,
       eastWest?.075D:.043D,.063D,eastWest?.043D:.075D);
    drawSized(mc,ev,cam,glow,
       eastWest?centerX-.0375D:centerX+half-.043D,baseY+low,
       eastWest?centerZ+half-.043D:z,
       eastWest?.075D:.043D,.063D,eastWest?.043D:.075D);
    double shift=.012D*Math.sin(now*.16D+i*.65D);
    drawSized(mc,ev,cam,(i+(int)(now/4L))%6<2?core:glow,
       eastWest?centerX-.017D:centerX-inner/2D+shift,baseY+low,
       eastWest?centerZ-inner/2D+shift:z+.012D,
       eastWest?.034D:inner,.063D,eastWest?inner:.034D);""")
# Set B orientation too; match facing with user's horizontal direction.
rewrite("portal/PortalActionPayload.java",
 """ObsidianNetwork.NETWORK_PORTAL_B.get().defaultBlockState()))return;""",
 """ObsidianNetwork.NETWORK_PORTAL_B.get().defaultBlockState()
      .setValue(PortalGateBlock.FACING,player.getDirection())))return;""")
# The renderer owns visibility; variants are for saved-state/blockmodel
# correctness and potential resource-pack use. Both axes, four directions.
for name in ("network_portal_a","network_portal_b"):
    path=assets/"blockstates"/(name+".json")
    states={"facing="+direction:{"model":"obsidiannetwork:block/"+name,"y":turn}
            for direction,turn in (("north",0),("east",90),("south",180),("west",270))}
    path.write_text(json.dumps({"variants":states},indent=2)+"\n",encoding="utf-8")

# JEI B404 must remain untouched: cosmetic red hover, clickable partial +.
jei=(root/"compat/jei/NetworkStorageRecipeTransferHandler.java").read_text()
assert "B404_JEI_COSMETIC_MISSING" in jei and "Type.COSMETIC" in jei
assert "ClientPacketDistributor.sendToServer(new JeiCraftTransferPayload(" in jei
menu=(root/"menu/StorageTerminalMenu.java").read_text()
assert "B368_PARTIAL_INGREDIENTS" in menu
assert "xsxRecipeIngredientAccepts" in menu
print("B409_TERMINAL_BFS_TICK_CACHE_PORTAL_FOUR_DIRECTIONS_JEI_PRESERVED_PASS")
