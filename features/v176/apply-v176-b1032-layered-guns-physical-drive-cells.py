#!/usr/bin/env python3
"""B1032: single yaw-inheriting player weapon layer, real armor-stand weapon
layer using synchronized ArmorStandRenderState, and physical connected-drive
Cell Terminal insertion. Applied after B1031. No fake fixed-position 3P gun.

Root causes:
* B1030 blanked the Player RenderLayer and moved gun into a Post event with
  reconstructed transforms: the Post gun did not rotate reliably with player.
* Turret depended on RenderLivingEvent.Post, optional ID, model lookup and
  extension history. Equipment and arm pose are ALREADY in ArmorStandRenderState.
* B1030 BFS discarded a drive with runtimeForDrive==null even if it physically
  touched a NETWORK cable belonging to the powered selected network.

Do not accept known foreign-runtime drives. Never hold cells in the terminal.
"""
import os
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def load(rel):return (J/rel).read_text(encoding="utf-8")
def save(rel,s):(J/rel).write_text(s,encoding="utf-8")
def method(src,needle):
 a=src.index(needle)
 left=src.index("{",a)
 depth=0
 for i in range(left,len(src)):
  if src[i]=="{":depth+=1
  elif src[i]=="}":
   depth-=1
   if depth==0:return a,i+1,src[a:i+1]
 raise AssertionError(("B1032_UNBALANCED_METHOD",needle))
def replace_method(rel,needle,new,markers):
 s=load(rel)
 a,b,old=method(s,needle)
 for marker in markers:assert marker in old,("B1032_DRIFT",rel,marker)
 save(rel,s[:a]+new+s[b:])

# 1. A native RenderLayer receives the player rotation and parent model
# transform from the player renderer. NO second world-space Post submission.
layer="client/V176MicroMgLayer.java"
replace_method(layer," @Override public void submit(",
''' @Override public void submit(PoseStack pose,SubmitNodeCollector nodes,int light,
       AvatarRenderState state,float yaw,float pitch){
  Integer equippedTier=state.getRenderData(V176AttackRenderState.TIER);
  if(equippedTier==null||equippedTier<1||equippedTier>24)return;
  boolean attack=Boolean.TRUE.equals(state.getRenderData(V176AttackRenderState.ACTIVE));
  float deployment=V176MicroMgVisualClient.extension(state.id,attack);
  if(deployment<=0.001F)return;
  // The RenderLayer pose already includes actual body yaw and local model
  // orientation. Multiplying another player/world yaw breaks rotation.
  PoseStack xsxWeaponPose=new PoseStack();
  xsxWeaponPose.mulPose(new org.joml.Matrix4f(pose.last().pose()));
  V176MicroMgVisualClient.drawArm(xsxWeaponPose,nodes,light,
      getParentModel().rightArm,equippedTier,deployment);
 }
''',["No hidden layer-marking","authoritative Post renderer"])

# Remove the detached Player-Post gun. It had no reliable parent body yaw.
weapon="client/V176MicroMgVisualClient.java"
replace_method(weapon,
 " @SubscribeEvent public static void wornFallback(",
''' @SubscribeEvent public static void wornFallback(RenderPlayerEvent.Post<?> event){
  // Intentional no-op. V176MicroMgLayer.submit is the sole world-player gun
  // renderer, bound to the real rotating PlayerModel.rightArm.
 }
''',["xsxGunPose","drawArm("])

# 2. The old ArmorStand Post renderer was still silently rejecting otherwise
# visible suits. Use a dedicated RenderLayer and the replicated render state.
# No entity-ID lookup or model-frame guessing is required to identify a module:
# state.chestEquipment and state.rightArmPose are populated by vanilla.
replace_method(weapon,
 " @SubscribeEvent public static void worldSuit(",
''' @SubscribeEvent public static void worldSuit(RenderLivingEvent.Post<?,?,?> event){
  // Intentional no-op. V176MicroMgStandLayer submits the turret barrel in
  // the native ArmorStandRenderer model/rotation frame, exactly once.
 }
''',["XSX_STAND_RENDER_ID","drawArm("])

stand=J/"client/V176MicroMgStandLayer.java"
assert not stand.exists(),("B1032_DUPLICATE_STAND_RENDER_LAYER",stand)
stand.write_text(r'''package dev.obsidiannetwork.client;

import com.mojang.blaze3d.vertex.PoseStack;
import dev.obsidiannetwork.powerarmor.PowerArmorRuntime;
import dev.obsidiannetwork.registry.ModDataComponents;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.ArmorStandRenderer;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.entity.state.ArmorStandRenderState;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.item.ItemStack;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.EntityRenderersEvent;
import java.util.Arrays;

/** Follows ArmorStandRenderer's rotated pose and replicated right-arm angles.
 * A baked pivot at the vanilla shoulder avoids concrete model classes
 * that have changed in NeoForge 26.1.
 */
public final class V176MicroMgStandLayer
    extends RenderLayer<ArmorStandRenderState,EntityModel<ArmorStandRenderState>> {
 private static final ModelPart RIGHT_ARM_PIVOT=createRightArmPivot();
 @SuppressWarnings({"rawtypes","unchecked"})
 public V176MicroMgStandLayer(ArmorStandRenderer parent){
  super((RenderLayerParent)parent);
 }
 private static ModelPart createRightArmPivot(){
  MeshDefinition mesh=new MeshDefinition();
  mesh.getRoot().addOrReplaceChild("rightArm",
     CubeListBuilder.create(),PartPose.offset(-5.0F,2.0F,0.0F));
  return LayerDefinition.create(mesh,16,16).bakeRoot().getChild("rightArm");
 }
 private static boolean has(ItemStack piece,String token){
  if(piece.isEmpty())return false;
  String raw=piece.get(ModDataComponents.POWER_ARMOR_UPGRADES.get());
  return raw!=null&&Arrays.asList(raw.split(",")).contains(token);
 }
 private static int tier(ArmorStandRenderState state){
  int value=PowerArmorRuntime.tier(state.headEquipment,0);
  if(value<1||value>24)return 0;
  if(PowerArmorRuntime.tier(state.chestEquipment,1)!=value
      ||PowerArmorRuntime.tier(state.legsEquipment,2)!=value
      ||PowerArmorRuntime.tier(state.feetEquipment,3)!=value)return 0;
  return value;
 }
 @Override public void submit(PoseStack pose,SubmitNodeCollector nodes,int light,
       ArmorStandRenderState state,float yaw,float pitch){
  int variant=tier(state);
  if(variant==0)return;
  boolean installed=has(state.chestEquipment,"micro_mg")
     ||has(state.headEquipment,"micro_mg")
     ||has(state.legsEquipment,"micro_mg")
     ||has(state.feetEquipment,"micro_mg");
  if(!installed)return;
  boolean active=has(state.chestEquipment,"micro_mg_turret_on")
       ||state.rightArmPose.x()<-40.0F;
  if(!active)return;
  // Already yaw-rotated by ArmorStandRenderer and posed by setupAnim.
  // No world-space pose guesses, no entity id, no dependence on EXTENSION.
  PoseStack gunPose=new PoseStack();
  gunPose.mulPose(new org.joml.Matrix4f(pose.last().pose()));
  RIGHT_ARM_PIVOT.xRot=(float)Math.toRadians(state.rightArmPose.x());
  RIGHT_ARM_PIVOT.yRot=(float)Math.toRadians(state.rightArmPose.y());
  RIGHT_ARM_PIVOT.zRot=(float)Math.toRadians(state.rightArmPose.z());
  V176MicroMgVisualClient.drawArm(gunPose,nodes,light,
      RIGHT_ARM_PIVOT,variant,1.0F);
 }
 @EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
 public static final class Register {
  private Register(){}
  @SubscribeEvent public static void layers(EntityRenderersEvent.AddLayers event){
   var renderer=event.getRenderer(EntityType.ARMOR_STAND);
   if(renderer instanceof ArmorStandRenderer standRenderer){
    standRenderer.addLayer((RenderLayer)new V176MicroMgStandLayer(standRenderer));
    System.out.println("XSXLABS_B1032_TURRET_LAYER_REGISTERED");
   }else{
    System.err.println("XSXLABS_B1032_TURRET_LAYER_MISSING");
   }
  }
 }
}
''',encoding="utf-8")

# 3. Drive membership: graph-listed drives are authoritative, but additional
# loaded drives directly touching the same physical NETWORK graph may have a
# null accessory/drive runtime on a given tick. Include them only by physical
# connectivity to the known powered graph, never via arbitrary blocks.
top="cellterminal/V176CellTerminalTopology.java"
s=load(top)
start,end,old=method(s," private static List<StorageDriveBlockEntity> physicalDrives(")
assert "nextNet!=identity" in old
assert "if(level.getBlockEntity(next) instanceof StorageDriveBlockEntity drive)" in old
new=r''' private static List<StorageDriveBlockEntity> physicalDrives(
       ServerLevel level,BlockPos terminal,NetworkRuntime identity){
  var pending=new ArrayDeque<BlockPos>();
  var seen=new HashSet<Long>();
  var found=new LinkedHashMap<Long,StorageDriveBlockEntity>();
  pending.add(terminal);
  while(!pending.isEmpty()&&seen.size()<16384&&found.size()<2048){
   BlockPos current=pending.removeFirst();
   if(!level.hasChunkAt(current)||!seen.add(current.asLong()))continue;
   if(!current.equals(terminal)){
    NetworkRuntime currentNet=attached(level,current);
    if(currentNet!=null&&currentNet!=identity)continue;
    // Do not walk arbitrary blocks in the world.
    if(currentNet!=identity&&!cable(level,current))continue;
   }
   for(Direction face:Direction.values()){
    BlockPos next=current.relative(face);
    if(!level.hasChunkAt(next))continue;
    NetworkRuntime nextNet=attached(level,next);
    if(nextNet!=null&&nextNet!=identity)continue;
    if(level.getBlockEntity(next) instanceof StorageDriveBlockEntity drive){
     // A null runtime can be a valid freshly-connected Drive. The connection
     // to this powered NETWORK component was verified by the path above.
     if(!drive.isRemoved())found.putIfAbsent(next.asLong(),drive);
    }else if((nextNet==identity||cable(level,next))
               &&!seen.contains(next.asLong())){
     pending.addLast(next);
    }
   }
  }
  return List.copyOf(found.values());
 }
'''
s=s[:start]+new+s[end:]
# Keep every graph-verified drive, avoid re-checking it against a second,
# sometimes stale runtime lookup. The authoritative graph selected identity.
old='''  for(StorageDriveBlockEntity drive:WorldTopologyBridge.xsxCellTerminalDrives(world,identity)){
   if(!drive.isRemoved()&&world.hasChunkAt(drive.getBlockPos())
       &&WorldTopologyBridge.runtimeForDrive(world,drive.getBlockPos())==identity)
    all.put(drive.getBlockPos().asLong(),drive);
  }'''
new='''  for(StorageDriveBlockEntity drive:WorldTopologyBridge.xsxCellTerminalDrives(world,identity)){
   if(!drive.isRemoved()&&world.hasChunkAt(drive.getBlockPos()))
    all.put(drive.getBlockPos().asLong(),drive);
  }'''
assert s.count(old)==1,("B1032_REGISTERED_DRIVES_GUARD",s.count(old))
s=s.replace(old,new,1)
assert "for(StorageDriveBlockEntity drive:physicalDrives(world,terminal,identity))" in s
save(top,s)

# Expose transfer diagnostics only on input actions. Never remove the cursor
# cell merely because the client showed a pad: the existing DriveMenu write,
# exact ItemStack NBT readback and only-then shrink remain authoritative.
menu="cellterminal/V176CellTerminalMenu.java"
m=load(menu)
assert "if(slotId>=0&&slotId<8)" in m
assert "backing.setItem(target,one);" in m
assert "if(!ItemStack.matches(backing.getItem(target),one))" in m
assert "carried.shrink(1);" in m
assert "broadcastFullState();" in m
a,b,clicked=method(m," @Override public void clicked(")
anchor='''   var scan=V176CellTerminalTopology.scan(world,terminal.getBlockPos());'''
assert clicked.count(anchor)==1
clicked=clicked.replace(anchor,anchor+'''
   System.out.println("XSXLABS_B1032_CELL_INPUT online="+scan.online()
      +" connectedDrives="+scan.drives().size()+" freeSlots="+scan.freeSlots());''',1)
m=m[:a]+clicked+m[b:]
save(menu,m)

v=load(weapon)
l=load(layer)
t=load(top)
assert "submitModelPart(XSX_WORLD_BARREL,pose" in v
assert "RIGHT_ARM_PIVOT,variant,1.0F" in stand.read_text(encoding="utf-8")
assert "V176MicroMgVisualClient.drawArm(xsxWeaponPose" in l
assert "V176MicroMgVisualClient.markLayerSubmitted(state.id)" not in l
assert "XSXLABS_B1032_CELL_INPUT" in load(menu)
assert "if(nextNet!=null&&nextNet!=identity)continue;" in t
assert "if(!drive.isRemoved())found.putIfAbsent" in t
print("B1032_PLAYER_YAW_ATTACHED_NATIVE_LAYER_TURRET_STAND_EQUIPMENT_STATE_DRIVE_NULL_RUNTIME_PATH_SAFE_CELLS_PASS")
