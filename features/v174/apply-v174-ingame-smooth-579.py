#!/usr/bin/env python3
"""B579: 1-tick reactor FE, 20-tick measured powerbank IO, physical Vision
cable geometry & low-cost projection, and blue/black item-style input rim.
Runs AFTER B577; nothing in older freeze or existing FE capacities is changed.
"""
from pathlib import Path
import os,re
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def read(rel):return (J/rel).read_text(encoding="utf-8")
def put(rel,s): (J/rel).write_text(s,encoding="utf-8")
def swap(s,old,new,n=1):
    count=s.count(old)
    assert count==n,("B579_DRIFT",old[:110],count)
    return s.replace(old,new,n)

# REACTOR: keep the intentionally cheap once/20-tick inventory, structure,
# fuel and coolant maintenance. Only FE generation + port export happen each
# server tick, with identical 20-tick total and no extra multi-block scans.
path="reactor/ReactorControllerBlockEntity.java"
s=read(path)
s=swap(s,
  "  if(sl.getGameTime()%5L==0L)be.pushToPowerPort(sl);",
  """  // B579_REACTOR_PUSH_EVERY_TICK: continuous committed transfer.
  if(be.formed&&be.enabled&&be.storedFe>0L)be.pushToPowerPort(sl);""")
s=swap(s,
  "  if(sl.getGameTime()%20L!=0L)return;",
  """  // B579_REACTOR_GENERATE_EVERY_TICK: every server tick earns exactly
  // the same FE that a 20-tick batch previously earned per tick on average.
  // Fuel/water and costly validation still use the original 20-tick cadence.
  if(sl.getGameTime()%20L!=0L){
   be.b579ActualGeneration=0L;
   if(be.formed&&be.enabled&&be.fuelTicks>0&&be.waterMb>=20){
    long theoretical=(long)be.rodAssemblies*600L*(100-be.controlRodInsertion)/100L;
    long produced=Math.min(Math.max(0L,FE_CAPACITY-be.storedFe),theoretical);
    if(produced>0L){
     be.storedFe+=produced;
     be.b579ActualGeneration=produced;
     be.setChanged();
    }
   }
   return;
  }""")
s=swap(s,"(long)be.rodAssemblies*600L*20L*(100-be.controlRodInsertion)/100L",
         "(long)be.rodAssemblies*600L*(100-be.controlRodInsertion)/100L")
s=swap(s,"  be.storedFe+=generated;",
         """  be.storedFe+=generated;
  be.b579ActualGeneration=generated;""")
s=swap(s,"  if(!(level instanceof ServerLevel sl))return;",
         """  if(!(level instanceof ServerLevel sl))return;
  be.b579ActualGeneration=0L;""")
marker=" private long b514Output=0L,b514OutputAccum=0L,b514OutputWindow=-1L,b514LastExport=-1L;"
s=swap(s,marker,marker+"""
 // B579_REACTOR_REAL_GENERATION_GUI: last actual tick, not hypothetical FE.
 private long b579ActualGeneration=0L;""")
# B577 guiFePerTick is theoretical; GUI now reports actual generated FE.
m=re.search(r"public long guiFePerTick\(\)\{return formed&&enabled&&fuelTicks>0&&waterMb>=20\?\s*\(long\)rodAssemblies\*600L\*\(100-controlRodInsertion\)/100L:0L;\}",s)
assert m,("B579_GUI_RATE_SOURCE",s.find("public long guiFePerTick"))
s=s[:m.start()]+"public long guiFePerTick(){return b579ActualGeneration;}"+s[m.end():]
s=swap(s,'out.putLong("b514Output",b514Output);',
         'out.putLong("b514Output",b514Output);out.putLong("b579Generated",b579ActualGeneration);')
s=swap(s,'b514Output=Math.max(0L,in.getLongOr("b514Output",0L));',
         'b514Output=Math.max(0L,in.getLongOr("b514Output",0L));\n   b579ActualGeneration=Math.max(0L,in.getLongOr("b579Generated",0L));')
# Recompute measured real export rate for each complete 20-tick window,
# never misrepresent one 5-tick or 20-tick packet as a permanent FE/t value.
begin=s.index(" private void b514Export(long transferred){")
end=s.index("\n private final net.neoforged.neoforge.transfer.transaction.SnapshotJournal<Long> energyJournal",begin)
s=s[:begin]+""" // B579_REACTOR_ACTUAL_EXPORT_WINDOW: server-committed FE, true tick rate.
 private void b514Export(long transferred){
  if(level==null||transferred<=0)return;
  long now=level.getGameTime();
  if(b514OutputWindow<0L)b514OutputWindow=now;
  if(now-b514OutputWindow>=20L){
   b514Output=b514OutputAccum/Math.max(1L,now-b514OutputWindow);
   b514OutputAccum=0L;b514OutputWindow=now;
  }
  b514OutputAccum+=transferred;
  b514LastExport=now;
  if(b514Output==0L)
   b514Output=b514OutputAccum/Math.max(1L,now-b514OutputWindow+1L);
 }
"""+s[end:]
put(path,s)

# POWERBANK: ports already transact each caller tick. Replace misleading
# first-commit FE/t samples with a constant-time 20-tick rolling actual
# committed-flow meter, including simultaneous input and output/idle decay.
path="powerbank/PowerbankBlockEntity.java"
s=read(path)
begin=s.index(" private void xsxCommittedTransfer(long in,long out){")
end=s.index("\n private final net.neoforged.neoforge.transfer.transaction.SnapshotJournal<long[]> journal=",begin)
s=s[:begin]+""" // B579_BANK_ROLLING_20: throughput always in FE per SERVER tick.
 private final long[] b579InputBuckets=new long[20],b579OutputBuckets=new long[20];
 private long b579WindowTick=Long.MIN_VALUE,b579WindowIn=0L,b579WindowOut=0L;
 private void b579AdvanceWindow(long now){
  if(b579WindowTick==Long.MIN_VALUE)b579WindowTick=now-1L;
  long elapsed=Math.max(0L,now-b579WindowTick);
  if(elapsed>=20L){
   java.util.Arrays.fill(b579InputBuckets,0L);
   java.util.Arrays.fill(b579OutputBuckets,0L);
   b579WindowIn=0L;b579WindowOut=0L;
  }else for(long t=b579WindowTick+1L;t<=now;t++){
   int idx=(int)Math.floorMod(t,20L);
   b579WindowIn-=b579InputBuckets[idx];
   b579WindowOut-=b579OutputBuckets[idx];
   b579InputBuckets[idx]=0L;b579OutputBuckets[idx]=0L;
  }
  b579WindowTick=now;
  xsxGuiIn=Math.max(0L,b579WindowIn)/20L;
  xsxGuiOut=Math.max(0L,b579WindowOut)/20L;
 }
 private void xsxCommittedTransfer(long in,long out){
  if(level==null)return;
  long now=level.getGameTime();
  b579AdvanceWindow(now);
  int idx=(int)Math.floorMod(now,20L);
  long addIn=Math.max(0L,in),addOut=Math.max(0L,out);
  b579InputBuckets[idx]+=addIn;b579OutputBuckets[idx]+=addOut;
  b579WindowIn+=addIn;b579WindowOut+=addOut;
  b514LastActivity=now;
  xsxGuiIn=b579WindowIn/20L;xsxGuiOut=b579WindowOut/20L;
 }
"""+s[end:]
# Shift the fixed window forward even if no new FE transaction occurs.
hook="// B494_LIVE_BANK_GUI:"
assert s.count(hook)==1,("B579_BANK_TICK_HOOK",s.count(hook))
s=s.replace(hook,"// B579_BANK_IDLE_DECAY: O(1) controller-only rate update.\n  if(be.mode()==PowerbankBlock.Mode.CONTROLLER)be.b579AdvanceWindow(sl.getGameTime());\n  "+hook,1)
put(path,s)

# NETWORK VISION: true thin pipe geometry is already projected by B514.
# Stop the 256-pixel-per-edge raster storm; skip disconnected arms.
# Cache each live cable's connections on the existing eight-tick scan rather
# than asking the world six times per frame. No world mutation/chunk loads.
path="client/NetworkVisionClient.java"
s=read(path)
s=swap(s,"int steps=Math.min(256,","int steps=Math.min(32,")
hook="private static final java.util.ArrayList<BlockPos> xrayPositions=new java.util.ArrayList<>();"
s=swap(s,hook,hook+"\n  // B579_VISION_CACHED_CONNECTIONS: bounded pipe segments only.\n  private static final java.util.Map<BlockPos,Integer> b579VisionMasks=new java.util.HashMap<>();")
s=s.replace("xrayPositions.clear();","xrayPositions.clear();b579VisionMasks.clear();")
old="if(xrayKind(mc.level.getBlockState(at))!=0)xrayPositions.add(at.immutable());"
new="""var found=mc.level.getBlockState(at);
   if(xrayKind(found)!=0){
    BlockPos stable=at.immutable();xrayPositions.add(stable);
    int connections=0;
    for(net.minecraft.core.Direction dir:net.minecraft.core.Direction.values()){
     var property=switch(dir){
      case UP->dev.obsidiannetwork.block.EnergyCableBlock.UP;
      case DOWN->dev.obsidiannetwork.block.EnergyCableBlock.DOWN;
      case NORTH->dev.obsidiannetwork.block.EnergyCableBlock.NORTH;
      case SOUTH->dev.obsidiannetwork.block.EnergyCableBlock.SOUTH;
      case WEST->dev.obsidiannetwork.block.EnergyCableBlock.WEST;
      case EAST->dev.obsidiannetwork.block.EnergyCableBlock.EAST;
     };
     if(found.hasProperty(property)){
      if(found.getValue(property))connections|=1<<dir.get3DDataValue();
     }else{
      BlockPos neighbor=at.relative(dir);
      if(mc.level.hasChunkAt(neighbor)&&xrayKind(mc.level.getBlockState(neighbor))!=0)
       connections|=1<<dir.get3DDataValue();
     }
    }
    b579VisionMasks.put(stable,connections);
   }"""
s=swap(s,old,new)
s=swap(s,"if(state.hasProperty(property)&&!state.getValue(property))continue;",
       "if((b579VisionMasks.getOrDefault(pos,0)&(1<<dir.get3DDataValue()))==0)continue;")
put(path,s)

# ENERGY INPUT: surround the original cyan socket with a narrow BLACK
# item-style outline; preserve the existing blue center, direction and
# render-state gate. This does not affect energy transfer.
path="client/EnergyCableInputRenderer.java"
s=read(path)
s=swap(s,"public final BlockModelRenderState cap=new BlockModelRenderState();",
       "public final BlockModelRenderState cap=new BlockModelRenderState();\n  public final BlockModelRenderState dark=new BlockModelRenderState();")
anchor="if(out.active)resolver.update(out.cap,"
assert anchor in s,("B579_INPUT_RENDERER_MODEL",s.find("resolver.update(out.cap"))
pos=s.index(anchor)
lineEnd=s.index(";",pos)+1
s=s[:lineEnd]+"\n  if(out.active)resolver.update(out.dark,Blocks.BLACK_CONCRETE.defaultBlockState(),DISPLAY);"+s[lineEnd:]
anchor=" @Override public void submit(InputState state,PoseStack pose,"
assert anchor in s
s=s.replace(anchor,""" // B579_ENERGY_INPUT_BLACK_FRAME: same cable-centered face as cyan core.
 private static void dark(InputState data,PoseStack pose,SubmitNodeCollector collector,
     float x,float y,float z,float sx,float sy,float sz){
  pose.pushPose();pose.translate(x,y,z);pose.scale(sx,sy,sz);
  data.dark.submit(pose,collector,data.lightCoords,OverlayTexture.NO_OVERLAY,0);
  pose.popPose();
 }
"""+anchor,1)
# Outer rim 10/16, 2/16 deep. Inner cyan cap remains 6/16 wide.
socket=[
 ("if(state.input[0])cap(state,pose,collector,5/16f,0,5/16f,6/16f,2/16f,6/16f);",
  "if(state.input[0]){dark(state,pose,collector,3/16f,0,3/16f,10/16f,2/16f,10/16f);cap(state,pose,collector,5/16f,0,5/16f,6/16f,2/16f,6/16f);}"),
 ("if(state.input[1])cap(state,pose,collector,5/16f,14/16f,5/16f,6/16f,2/16f,6/16f);",
  "if(state.input[1]){dark(state,pose,collector,3/16f,14/16f,3/16f,10/16f,2/16f,10/16f);cap(state,pose,collector,5/16f,14/16f,5/16f,6/16f,2/16f,6/16f);}"),
 ("if(state.input[2])cap(state,pose,collector,5/16f,5/16f,0,6/16f,6/16f,2/16f);",
  "if(state.input[2]){dark(state,pose,collector,3/16f,3/16f,0,10/16f,10/16f,2/16f);cap(state,pose,collector,5/16f,5/16f,0,6/16f,6/16f,2/16f);}"),
 ("if(state.input[3])cap(state,pose,collector,5/16f,5/16f,14/16f,6/16f,6/16f,2/16f);",
  "if(state.input[3]){dark(state,pose,collector,3/16f,3/16f,14/16f,10/16f,10/16f,2/16f);cap(state,pose,collector,5/16f,5/16f,14/16f,6/16f,6/16f,2/16f);}"),
 ("if(state.input[4])cap(state,pose,collector,0,5/16f,5/16f,2/16f,6/16f,6/16f);",
  "if(state.input[4]){dark(state,pose,collector,0,3/16f,3/16f,2/16f,10/16f,10/16f);cap(state,pose,collector,0,5/16f,5/16f,2/16f,6/16f,6/16f);}"),
 ("if(state.input[5])cap(state,pose,collector,14/16f,5/16f,5/16f,2/16f,6/16f,6/16f);",
  "if(state.input[5]){dark(state,pose,collector,14/16f,3/16f,3/16f,2/16f,10/16f,10/16f);cap(state,pose,collector,14/16f,5/16f,5/16f,2/16f,6/16f,6/16f);}")
]
for old,new in socket:s=swap(s,old,new)
put(path,s)
print("B579_PER_TICK_REACTOR_BANK_ROLLING_TRUE_FE_VISION_CABLE_GEOMETRY_ENERGY_RIM_PASS")
