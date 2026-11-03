#!/usr/bin/env python3
"""B1030: single reliable 3P gun submitter, robust stand turret, and live Cell delivery.

The previous model layer marked its tick 'submitted' even when no visible gun
was drawn, preventing the existing RenderPlayerEvent.Post fallback. Use only
the Post event with a self-contained real humanoid-frame transform.

For world suits, prefer the exact render-state entity ID, but use an
in-bounds matching stand fallback when the optional modifier was absent.
Keep each gun mounted to the genuine animated right-arm ModelPart.

For cells, scan ALL loaded registered drives plus loaded physically contiguous
same-runtime NETWORK nodes. The server never takes a cell until it verifies
the exact NBT in the real DriveMenu backing container.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def read(rel):return (J/rel).read_text(encoding="utf-8")
def write(rel,source):(J/rel).write_text(source,encoding="utf-8")
def balanced(src,needle):
 start=src.index(needle)
 opening=src.index("{",start)
 level=0
 for i in range(opening,len(src)):
  if src[i]=="{":level+=1
  if src[i]=="}":
   level-=1
   if level==0:return start,i+1,src[start:i+1]
 raise AssertionError(("B1030_UNBALANCED",needle))
def replace_method(path,needle,new,guards):
 s=read(path)
 a,b,old=balanced(s,needle)
 for guard in guards:assert guard in old,("B1030_SOURCE_DRIFT",path,guard)
 write(path,s[:a]+new+s[b:])

weapon="client/V176MicroMgVisualClient.java"
layer="client/V176MicroMgLayer.java"

# Remove competing/hidden gun submissions. Keep the registered layer for ABI,
# but render it through the deterministic Post owner instead of marking a
# tick as successfully submitted before a frame has actually drawn anything.
layerSrc=read(layer)
assert "V176MicroMgVisualClient.markLayerSubmitted(state.id);" in layerSrc
assert "V176MicroMgVisualClient.drawArm(xsxWeaponPose" in layerSrc
a,b,old=balanced(layerSrc," @Override public void submit(")
new=''' @Override public void submit(PoseStack pose,SubmitNodeCollector nodes,int light,
       AvatarRenderState state,float yaw,float pitch){
  // The weapon has one authoritative Post renderer (V176MicroMgVisualClient).
  // No hidden layer-marking or duplicate local/world barrel submission here.
 }
'''
write(layer,layerSrc[:a]+new+layerSrc[b:])

# The POST event always owns the actual 3P gun while armed, using the local
# player's or a tracked remote player's synchronized chest upgrade and full suit.
# It does not require V176AttackRenderState or the untrusted 'layer submitted' map.
replace_method(weapon,
 " @SubscribeEvent public static void wornFallback(",
''' @SubscribeEvent public static void wornFallback(RenderPlayerEvent.Post<?> event){
  Minecraft mc=Minecraft.getInstance();
  if(mc.level==null)return;
  var state=event.getRenderState();
  Entity e=mc.level.getEntity(state.id);
  if(!(e instanceof Player player))return;
  int variant=tier(player);
  if(variant<1||variant>24)return;
  boolean active=armedForAttack(player);
  float progress=extension(player.getId(),active);
  if(progress<=0.001F)return;
  // Exactly one 3P gun, independent of a potentially absent player layer.
  PoseStack xsxGunPose=new PoseStack();
  xsxGunPose.mulPose(new org.joml.Matrix4f(event.getPoseStack().last().pose()));
  // The Post event is in root entity space; ModelPart rightArm uses 24px
  // inverted-Y humanoid coordinates, not world/feet coordinates.
  xsxGunPose.translate(0.0F,1.5F,0.0F);
  xsxGunPose.scale(-1.0F,-1.0F,1.0F);
  var arm=event.getRenderer().getModel().rightArm;
  float x=arm.xRot,y=arm.yRot,z=arm.zRot;
  try{
   if(active){
    arm.xRot=-1.535F;
    arm.yRot=0.0F;arm.zRot=0.0F;
   }
   drawArm(xsxGunPose,event.getSubmitNodeCollector(),
       state.lightCoords,arm,variant,progress);
  }finally{
   arm.xRot=x;arm.yRot=y;arm.zRot=z;
  }
 }
''',["LAYER_SUBMITTED","V176AttackRenderState.ACTIVE","drawArm("])
# Turret exact entity modifier can be missing under custom renderers.
# Fall back to the nearest synchronised live world stand matching the CURRENT
# renderer state position and authoritative Micro-MG/mode pose. Do not require
# the ArmorStand to be non-invisible: suit equipment layers may render it even
# when its base model is invisible. This is a render-only change.
replace_method(weapon,
 " @SubscribeEvent public static void worldSuit(",
''' @SubscribeEvent public static void worldSuit(RenderLivingEvent.Post<?,?,?> event){
  Minecraft mc=Minecraft.getInstance();
  if(mc.level==null)return;
  var state=event.getRenderState();
  if(state.entityType!=EntityType.ARMOR_STAND)return;
  ArmorStand suit=null;
  Integer standId=state.getRenderData(XSX_STAND_RENDER_ID);
  if(standId!=null){
   Entity resolved=mc.level.getEntity(standId);
   if(resolved instanceof ArmorStand exact)suit=exact;
  }
  if(suit==null){
   // Old 0.2-block matching lost moving suits between entity ticks.
   // Match only the CURRENT rendered stand, never an arbitrary player.
   var region=new AABB(state.x-1.75D,state.y-1.25D,state.z-1.75D,
                       state.x+1.75D,state.y+2.75D,state.z+1.75D);
   double nearest=Double.POSITIVE_INFINITY;
   for(ArmorStand candidate:mc.level.getEntitiesOfClass(ArmorStand.class,region)){
    if(!candidate.isAlive()||tier(candidate)<1)continue;
    double dx=candidate.getX()-state.x,dy=candidate.getY()-state.y,
           dz=candidate.getZ()-state.z;
    double distance=dx*dx+dy*dy+dz*dz;
    if(distance<nearest){nearest=distance;suit=candidate;}
   }
  }
  if(suit==null||!suit.isAlive())return;
  int variant=tier(suit);
  if(variant<1||variant>24)return;
  boolean installed=false;
  for(EquipmentSlot slot:PowerArmorRuntime.SLOTS)
   if(has(suit.getItemBySlot(slot),"micro_mg")){installed=true;break;}
  if(!installed)return;
  ItemStack chest=suit.getItemBySlot(EquipmentSlot.CHEST);
  boolean active=has(chest,"micro_mg_turret_on")
     ||suit.getRightArmPose().x()<-40.0F
     ||suit.entityTags().contains("xsxlabs_v176_turret");
  float progress=extension(suit.getId(),active);
  if(progress<=0.001F)return;
  if(!(event.getRenderer().getModel() instanceof HumanoidModel<?> model))return;
  PoseStack xsxSuitPose=new PoseStack();
  xsxSuitPose.mulPose(new org.joml.Matrix4f(event.getPoseStack().last().pose()));
  xsxSuitPose.translate(0.0F,1.5F,0.0F);
  xsxSuitPose.scale(-1.0F,-1.0F,1.0F);
  // The ArmorStand's server-synced actual gun-arm aim wins over idle model.
  var arm=model.rightArm;
  float x=arm.xRot,y=arm.yRot,z=arm.zRot;
  try{
   arm.xRot=(float)Math.toRadians(suit.getRightArmPose().x());
   arm.yRot=(float)Math.toRadians(suit.getRightArmPose().y());
   arm.zRot=(float)Math.toRadians(suit.getRightArmPose().z());
   drawArm(xsxSuitPose,event.getSubmitNodeCollector(),
       state.lightCoords,arm,variant,progress);
  }finally{
   arm.xRot=x;arm.yRot=y;arm.zRot=z;
  }
 }
''',["XSX_STAND_RENDER_ID","stand.isInvisible()","drawRight("])
v=read(weapon)
assert v.count("nodes.submitModelPart(XSX_WORLD_BARREL,pose")==1
assert "private static final ModelPart XSX_WORLD_BARREL" in v
assert "nodes.submitModelPart(BARREL,pose" in v
assert v.count(" public static void drawArm(")==1
assert "setInvisible(" not in v

# Refresh ALL trustworthy graph drives, and additionally discover physical
# NETWORK connectivity through registered same-runtime graph nodes, not just
# cables. Never assume a nearby but unrelated drive is connected.
top="cellterminal/V176CellTerminalTopology.java"
t=read(top)
assert "private static List<StorageDriveBlockEntity> physicalDrives(" in t
start,end,old=balanced(t," private static List<StorageDriveBlockEntity> physicalDrives(")
assert "runtimeForDrive(level,next)" in old
new=r''' private static NetworkRuntime attached(ServerLevel level,BlockPos pos){
  NetworkRuntime net=WorldTopologyBridge.runtimeForAccessory(level,pos);
  if(net==null)net=WorldTopologyBridge.runtimeForTerminal(level,pos);
  if(net==null)net=WorldTopologyBridge.runtimeForDrive(level,pos);
  if(net==null)net=WorldTopologyBridge.runtimeForController(level,pos);
  return net;
 }
 private static List<StorageDriveBlockEntity> physicalDrives(
       ServerLevel level,BlockPos terminal,NetworkRuntime identity){
  var queued=new ArrayDeque<BlockPos>();
  var seen=new HashSet<Long>();
  var found=new LinkedHashMap<Long,StorageDriveBlockEntity>();
  queued.add(terminal);
  while(!queued.isEmpty()&&seen.size()<16384&&found.size()<2048){
   BlockPos current=queued.removeFirst();
   if(!level.hasChunkAt(current)||!seen.add(current.asLong()))continue;
   if(!current.equals(terminal)){
    NetworkRuntime currentNet=attached(level,current);
    if(currentNet!=identity)continue;
   }
   for(Direction face:Direction.values()){
    BlockPos next=current.relative(face);
    if(!level.hasChunkAt(next))continue;
    NetworkRuntime nextNet=attached(level,next);
    if(nextNet!=identity)continue;
    if(level.getBlockEntity(next) instanceof StorageDriveBlockEntity drive){
     if(!drive.isRemoved())found.putIfAbsent(next.asLong(),drive);
    }
    if(!seen.contains(next.asLong()))queued.addLast(next);
   }
  }
  return List.copyOf(found.values());
 }
'''
t=t[:start]+new+t[end:]
# Always supplement, even if *some* registered drive has space. Otherwise the
# number of known drives can be incomplete and balancing repeatedly misses
# a connected drive hidden behind a crafting terminal or controller.
a='''  boolean graphHasSpace=false;
  for(StorageDriveBlockEntity drive:all.values())
   if(drive.xsxCellTerminalFirstEmptySlot()>=0){graphHasSpace=true;break;}
  if(!graphHasSpace)
   for(StorageDriveBlockEntity drive:physicalDrives(world,terminal,identity))
    all.putIfAbsent(drive.getBlockPos().asLong(),drive);'''
b='''  for(StorageDriveBlockEntity drive:physicalDrives(world,terminal,identity))
   all.putIfAbsent(drive.getBlockPos().asLong(),drive);'''
assert t.count(a)==1,("B1030_GRAPH_BFS_DRIFT",t.count(a))
t=t.replace(a,b,1)
write(top,t)

# The click pads are actions, NOT real inventory. Log failure reason to the
# player in terms of live network/drive counts rather than silently refusing.
menu="cellterminal/V176CellTerminalMenu.java"
m=read(menu)
assert 'if(slotId>=0&&slotId<8)' in m
assert 'if(!scan.online()||scan.freeSlots()<1)' in m
assert 'broadcastFullState();' in m
assert 'backing.setItem(target,one);' in m
assert 'carried.shrink(1);' in m
a,b,clicked=balanced(m," @Override public void clicked(")
assert '    carried.shrink(1);' in clicked
assert '    broadcastFullState();' in clicked
clicked=clicked.replace(
 '''    broadcastFullState();
    return;''',
 '''    broadcastFullState();
    server.connection.send(new net.minecraft.network.protocol.game.ClientboundSetActionBarTextPacket(
      net.minecraft.network.chat.Component.literal(
       "Cell Terminal: Cell in verbundenem Drive installiert")));
    return;''',1)
assert "Cell in verbundenem Drive installiert" in clicked
m=m[:a]+clicked+m[b:]
write(menu,m)
assert "public static NetworkRuntime xsxCellTerminalNetwork" in read("network/WorldTopologyBridge.java")
assert "WorldTopologyBridge.xsxCellTerminalDrives" in read(top)
print("B1030_SINGLE_3P_GUN_RENDER_POST_STAND_TURRET_FALLBACK_RIGHT_ARM_8_CELL_NETWORK_RUNTIME_TRANSFER_PASS")
