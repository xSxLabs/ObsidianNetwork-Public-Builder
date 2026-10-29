#!/usr/bin/env python3
"""B392: fix invisible or larger-than-16 Blueprint world-model preview."""
import os
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/client/V173WorldGhostRenderer.java"
s=p.read_text(encoding="utf-8")
def change(old,new):
 global s
 assert s.count(old)==1,("B392_BLUEPRINT_SOURCE_DRIFT",old[:110],s.count(old))
 s=s.replace(old,new,1)
change('''  if(!anchor.startsWith(prefix))return;
  String[] a=anchor.substring(prefix.length()).split("[|]");
  String[] d=NetworkBlueprintItem.read(held,"xsxlabs_size").split(",");
  if(a.length!=3||d.length!=3)return;
  int x,y,z,sx,sy,sz,rot=0;
  try{
   x=Integer.parseInt(a[0]);y=Integer.parseInt(a[1]);z=Integer.parseInt(a[2]);''',
'''  // B392_BLUEPRINT_FIRST_FRAME: render before the first confirmation too.
  String[] a=anchor.startsWith(prefix)?
     anchor.substring(prefix.length()).split("[|]"):new String[0];
  String[] d=NetworkBlueprintItem.read(held,"xsxlabs_size").split(",");
  if((a.length!=3&&a.length!=0)||d.length!=3)return;
  int x,y,z,sx,sy,sz,rot=0;
  try{
   if(a.length==3){
    x=Integer.parseInt(a[0]);y=Integer.parseInt(a[1]);z=Integer.parseInt(a[2]);
   }else{
    BlockPos start;
    if(mc.hitResult instanceof net.minecraft.world.phys.BlockHitResult hit)
     start=hit.getBlockPos().relative(hit.getDirection());
    else start=mc.player.blockPosition().relative(mc.player.getDirection(),3);
    x=start.getX();y=start.getY();z=start.getZ();
   }''')
change('''  if(sx<1||sy<1||sz<1||sx>16||sy>16||sz>16||rot<0||rot>7)return;
  var ids=NetworkBlueprintItem.blocks(held);
  String[] states=NetworkBlueprintItem.read(held,"xsxlabs_states").split(";",-1);
  int shown=0,volume=sx*sy*sz;
  // Flat stride=16 previously sampled only x=0 in a 16^3 Blueprint.
  // Keep the complete exposed shell when it fits; distribute larger
  // outlines across all three axes rather than one coordinate plane.
  final int MAX_GHOST_BLOCKS=1536;
  int extent=Math.min(ids.size(),volume),exposed=0;
  for(int n=0;n<extent;n++){
   if(ghostAir(ids,n))continue;
   int dx=n%sx,dz=(n/sx)%sz,dy=n/(sx*sz);
   if(!ghostBuried(ids,n,dx,dy,dz,sx,sy,sz))exposed++;
  }
  for(int n=0;n<extent&&shown<MAX_GHOST_BLOCKS;n++){
   if(ghostAir(ids,n))continue;
   int dx=n%sx,dz=(n/sx)%sz,dy=n/(sx*sz);
   if(ghostBuried(ids,n,dx,dy,dz,sx,sy,sz))continue;
   if(exposed>MAX_GHOST_BLOCKS &&
      Math.floorMod(dx*73856093 ^ dy*19349663 ^ dz*83492791,exposed)>=MAX_GHOST_BLOCKS)
    continue;''',
'''  // B392_BLUEPRINT_ANY_SIZE: remove SECOND legacy 16^3 renderer cap.
  if(sx<1||sy<1||sz<1||sx>NetworkBlueprintItem.MAX_BLOCKS||
     sy>NetworkBlueprintItem.MAX_BLOCKS||sz>NetworkBlueprintItem.MAX_BLOCKS||
     rot<0||rot>7)return;
  long volume=(long)sx*sy*sz;
  if(volume<=0L||volume>NetworkBlueprintItem.MAX_BLOCKS)return;
  // B392_BLUEPRINT_CACHE: decode once per card/component, not each frame.
  if(!net.minecraft.world.item.ItemStack.isSameItemSameComponents(b392Source,held)){
   b392Source=held.copy();
   b392Ids=NetworkBlueprintItem.blocks(held);
   String raw=NetworkBlueprintItem.read(held,"xsxlabs_states");
   b392States=raw.isBlank()?new String[0]:raw.split(";",-1);
   java.util.ArrayList<Integer> shell=new java.util.ArrayList<>();
   int extent=(int)Math.min(volume,b392Ids.size());
   for(int n=0;n<extent;n++){
    if(ghostAir(b392Ids,n))continue;
    int dx=n%sx,dz=(n/sx)%sz,dy=n/(sx*sz);
    if(!ghostBuried(b392Ids,n,dx,dy,dz,sx,sy,sz))shell.add(n);
   }
   b392Surface=shell;
  }
  var ids=b392Ids;
  String[] states=b392States;
  // Cyan corner/edge markers persist while held (no particle flicker).
  BlockState edge=Blocks.LIGHT_BLUE_STAINED_GLASS.defaultBlockState();
  int width=(rot%2==0)?sx:sz,depth=(rot%2==0)?sz:sx;
  for(int axis=0;axis<3;axis++)for(int corner=0;corner<4;corner++){
   int length=axis==0?width:axis==1?sy:depth;
   int samples=Math.min(12,Math.max(1,length));
   for(int t=0;t<=samples;t++){
    double u=(double)t/samples;
    double wx=x+(axis==0?width*u:(corner&1)*width);
    double wy=y+(axis==1?sy*u:(axis==0?(corner&1)*sy:((corner>>1)&1)*sy));
    double wz=z+(axis==2?depth*u:((corner>>1)&1)*depth);
    if(mc.level.hasChunkAt(BlockPos.containing(wx,wy,wz)))
     drawSized(mc,ev,cam,edge,wx-.08,wy-.08,wz-.08,.16,.16,.16);
   }
  }
  int shown=0;
  final int MAX_GHOST_BLOCKS=1536;
  int step=Math.max(1,(b392Surface.size()+MAX_GHOST_BLOCKS-1)/MAX_GHOST_BLOCKS);
  for(int i=0;i<b392Surface.size()&&shown<MAX_GHOST_BLOCKS;i+=step){
   int n=b392Surface.get(i);
   int dx=n%sx,dz=(n/sx)%sz,dy=n/(sx*sz);''')
change('''      !mc.level.hasChunkAt(at)||!mc.level.getBlockState(at).isAir())continue;''',
       '''      !mc.level.hasChunkAt(at)||!mc.level.getWorldBorder().isWithinBounds(at))continue;''')
change('''   draw(mc,ev,cam,state,at.getX(),at.getY(),at.getZ(),1D);''',
'''   // B392_BLUEPRINT_BLOCKED_VISIBLE: obstructed cells are red instead of gone.
   if(!mc.level.getBlockState(at).isAir())
    state=Blocks.RED_STAINED_GLASS.defaultBlockState();
   draw(mc,ev,cam,state,at.getX(),at.getY(),at.getZ(),1D);''')
anchor=' private static void blueprint(Minecraft mc,SubmitCustomGeometryEvent ev,Vec3 cam,'
change(anchor,''' // B392 persistent surface cache, invalidated by card+components.
 private static net.minecraft.world.item.ItemStack b392Source=
     net.minecraft.world.item.ItemStack.EMPTY;
 private static java.util.List<String> b392Ids=java.util.List.of();
 private static java.util.List<Integer> b392Surface=java.util.List.of();
 private static String[] b392States=new String[0];
'''+anchor)
assert "B388_EXACT_MAP_FOOTPRINT" in s and "private static void networkProjection(" in s
p.write_text(s,encoding="utf-8")
print("B392_BLUEPRINT_3D_GHOST_PASS")
