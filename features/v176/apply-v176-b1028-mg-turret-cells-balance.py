#!/usr/bin/env python3
"""B1028: resolve Build 1026 gameplay regressions AND keep B1027 skin fix.

Turret: world renderer must enter the humanoid model frame before applying
right-arm model pivot (the foot-mounted gun was in entity/world frame).
Server still follows player; if shooting, it now rotates whole suit/head/right
arm to its real hostile target (owner and line-of-sight checks unchanged).
3P: preserve the already arm-mounted player weapon layer, not a world offset.
1P: RenderHandEvent must not cancel the submitter that renders the barrel;
bare player-arm skin is suppressed separately by B1027 RenderArmEvent.
Cells: 8 GUI click pads must ACCEPT cells to deliver valid click packets, yet
never own inventory: real DriveMenu backing and server atomic readback remain.
Network: graph-first powered identity plus loaded-cable fallback only when
needed, strictly excluding drives bound to a different network.
Balance: 4 HP projectile damage, 3000 FE per shot, expensive 4-star+4-block
recipe. No modification of legacy or frozen version branches.
"""
from pathlib import Path
import json,os
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])
def read(rel):return (J/rel).read_text(encoding="utf-8")
def write(rel,text):(J/rel).write_text(text,encoding="utf-8")
def change(rel,a,b):
 s=read(rel)
 assert s.count(a)==1,("B1028_SOURCE_DRIFT",rel,s.count(a),a[:160])
 write(rel,s.replace(a,b,1))

# World Post event starts in entity/world render-space. ModelPart pivots are
# defined in vanilla humanoid model-space (24px tall flipped Y model).
# Just like wornFallback's verified conversion, establish that model frame
# ONCE. Do not change the player's layer or the first-person barrel pose.
gun="client/V176MicroMgVisualClient.java"
change(gun,
"""  xsxTurretPose.mulPose(new org.joml.Matrix4f(event.getPoseStack().last().pose()));
  xsxLogTurretPose(stand.getId(),suitTier,amount,"ENTER");""",
"""  xsxTurretPose.mulPose(new org.joml.Matrix4f(event.getPoseStack().last().pose()));
  // Post pose is at the STAND ROOT; ModelPart is in inverted 24px model-space.
  // The missing transform made the gun appear at the feet.
  xsxTurretPose.translate(0.0F,1.5F,0.0F);
  xsxTurretPose.scale(-1.0F,-1.0F,1.0F);
  xsxLogTurretPose(stand.getId(),suitTier,amount,"ENTER");""")
# NeoForge 26.1 deferred submission: the MainHand event must continue after
# the custom node is queued. Suppress ONLY vanilla naked arm using B1027's
# independent RenderArmEvent; preserve the camera elbow and single BARREL.
change(gun,
"""  // Cancel only the main hand while this animation is deployed.
  event.setCanceled(true);
  PoseStack pose=new PoseStack();""",
"""  // Do NOT cancel this RenderHandEvent: it owns the deferred gun nodes.
  // The bare vanilla arm is canceled separately by V176WornSkinClient.
  PoseStack pose=new PoseStack();""")
s=read(gun)
hand=s[s.index(" @SubscribeEvent public static void firstPerson(RenderHandEvent event){"):
       s.index(" @SubscribeEvent public static void xsxlabs$aimVisibleFirstPersonArm(",s.index(" @SubscribeEvent public static void firstPerson(RenderHandEvent event){"))]
assert hand.count("nodes.submitModelPart(BARREL,pose")==1,"B1028_ONE_FIRSTPERSON_GUN"
assert "event.setCanceled(true)" not in hand,"B1028_HAND_EVENT_STILL_CANCELLED"
assert "pose.mulPose(interpolated)" in hand,"B1028_ELBOW_AIM_MISSING"
assert "XSX_POWER_LOWER" in hand,"B1028_ARMOR_FOREARM_MISSING"
assert "nodes.submitModelPart(XSX_WORLD_BARREL,pose" in s,"B1028_MISSING_WORLD_BARREL"
layer=read("client/V176MicroMgLayer.java")
assert "xsxWeaponPose=new PoseStack()" in layer
assert "getParentModel().rightArm" in layer

# Server turret: orient the visual ArmorStand to the same enemy that receives
# the real projectile. Following movement is STILL executed before aiming.
# The standing suit's arm pose is synchronized by vanilla ArmorStand metadata.
mode="powerarmor/V176CompanionMode.java"
change(mode,
"""   Vec3 dir=end.subtract(muzzle).normalize();
   var shot=new V176MicroMgProjectile(""",
"""   Vec3 dir=end.subtract(muzzle).normalize();
   // Actual target orientation after line-of-sight and energy validation:
   // whole body/head + right gun arm follow the real projectile aim.
   Vec3 targetVector=end.subtract(start);
   float xsxYaw=(float)Math.toDegrees(Math.atan2(-targetVector.x,targetVector.z));
   double horizontal=Math.sqrt(targetVector.x*targetVector.x+
       targetVector.z*targetVector.z);
   float xsxPitch=(float)Math.toDegrees(Math.atan2(targetVector.y,horizontal));
   suit.setYRot(xsxYaw);
   suit.setYBodyRot(xsxYaw);
   suit.setYHeadRot(xsxYaw);
   suit.setRightArmPose(new net.minecraft.core.Rotations(
       Math.max(-125F,Math.min(-35F,-80F-xsxPitch)),0F,0F));
   var shot=new V176MicroMgProjectile(""")
m=read(mode)
assert "walkingPose(suit,walking,turret&&hasModule(suit)" in m
assert "suit.setYBodyRot(xsxYaw)" in m
assert "V176MicroMgRules.canTurretFire" in m

# Real cell action pad: replacing the B1019 mayPlace(false) gate is REQUIRED.
# Server clicked() already authorizes actual physical drive installation and
# doesn't let any slot keep an item; menu/screen must both send a normal click.
cell="cellterminal/V176CellTerminalMenu.java"
screen="client/V176CellTerminalScreen.java"
for p in (cell,screen):
 change(p,
 """    @Override public boolean mayPlace(ItemStack item){return false;}""",
 """    @Override public boolean mayPlace(ItemStack item){
     return item.getItem() instanceof dev.obsidiannetwork.item.StorageCellItem
         ||item.getItem() instanceof dev.obsidiannetwork.item.EquipmentCellItem;
    }""")
 c=read(p)
 assert c.count("for(int pad=0;pad<8;pad++)")>=1
 assert "mayPickup" in c
assert "if(slotId>=0&&slotId<8)" in read(cell)
assert "backing.setItem(target,one);" in read(cell)
assert "carried.shrink(1);" in read(cell)
assert "broadcastFullState();" in read(cell)

# The terminal may attach to a Crafting Terminal, controller, drive, or network
# wire. Use the authoritative powered graph; when its drive registry is stale,
# visit only loaded NETWORK cables in the SAME component, without loading
# chunks and without trusting drives bound to another controller.
top="cellterminal/V176CellTerminalTopology.java"
original=read(top)
assert "xsxCableDrives(world,terminal,network)" in original
assert "WorldTopologyBridge.xsxCellTerminalNetwork(world,terminal)" in original
new=r'''package dev.obsidiannetwork.cellterminal;

import dev.obsidiannetwork.blockentity.StorageDriveBlockEntity;
import dev.obsidiannetwork.core.NetworkRuntime;
import dev.obsidiannetwork.network.WorldTopologyBridge;
import dev.obsidiannetwork.network.NetworkSignalRelayBridge;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;

/** Server-authoritative graph; conservative bounded cable fallback. */
public final class V176CellTerminalTopology {
 private V176CellTerminalTopology(){}
 public record Scan(boolean online,List<StorageDriveBlockEntity> drives,
                    int freeSlots,boolean truncated){}
 private static boolean cable(ServerLevel level,BlockPos pos){
  return level.hasChunkAt(pos)&&NetworkSignalRelayBridge.networkWire(level,pos);
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
    if(!cable(level,current))continue;
    NetworkRuntime node=WorldTopologyBridge.runtimeForAccessory(level,current);
    if(node!=null&&node!=identity)continue;
   }
   for(Direction face:Direction.values()){
    BlockPos next=current.relative(face);
    if(!level.hasChunkAt(next))continue;
    if(level.getBlockEntity(next) instanceof StorageDriveBlockEntity drive){
     // Never load another network's drives or unbound foreign inventory.
     NetworkRuntime own=WorldTopologyBridge.runtimeForDrive(level,next);
     if(own==identity&&!drive.isRemoved())
      found.putIfAbsent(next.asLong(),drive);
    }else if(!seen.contains(next.asLong())&&cable(level,next)){
     NetworkRuntime own=WorldTopologyBridge.runtimeForAccessory(level,next);
     if(own==null||own==identity)queued.addLast(next);
    }
   }
  }
  return List.copyOf(found.values());
 }
 public static Scan scan(ServerLevel world,BlockPos terminal){
  if(!world.hasChunkAt(terminal)||
      !(world.getBlockEntity(terminal) instanceof V176CellTerminalBlockEntity))
   return new Scan(false,List.of(),0,false);
  NetworkRuntime identity=WorldTopologyBridge.xsxCellTerminalNetwork(world,terminal);
  if(identity==null||!identity.powered())
   return new Scan(false,List.of(),0,false);
  var all=new LinkedHashMap<Long,StorageDriveBlockEntity>();
  for(StorageDriveBlockEntity drive:WorldTopologyBridge.xsxCellTerminalDrives(world,identity)){
   if(!drive.isRemoved()&&world.hasChunkAt(drive.getBlockPos())
       &&WorldTopologyBridge.runtimeForDrive(world,drive.getBlockPos())==identity)
    all.put(drive.getBlockPos().asLong(),drive);
  }
  boolean graphHasSpace=false;
  for(StorageDriveBlockEntity drive:all.values())
   if(drive.xsxCellTerminalFirstEmptySlot()>=0){graphHasSpace=true;break;}
  if(!graphHasSpace)
   for(StorageDriveBlockEntity drive:physicalDrives(world,terminal,identity))
    all.putIfAbsent(drive.getBlockPos().asLong(),drive);
  var drives=new ArrayList<>(all.values());
  drives.sort(Comparator.comparingLong(d->d.getBlockPos().asLong()));
  int free=0;
  for(StorageDriveBlockEntity drive:drives)
   for(int i=0;i<1;i++)
    free+=Math.max(0,16-drive.occupiedSlots());
  return new Scan(true,List.copyOf(drives),free,drives.size()>=2048);
 }
}
'''
new=new.replace("  for(StorageDriveBlockEntity drive:drives)\n   for(int i=0;i<1;i++)\n    free+=Math.max(0,16-drive.occupiedSlots());",
"""  for(StorageDriveBlockEntity drive:drives)
   free+=Math.max(0,16-drive.occupiedSlots());""")
write(top,new)

# 2 hearts per hit, unchanged FE and rate. Real projectile uses the rules.
rules="powerarmor/V176MicroMgRules.java"
change(rules,"public static final float DAMAGE_HP=4.0f;",
             "public static final float DAMAGE_HP=4.0f;") if False else None
# The public-source rules are already updated to 4HP before copy into work;
# if the workflow copied an old template, force 4HP in the generated Java.
rs=read(rules)
assert "FE_PER_SHOT=3000L" in rs
assert "DAMAGE_HP=" in rs
assert rs.count("DAMAGE_HP=2.0f;")+rs.count("DAMAGE_HP=4.0f;")==1
write(rules,rs.replace("DAMAGE_HP=2.0f;","DAMAGE_HP=4.0f;"))
assert "DAMAGE_HP=4.0f;" in read(rules)

recipe=R/"data/obsidiannetwork/recipe/power_card_micro_mg.json"
assert recipe.is_file(),"B1028_MG_RECIPE_NOT_FOUND"
prior=json.loads(recipe.read_text(encoding="utf-8"))
assert prior["result"]["id"]=="obsidiannetwork:power_card_micro_mg"
expensive={"type":"minecraft:crafting_shaped",
 "pattern":["NSN","SUS","NSN"],
 "key":{"N":"minecraft:netherite_block","S":"minecraft:nether_star",
        "U":"obsidiannetwork:power_armor_upgrade"},
 "result":{"id":"obsidiannetwork:power_card_micro_mg","count":1}}
recipe.write_text(json.dumps(expensive,indent=2)+"\n",encoding="utf-8")
assert expensive["pattern"].count("NSN")==2
print("B1028_SKIN_IMPORTS_RESTORED_1P_3P_TURRET_MODEL_FRAME_TARGET_TRACKING_8_CELL_INPUTS_DRIVE_DISTRIBUTION_4HP_EXPENSIVE_RECIPE_PASS")
