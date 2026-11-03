#!/usr/bin/env python3
"""B1035: address B1034 confirmed in-game failures. Runs AFTER B1032.
1. The client weapon layer must not depend solely on an optional render-state
   context key or an extension transition when Attack is already ON.
2. Use model-space coordinates for native player/stand layer submitters.
3. Discover the powered network through loaded NETWORK wires when the adjacent
   accessory-runtime lookup has not been populated; never cross unrelated nets.
Real Cell installation still uses verified DriveMenu backing and only consumes
a cell after identical NBT readback. First-person and skin visibility unchanged.
"""
import os
from pathlib import Path
ROOT=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def read(rel):return (ROOT/rel).read_text(encoding="utf-8")
def write(rel,s):(ROOT/rel).write_text(s,encoding="utf-8")
def replace(rel,old,new):
 s=read(rel)
 count=s.count(old)
 assert count==1,("B1035_SOURCE_DRIFT",rel,count,old[:120])
 write(rel,s.replace(old,new,1))

layer="client/V176MicroMgLayer.java"
replace(layer,
"""  Integer equippedTier=state.getRenderData(V176AttackRenderState.TIER);
  if(equippedTier==null||equippedTier<1||equippedTier>24)return;
  boolean attack=Boolean.TRUE.equals(state.getRenderData(V176AttackRenderState.ACTIVE));
  float deployment=V176MicroMgVisualClient.extension(state.id,attack);
  if(deployment<=0.001F)return;""",
"""  // A registered third-person layer can render before the optional avatar
  // modifier has filled its context keys. Read the exact entity as fallback.
  Integer equippedTier=state.getRenderData(V176AttackRenderState.TIER);
  boolean attack=Boolean.TRUE.equals(state.getRenderData(V176AttackRenderState.ACTIVE));
  var client=net.minecraft.client.Minecraft.getInstance();
  if(client.level!=null&&client.level.getEntity(state.id)
       instanceof net.minecraft.world.entity.player.Player live){
   if(equippedTier==null||equippedTier<1||equippedTier>24)
    equippedTier=V176MicroMgVisualClient.tier(live);
   attack=attack||V176MicroMgVisualClient.armedForAttack(live);
  }
  if(equippedTier==null||equippedTier<1||equippedTier>24)return;
  float deployment=attack?1.0F:V176MicroMgVisualClient.extension(state.id,false);
  if(deployment<=0.001F)return;""")
# Draw only against the COPY of the event pose, which owns current body yaw.
# 24-pixel humanoid part coordinates are inverted in world render space.
replace(layer,
"""  xsxWeaponPose.mulPose(new org.joml.Matrix4f(pose.last().pose()));
  V176MicroMgVisualClient.drawArm(xsxWeaponPose,nodes,light,""",
"""  xsxWeaponPose.mulPose(new org.joml.Matrix4f(pose.last().pose()));
  xsxWeaponPose.translate(0.0F,1.5F,0.0F);
  xsxWeaponPose.scale(-1.0F,-1.0F,1.0F);
  V176MicroMgVisualClient.drawArm(xsxWeaponPose,nodes,light,""")

stand="client/V176MicroMgStandLayer.java"
replace(stand,
"""  boolean active=has(state.chestEquipment,"micro_mg_turret_on")
       ||state.rightArmPose.x()<-40.0F;
  if(!active)return;""",
"""  boolean active=has(state.chestEquipment,"micro_mg_turret_on")
       ||has(state.chestEquipment,"micro_mg_on")
       ||state.rightArmPose.x()<-35.0F;
  if(!active)return;""")
replace(stand,
"""  gunPose.mulPose(new org.joml.Matrix4f(pose.last().pose()));
  RIGHT_ARM_PIVOT.xRot=""",
"""  gunPose.mulPose(new org.joml.Matrix4f(pose.last().pose()));
  gunPose.translate(0.0F,1.5F,0.0F);
  gunPose.scale(-1.0F,-1.0F,1.0F);
  RIGHT_ARM_PIVOT.xRot=""")

top="cellterminal/V176CellTerminalTopology.java"
s=read(top)
needle=" public static Scan scan(ServerLevel world,BlockPos terminal){"
assert s.count(needle)==1
helper=""" // A valid cable chain is sometimes not registered as an adjacent
 // accessory runtime although the remote Controller and Drives ARE online.
 // Resolve its one powered identity through loaded NETWORK-only wires.
 private static NetworkRuntime wiredNetwork(ServerLevel world,BlockPos terminal){
  NetworkRuntime direct=WorldTopologyBridge.xsxCellTerminalNetwork(world,terminal);
  if(direct!=null&&direct.powered())return direct;
  var pending=new ArrayDeque<BlockPos>();
  var seen=new HashSet<Long>();
  pending.add(terminal);
  NetworkRuntime selected=null;
  while(!pending.isEmpty()&&seen.size()<16384){
   BlockPos here=pending.removeFirst();
   if(!world.hasChunkAt(here)||!seen.add(here.asLong()))continue;
   if(!here.equals(terminal)&&!cable(world,here))continue;
   for(Direction side:Direction.values()){
    BlockPos next=here.relative(side);
    if(!world.hasChunkAt(next))continue;
    NetworkRuntime current=attached(world,next);
    if(current!=null&&current.powered()){
     // Ambiguous components must not silently merge different networks.
     if(selected!=null&&selected!=current)return null;
     selected=current;
    }
    if(cable(world,next)&&!seen.contains(next.asLong()))
     pending.addLast(next);
   }
  }
  return selected;
 }
"""
s=s.replace(needle,helper+needle,1)
old="NetworkRuntime identity=WorldTopologyBridge.xsxCellTerminalNetwork(world,terminal);"
assert s.count(old)==1
s=s.replace(old,"NetworkRuntime identity=wiredNetwork(world,terminal);",1)
write(top,s)

# Non-destructive safety and visible gun assertions.
player=read(layer); turret=read(stand); topology=read(top)
menu=read("cellterminal/V176CellTerminalMenu.java")
assert "attack?1.0F" in player and "xsxWeaponPose.scale(-1.0F,-1.0F,1.0F)" in player
assert "RIGHT_ARM_PIVOT,variant,1.0F" in turret
assert "gunPose.scale(-1.0F,-1.0F,1.0F)" in turret
assert "NetworkRuntime identity=wiredNetwork(world,terminal)" in topology
assert "if(selected!=null&&selected!=current)return null;" in topology
for marker in ("backing.setItem(target,one);","ItemStack.matches(backing.getItem(target),one)",
               "carried.shrink(1);","XSXLABS_B1032_CELL_INPUT"):
 assert marker in menu,("B1035_CELL_CONSERVATION_GUARD",marker)
print("B1035_PLAYER_STAND_NATIVE_MODEL_SPACE_GUNS_WIRED_NETWORK_FALLBACK_SAFE_CELLS_PASS")
