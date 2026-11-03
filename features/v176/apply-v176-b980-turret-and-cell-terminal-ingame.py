#!/usr/bin/env python3
"""B980 user-approved ingame repairs. Temporary Turret diagnostics are removable.

- Temporary renderer-phase tracing ONLY for active world-suit turret.
- ArmorStand world-gun no longer submits with Minecraft's caller PoseStack.
- Distinct slimmer 3P barrel removes large, floating 3P mounting plate.
- Preserve first-person right elbow quaternion and gun placement EXACTLY.
- First-person lower forearm uses the worn power armor 24-tier atlas, no
  artificial skinned upper arm, no sleeve overlay.
- Worn backpack slightly larger and lower, all 24 palettes/placed blocks safe.
- Cell terminal uses authoritative graph membership/drive bindings, not a
  cable-only BFS; connects through neighboring crafting terminals/devices.
- Cell Terminal exterior derives from purple Crafting Terminal geometry and
  violet/gunmetal material, no face-cull occlusion.
"""
import os,json
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])
A=R/"assets/obsidiannetwork"

def change(rel,old,new):
 p=J/rel
 s=p.read_text(encoding="utf-8")
 n=s.count(old)
 assert n==1,("B980_SOURCE_DRIFT",rel,n,old[:120])
 p.write_text(s.replace(old,new,1),encoding="utf-8")

def set_source(rel,text):
 p=J/rel
 assert p.exists(),("B980_MISSING",rel)
 p.write_text(text,encoding="utf-8")

# --- CELL TERMINAL: authoritative existing NetworkGraph, not local cable BFS.
# The Cell Terminal isn't itself registered as a vanilla crafting terminal in
# topology, so use its adjacent already-registered network node. This accepts
# direct adjacency to crafting terminals, drives, controllers AND network wires.
# WorldTopologyBridge's s.drives contains ALL registered loaded drive nodes;
# only return ones with runtimeForDrive == the selected active controller.
bridge="network/WorldTopologyBridge.java"
change(bridge,
"   public static NetworkRuntime runtimeForAccessory(ServerLevel level, BlockPos pos) {",
"""   // B980 Cell Terminal adjacency to ANY registered graph node, including
   // a Crafting Terminal (not only an exposed cable block). No chunk loads.
   public static NetworkRuntime xsxCellTerminalNetwork(ServerLevel level, BlockPos pos) {
      if (level==null||pos==null||!level.hasChunkAt(pos)) return null;
      for(Direction face:Direction.values()){
         BlockPos neighbor=pos.relative(face);
         if(!level.hasChunkAt(neighbor))continue;
         NetworkRuntime network=runtimeForTerminal(level,neighbor);
         if(network==null)network=runtimeForDrive(level,neighbor);
         if(network==null)network=runtimeForController(level,neighbor);
         if(network==null)network=runtimeForAccessory(level,neighbor);
         if(network!=null&&network.powered())return network;
      }
      return null;
   }
   // Use existing authoritative drive registry + component binding. A single
   // physically adjacent network cannot ever pick up another network's drives.
   public static java.util.List<StorageDriveBlockEntity> xsxCellTerminalDrives(
        ServerLevel level,NetworkRuntime network) {
      WorldTopologyBridge.LevelTopology s=LEVELS.get(level);
      if(s==null||network==null)return java.util.List.of();
      java.util.ArrayList<StorageDriveBlockEntity> found=new java.util.ArrayList<>();
      for(NetworkGraph.Pos node:s.drives){
         if(found.size()>=2048)break;
         BlockPos pos=new BlockPos(node.x(),node.y(),node.z());
         if(level.hasChunkAt(pos)&&runtimeForDrive(level,pos)==network
            &&level.getBlockEntity(pos) instanceof StorageDriveBlockEntity drive
            &&!drive.isRemoved())found.add(drive);
      }
      found.sort(java.util.Comparator.comparingLong(b->b.getBlockPos().asLong()));
      return java.util.List.copyOf(found);
   }

   public static NetworkRuntime runtimeForAccessory(ServerLevel level, BlockPos pos) {""")

topology=r'''package dev.obsidiannetwork.cellterminal;

import dev.obsidiannetwork.blockentity.StorageDriveBlockEntity;
import dev.obsidiannetwork.core.NetworkRuntime;
import dev.obsidiannetwork.network.WorldTopologyBridge;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import java.util.List;

/** Uses authoritative existing world graph, not isolated physical-cable BFS.
 *  One locally adjacent ACTIVE network only, no foreign-network drives,
 *  no forced chunk loads; every shift click rescans server-side.
 */
public final class V176CellTerminalTopology {
 private V176CellTerminalTopology(){}
 public record Scan(boolean online,List<StorageDriveBlockEntity> drives,
                    int freeSlots,boolean truncated){}
 public static Scan scan(ServerLevel world,BlockPos terminal){
  if(!world.hasChunkAt(terminal)||
     !(world.getBlockEntity(terminal) instanceof V176CellTerminalBlockEntity))
     return new Scan(false,List.of(),0,false);
  NetworkRuntime network=WorldTopologyBridge.xsxCellTerminalNetwork(world,terminal);
  if(network==null||!network.powered())return new Scan(false,List.of(),0,false);
  List<StorageDriveBlockEntity> drives=WorldTopologyBridge.xsxCellTerminalDrives(world,network);
  int free=0;
  for(StorageDriveBlockEntity drive:drives)
   free+=Math.max(0,16-drive.occupiedSlots());
  return new Scan(true,drives,free,drives.size()>=2048);
 }
}
'''
set_source("cellterminal/V176CellTerminalTopology.java",topology)
# Do not change DriveMenu backing transfer code or its stack-consumption order.
cellmenu=(J/"cellterminal/V176CellTerminalMenu.java").read_text()
assert "backing.setItem(targetSlot,one);" in cellmenu
assert cellmenu.index("backing.setItem(targetSlot,one);")<cellmenu.index("carried.shrink(transferred);")
assert "if(!ItemStack.matches(inserted,one))" in cellmenu

# --- CRAFTING TERMINAL VISUAL MATERIALS, retaining functional machine front.
# The old white/Power-Monitor cube is NOT the accepted Network Storage style.
craft=A/"models/block/crafting_terminal.json"
assert craft.is_file(),("B980_CRAFTING_TERMINAL_MODEL_MISSING",craft)
model=json.loads(craft.read_text(encoding="utf-8"))
assert len(model.get("elements",[]))>=1, "B980_CRAFTING_MODEL_WITHOUT_GEOMETRY"
tex=model.get("textures",{})
assert tex.get("ns_violet") and tex.get("ns_chassis"),"B980_PURPLE_PALETTE_DRIFT"
model["textures"]["ns_violet"]="obsidiannetwork:block/ns_violet_glow"
model["textures"]["ns_data"]="obsidiannetwork:block/ns_data_glow_strong"
model["textures"]["ns_status"]="obsidiannetwork:block/ns_status_glow_strong"
model["ambientocclusion"]=False
def strip_cull(value):
 if isinstance(value,dict):
  value.pop("cullface",None)
  for child in value.values():strip_cull(child)
 elif isinstance(value,list):
  for child in value:strip_cull(child)
strip_cull(model)
assert all(e.get("faces") for e in model["elements"])
(A/"models/block/cell_terminal.json").write_text(json.dumps(model,indent=2)+"\n",encoding="utf-8")
assert "cullface" not in json.dumps(model)
# noOcclusion() already registered in Block.Properties for the Cell Terminal.
assert "noOcclusion()" in (J/"ObsidianNetwork.java").read_text()
# Preserve its own facing blockstate, item model, recipe and GUI.
for rel in ("blockstates/cell_terminal.json","items/cell_terminal.json"):
 assert (A/rel).exists(),("B980_CELL_TERMINAL_ASSET_MISSING",rel)

# --- FIRST PERSON armor forearm, keep existing elbow/gun transform unchanged.
visual="client/V176MicroMgVisualClient.java"
p=J/visual
s=p.read_text(encoding="utf-8")
# Place the true Power Armor lower-arm mesh in the existing first-person
# two-piece model geometry. Vanilla 64x32 humanoid armor atlas, right arm
# lower half uses texOffs(40,22). Inflated outer shell avoids bare-skin seams.
anchor=" private static final ModelPart XSX_SLEEVE_LOWER_SLIM=xsxArmSection(true,true,true);"
assert s.count(anchor)==1,"B980_ARM_HELPERS_DRIFT"
armor=r'''
 // The tier armor atlas is 64x32; use actual armor pixels, not player skin.
 // Armor lower-arm surface stays in the established 1P elbow frame.
 private static final ModelPart XSX_POWER_LOWER=xsxPowerForearm();
 private static ModelPart xsxPowerForearm(){
  MeshDefinition mesh=new MeshDefinition();
  mesh.getRoot().addOrReplaceChild("xsx_power_forearm",
    CubeListBuilder.create().texOffs(40,22).addBox(
       -3.0F,4.0F,-2.0F,4.0F,6.0F,4.0F,
       new net.minecraft.client.model.geom.builders.CubeDeformation(0.28F)),
    PartPose.offset(-5.0F,2.0F,0.0F));
  return LayerDefinition.create(mesh,64,32).bakeRoot().getChild("xsx_power_forearm");
 }
'''
s=s.replace(anchor,anchor+"\n"+armor,1)
first=" @SubscribeEvent public static void firstPerson(RenderHandEvent event){"
legacy=" @SubscribeEvent public static void xsxlabs$aimVisibleFirstPersonArm(RenderArmEvent event){"
assert s.count(first)==s.count(legacy)==1
a=s.index(first);b=s.index(legacy,a)
hand=s[a:b]
# Skin upper arm and sleeve do not belong to this user's chosen 1P view.
old='''  nodes.submitModelPart(upper,pose,skin,light,OverlayTexture.NO_OVERLAY,
      null,false,false,0xFFFFFFFF,null,0);
  if(sleeve)
   nodes.submitModelPart(upperSleeve,pose,skin,light,OverlayTexture.NO_OVERLAY,
       null,false,false,0xFFFFFFFF,null,0);'''
assert hand.count(old)==1, "B980_UPPER_ARM_RENDER_NOT_FOUND"
hand=hand.replace(old,'''  // Upper shoulder and upper arm are deliberately INVISIBLE in 1P Attack.
  // Only the hinged armor forearm is submitted further below.''',1)
old='''   nodes.submitModelPart(lower,pose,skin,light,OverlayTexture.NO_OVERLAY,
       null,false,false,0xFFFFFFFF,null,0);
   if(sleeve)
    nodes.submitModelPart(lowerSleeve,pose,skin,light,OverlayTexture.NO_OVERLAY,
        null,false,false,0xFFFFFFFF,null,0);'''
assert hand.count(old)==1, "B980_FOREARM_DRAW_NOT_FOUND"
hand=hand.replace(old,'''   String armorName=equippedTier==1?"power_armor":"power_armor_mk"+equippedTier;
   var armorAtlas=RenderTypes.entitySolid(
       Identifier.fromNamespaceAndPath("obsidiannetwork",
          "textures/entity/equipment/humanoid/"+armorName+".png"));
   nodes.submitModelPart(XSX_POWER_LOWER,pose,armorAtlas,light,
       OverlayTexture.NO_OVERLAY,null,false,false,0xFFFFFFFF,null,0);''',1)
# Keep EXACT previously approved pivot and barrel mount.
for marker in ("org.joml.Quaternionf interpolated","pose.mulPose(interpolated)",
 "pose.translate(-5.0F/16.0F,6.0F/16.0F,0.0F);",
 "pose.translate(-5.0F/16.0F,2.0F/16.0F,0.0F);",
 "nodes.submitModelPart(BARREL,pose"):
 assert marker in hand,("B980_USER_APPROVED_1P_POSITION_DRIFT",marker)
assert "nodes.submitModelPart(upper,pose" not in hand
assert "nodes.submitModelPart(lower,pose,skin" not in hand
s=s[:a]+hand+s[b:]
# The 3P barrel must not reuse 1P plate geometry. Its gun mount gets a
# slim world-only model, leaving the approved first-person BARREL untouched.
barrel_anchor=" private static final ModelPart BARREL=createBarrel();"
assert s.count(barrel_anchor)==1, "B980_BARREL_MODEL_ANCHOR_DRIFT"
world_model=r'''
 // World-only slim barrel; removes black, floating 3P square rail/end plate.
 // Keep first-person BARREL unchanged and in exactly its established frame.
 private static final ModelPart XSX_WORLD_BARREL=xsxWorldBarrel();
 private static ModelPart xsxWorldBarrel(){
  MeshDefinition mesh=new MeshDefinition();
  mesh.getRoot().addOrReplaceChild("xsx_world_barrel",
    CubeListBuilder.create().texOffs(0,0)
       .addBox(-0.62F,5.0F,-3.15F,1.24F,8.5F,1.25F),PartPose.ZERO);
  return LayerDefinition.create(mesh,32,32).bakeRoot().getChild("xsx_world_barrel");
 }
'''
s=s.replace(barrel_anchor,barrel_anchor+"\n"+world_model,1)
# Only the 3P submit drawArm() changes. First person uses separate BARREL.
draw_start=s.index(" public static void drawArm(")
draw_end=s.index("\n }",draw_start)+3
draw=s[draw_start:draw_end]
assert "parent.translateAndRotate(pose);" in draw,"B980_WORLD_ARM_PIVOT_DRIFT"
assert "nodes.submitModelPart(BARREL,pose" in draw,"B980_WORLD_BARREL_SUBMIT_DRIFT"
draw=draw.replace("parent.translateAndRotate(pose);",
'''parent.translateAndRotate(pose);
  // Move the front-mounted world barrel down onto the armor arm surface,
  // without changing the first-person gun's already-correct position.
  pose.translate(0.0F,0.0F,-0.075F);''',1)
draw=draw.replace("nodes.submitModelPart(BARREL,pose","nodes.submitModelPart(XSX_WORLD_BARREL,pose",1)
s=s[:draw_start]+draw+s[draw_end:]
# Complete isolation for *ArmorStand* world-suit turret renderer, not just
# the B973 player attachment renderer. The old handler was still submitting
# with the caller's LevelRenderer pose.
world_marker=" @SubscribeEvent public static void worldSuit("
assert s.count(world_marker)==1, "B980_WORLDSUIT_DUPLICATE"
start=s.index(world_marker)
brace=s.index("{",start)
depth=0
stop=None
for i in range(brace,len(s)):
 if s[i]=="{":depth+=1
 elif s[i]=="}":
  depth-=1
  if depth==0:
   stop=i+1
   break
assert stop is not None,"B980_WORLDSUIT_METHOD_UNCLOSED"
method=s[start:stop]
assert "event.getPoseStack()" in method and "drawPair(" in method,"B980_WORLD_ARM_SOURCE_DRIFT"
method=method.replace("event.getPoseStack()","xsxTurretPose")
method=method.replace("{\n",'''{
  // TEMP DIAGNOSTICS B980: remove after user verifies that both 3P and
  // deployed turret are crash-free. Never touch the renderer's live pose.
  PoseStack xsxTurretPose=new PoseStack();
  xsxTurretPose.mulPose(new org.joml.Matrix4f(event.getPoseStack().last().pose()));
''',1)
# All world-suit 3P gun geometry on right arm, never mirrored left.
assert "drawPair(xsxTurretPose,event.getSubmitNodeCollector()," in method
method=method.replace("drawPair(xsxTurretPose,event.getSubmitNodeCollector(),",
 "drawArm(xsxTurretPose,event.getSubmitNodeCollector(),",1)
assert "state.lightCoords,model,tier,amount" in method
method=method.replace("state.lightCoords,model,tier,amount","state.lightCoords,model.rightArm,tier,amount",1)
# Emit a low-frequency stage marker only while a deployed world turret is
# visible. The trace survives in latest.log if another mod leaks a stack.
needle="    drawArm(xsxTurretPose,event.getSubmitNodeCollector(),"
# expression likely at 4-column indent
if needle not in method:needle="drawArm(xsxTurretPose,event.getSubmitNodeCollector(),"
assert needle in method,"B980_WORLD_DRAW_DIAG_ANCHOR"
method=method.replace(needle,'''    xsxLogTurretPose(stand.getId(),tier,amount,"ENTER");
    drawArm(xsxTurretPose,event.getSubmitNodeCollector(),''',1)
needle="state.lightCoords,model.rightArm,tier,amount);"
assert needle in method
method=method.replace(needle,needle+'''
   xsxLogTurretPose(stand.getId(),tier,amount,"EXIT");''',1)
s=s[:start]+method+s[stop:]
# Instrument only every 100th call per armor stand; do not spam each frame.
diag=r'''
 private static final java.util.Map<Integer,Integer> XSX_TURRET_DIAG_FRAMES=
      new java.util.HashMap<>();
 private static void xsxLogTurretPose(int id,int tier,float extension,String phase){
  int frame=XSX_TURRET_DIAG_FRAMES.getOrDefault(id,0);
  if("ENTER".equals(phase)){
   frame++;
   XSX_TURRET_DIAG_FRAMES.put(id,frame);
  }
  if(frame==1||frame%100==0)
   System.err.println("XSXLABS_TEMP_B980_TURRET_RENDER phase="+phase+
     " entity="+id+" tier="+tier+" extension="+extension+" frame="+frame);
 }
'''
assert s.count(world_marker)==1
s=s.replace(world_marker,diag+"\n"+world_marker,1)
set_source(visual,s)

# --- backpack slightly larger and lower only while WORN.
change("client/V176BackpackWornRenderer.java",
 "  pose.scale(1.35F,1.35F,1.35F);",
 "  pose.scale(1.47F,1.47F,1.47F);")
change("client/V176BackpackWornRenderer.java",
 "  pose.translate(0.0F,event.getRenderState().isCrouching?1.04F:1.35F,.29F);",
 "  pose.translate(0.0F,event.getRenderState().isCrouching?.92F:1.23F,.29F);")

# Confirm no mutation of approved third-person PLAYER gun isolation.
layer=(J/"client/V176MicroMgLayer.java").read_text()
assert "xsxWeaponPose=new PoseStack()" in layer
assert "V176MicroMgVisualClient.drawArm(xsxWeaponPose" in layer
assert "V176AttackPoseContext.aim(state)" in (J/"mixin/V176AttackRightArmMixin.java").read_text()
world=(J/visual).read_text()
assert "XSXLABS_TEMP_B980_TURRET_RENDER" in world
assert "xsxTurretPose.mulPose(new org.joml.Matrix4f(event.getPoseStack().last().pose()))" in world
assert "nodes.submitModelPart(XSX_POWER_LOWER,pose,armorAtlas" in world
assert "nodes.submitModelPart(XSX_WORLD_BARREL,pose" in world
assert "nodes.submitModelPart(BARREL,pose" in world
assert "pose.scale(1.47F,1.47F,1.47F)" in (J/"client/V176BackpackWornRenderer.java").read_text()
assert "xsxCellTerminalNetwork(ServerLevel level, BlockPos pos)" in (J/bridge).read_text()
assert "xsxCellTerminalDrives(" in (J/bridge).read_text()
assert "WorldTopologyBridge.xsxCellTerminalDrives(world,network)" in (J/"cellterminal/V176CellTerminalTopology.java").read_text()
assert '"cullface"' not in (A/"models/block/cell_terminal.json").read_text()
print("B980_3P_TURRET_POSE_ISOLATED_TEMP_DIAG_1P_ARMOR_FOREARM_ONLY_WORLD_BARREL_BLACK_PLATE_REMOVED_BACKPACK_147_PURPLE_CELL_NETWORK_GRAPH_PASS")
