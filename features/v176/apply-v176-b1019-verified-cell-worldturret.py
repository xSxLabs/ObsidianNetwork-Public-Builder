#!/usr/bin/env python3
"""B1019: Root-cause fix for Build 1018 red in-game tests.

Inspect B1014's actual compiled bytecode before editing: the old HATCH
if-statement accidentally captures pose.popPose() at full deployment,
leaving the world gun attached to the rotated hatch transform. Rewrite
the whole 3P draw path as a single balanced gun-only scoped submission.
The separate 1P BARREL and camera code MUST remain byte-identical.

Turret: look up the rendered ArmorStand by the render-state entity ID, not a
nearby-AABB search; derive ON from the server-synced -80deg right-arm pose
and equipment token as well as entity tags.

Cell Terminal: treat the eight visual slots as click-through ACTION pads,
not actual ChestMenu items. Client mayPlace=false prevents fake deposits;
server overrides clicked and writes only verified physical Drive slots.
Use network-identity-gated cable fallback if graph drive registry is stale.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def load(path):return (J/path).read_text(encoding="utf-8")
def save(path,src):(J/path).write_text(src,encoding="utf-8")
def balanced(src,needle):
 pos=src.index(needle)
 brace=src.index("{",pos)
 depth=0
 for end in range(brace,len(src)):
  if src[end]=="{":depth+=1
  elif src[end]=="}":
   depth-=1
   if depth==0:return (pos,end+1,src[pos:end+1])
 raise AssertionError(("B1019_BRACE_UNCLOSED",needle))

# 1. The old B745 HATCH branch contains a conditional popPose() after B957
# eliminated hatch submission. B1014's angle tweak never corrected this.
# At full gunOut=1, hatchOpen=1, the inner matrix is not popped; its -16 deg
# hatch transform contaminates the barrel. Completely remove the branch.
weapon="client/V176MicroMgVisualClient.java"
s=load(weapon)
start,end,old=balanced(s," public static void drawArm(")
assert "float hatchOpen=phase(" in old
assert "nodes.submitModelPart(XSX_WORLD_BARREL,pose" in old
assert "pose.translate(0.0F,8.3F/16.0F" in old
assert "nodes.submitModelPart(HATCH,pose" not in old
new=''' public static void drawArm(PoseStack pose,SubmitNodeCollector nodes,int light,
     ModelPart parent,int tier,float extension){
  // Never draw a moving hatch. Both frame stack and geometry belong to
  // exactly one right forearm, in the ACTUAL animated arm coordinate frame.
  float gunOut=phase(extension,7.0F/12.0F,1.0F);
  if(gunOut<=0.001F)return;
  pose.pushPose();
  try{
   parent.translateAndRotate(pose);
   // Local model pixels: upper arm ends at y~6, wrist at y~12.
   // A square-edged armored forearm has a constant dorsal z surface.
   // The only visible shape lies y=6.8..11.5 and z=-2.95..-2.30:
   // its underside touches that surface at front AND back.
   // No inherited hatch tilt, no shoulder plate, no dangling frame.
   pose.translate(0.0F,-(1.0F-gunOut)*0.26F,-0.014F);
   nodes.submitModelPart(XSX_WORLD_BARREL,pose,RenderTypes.entitySolid(
       Identifier.fromNamespaceAndPath("obsidiannetwork",
       "textures/entity/micro_mg_world_barrel.png")),
       light,OverlayTexture.NO_OVERLAY,null,false,false,0xFFFFFFFF,null,0);
  }finally{
   pose.popPose();
  }
 }'''
s=s[:start]+new+s[end:]
assert s.count(".addBox(-0.45F,6.1F,-2.85F,0.90F,6.6F,0.83F)")==1
s=s.replace(".addBox(-0.45F,6.1F,-2.85F,0.90F,6.6F,0.83F)",
            ".addBox(-0.46F,6.8F,-2.95F,0.92F,4.7F,0.65F)",1)
# The unused HATCH model is not allowed to reappear as a second black slab.
assert "nodes.submitModelPart(HATCH,pose" not in s
assert "submitModelPart(HATCH,pose" not in s
s=s.replace(" private static final ModelPart HATCH=createHatch();\n","",1)
if " private static ModelPart createHatch(){" in s:
 a,b,_=balanced(s," private static ModelPart createHatch(){")
 s=s[:a]+s[b:]
assert "createHatch()" not in s
# The world turret renderer used proximity to an interpolated render-state
# x/z. On a moving ArmorStand it matched poorly; actual state.id is exact.
# Official NeoForge 26.1 render-state modifier captures the exact
# ArmorStand ID during extraction. LivingEntityRenderState has NO .id field.
anchor=" private V176MicroMgVisualClient(){}"
assert s.count(anchor)==1, "B1019_RENDER_STATE_KEY_ANCHOR"
s=s.replace(anchor,anchor+'''
 // Render-state attachment: exact stand identity, no tick-vs-frame AABB.
 private static final net.neoforged.neoforge.client.renderstate.ContextKey<Integer>
     XSX_STAND_RENDER_ID=new net.neoforged.neoforge.client.renderstate.ContextKey<>(
       Identifier.fromNamespaceAndPath("obsidiannetwork","v176_turret_stand_id"));
 @SubscribeEvent public static void xsxCaptureTurretStandId(
      net.neoforged.neoforge.client.renderstate.RegisterRenderStateModifiersEvent event){
  event.registerEntityModifier(net.minecraft.client.renderer.entity.ArmorStandRenderer.class,
       (stand,state)->state.setRenderData(XSX_STAND_RENDER_ID,stand.getId()));
 }
''',1)
a,b,old=balanced(s," @SubscribeEvent public static void worldSuit(")
assert "getEntitiesOfClass(ArmorStand.class,box)" in old, "B1019_OLD_AABB_GUARD"
assert 'xsxLogTurretPose(' in old, "B1019_DIAG_GUARD"
assert 'stand.getRightArmPose().x()<-35F' in old
new=''' @SubscribeEvent public static void worldSuit(RenderLivingEvent.Post<?,?,?> event){
  Minecraft mc=Minecraft.getInstance();
  if(mc.level==null)return;
  var state=event.getRenderState();
  // This is the very same tracked entity currently being rendered. Do not
  // compare interpolated x/z to a separate tick-position AABB.
  Integer xsxId=state.getRenderData(XSX_STAND_RENDER_ID);
  if(xsxId==null)return;
  Entity entity=mc.level.getEntity(xsxId);
  if(!(entity instanceof ArmorStand stand)||!stand.isAlive()||stand.isInvisible())return;
  int suitTier=tier(stand);
  if(suitTier<1)return;
  ItemStack chest=stand.getItemBySlot(EquipmentSlot.CHEST);
  // Server V176CompanionMode.walkingPose(true) synchronizes -80deg right arm.
  // ArmorStand scoreboard tags alone are not a reliable CLIENT condition.
  boolean installed=has(chest,"micro_mg");
  boolean turret=installed && (has(chest,"micro_mg_turret_on")
      ||stand.getRightArmPose().x()<-40.0F
      ||stand.entityTags().contains("xsxlabs_v176_turret"));
  float amount=extension(stand.getId(),turret);
  if(amount<=0.001F)return;
  if(!(event.getRenderer().getModel() instanceof HumanoidModel<?> model))return;
  // Dedicated render pose independent of LevelRenderer and player pose.
  PoseStack xsxTurretPose=new PoseStack();
  xsxTurretPose.mulPose(new org.joml.Matrix4f(event.getPoseStack().last().pose()));
  xsxLogTurretPose(stand.getId(),suitTier,amount,"ENTER");
  drawRight(xsxTurretPose,event.getSubmitNodeCollector(),
       state.lightCoords,model,suitTier,amount,true);
  xsxLogTurretPose(stand.getId(),suitTier,amount,"EXIT");
 }'''
s=s[:a]+new+s[b:]
assert "getEntitiesOfClass(ArmorStand.class,box)" not in s
assert "mc.level.getEntity(state.id)" in s
assert "if(event.getRenderState().entityType!=EntityType.ARMOR_STAND)" not in s
# The 1P method, helpers, and BARREL part must be EXACTLY preserved.
assert s.count(" public static void firstPerson(RenderHandEvent event){")==1
assert s.count("nodes.submitModelPart(BARREL,pose")==1
assert s.count(" private static ModelPart createBarrel(){")==1
assert "nodes.submitModelPart(XSX_WORLD_BARREL,pose" in s
save(weapon,s)

# 2. Eight action pads: never let vanilla client predict putting a real Cell
# into the fake 54-slot SimpleContainer. It will not be 'stuck' on the client
# and cannot be stored by a malicious click packet. Server clicked() is still
# the only path that installs the exact original NBT into the real drive.
menu="cellterminal/V176CellTerminalMenu.java"
screen="client/V176CellTerminalScreen.java"
for path in (menu,screen):
 s=load(path)
 a=s.index("  for(int pad=0;pad<8;pad++){")
 b=s.index("\n  }",a)+4
 block=s[a:b]
 assert "isActive(){return true;}" in block and "mayPickup" in block
 assert "mayPlace" in block
 p=block.index("    @Override public boolean mayPlace(ItemStack item){")
 q=block.index("\n    @Override public boolean mayPickup",p)
 # The server still intercepts the clicked action to process the cursor.
 block=block[:p]+'''    @Override public boolean mayPlace(ItemStack item){return false;}
'''.rstrip("\n")+block[q:]
 s=s[:a]+block+s[b:]
 assert "mayPlace(ItemStack item){return false;}" in s
 save(path,s)

# Server accepts both real StorageCellItem and EquipmentCellItem, exactly as
# DriveMenu's BE-backed DriveContainer does. Nothing remains in terminal.
s=load(menu)
assert s.count("carried.getItem() instanceof StorageCellItem")==2 or s.count("carried.getItem() instanceof StorageCellItem")==1
s=s.replace("!(carried.getItem() instanceof StorageCellItem)",
 '''!(carried.getItem() instanceof StorageCellItem
         ||carried.getItem() instanceof dev.obsidiannetwork.item.EquipmentCellItem)''')
assert "if(slotId>=0&&slotId<8)" in s
# On both failed and successful attempts force empty action-pad inventory sync.
# This prevents stale client cells even if the cursor update was delayed.
start,end,clicked=balanced(s," @Override public void clicked(")
assert "terminal.xsxRefresh(world)" in clicked
assert "setCarried(carried)" in clicked
# Client message tells why an apparently connected network rejected a cell.
clicked=clicked.replace('''   if(!scan.online()||scan.freeSlots()<1)return;''',
'''   if(!scan.online()||scan.freeSlots()<1){
    server.connection.send(
      new net.minecraft.network.protocol.game.ClientboundSetActionBarTextPacket(
       net.minecraft.network.chat.Component.literal(
        !scan.online()?"Cell Terminal: Netzwerk OFFLINE":
        "Cell Terminal: Keine freien Drive-Slots")));
    broadcastFullState();
    return;
   }''')
assert "Cell Terminal: Netzwerk OFFLINE" in clicked
clicked=clicked.replace("    broadcastChanges();\n    return;",
                        "    broadcastFullState();\n    return;",1)
# If a full scan yields no verified slot despite claims, explain the issue.
needle='''   }
   return;
  }
  // All other 46 virtual preview slots remain disabled.'''
assert needle in clicked,("B1019_CLICKED_TAIL_DRIFT",clicked[-350:])
clicked=clicked.replace(needle,'''   }
   server.connection.send(
     new net.minecraft.network.protocol.game.ClientboundSetActionBarTextPacket(
      net.minecraft.network.chat.Component.literal(
       "Cell Terminal: Kein passender freier Drive-Slot gefunden")));
   broadcastFullState();
   return;
  }
  // All other 46 virtual preview slots remain disabled.''',1)
s=s[:start]+clicked+s[end:]
# Make shift-click refresh complete tracking too: no ghosts in player inventory.
assert "  terminal.xsxRefresh(world);\n  broadcastChanges();\n  return original;" in s
s=s.replace("  terminal.xsxRefresh(world);\n  broadcastChanges();\n  return original;",
'''  terminal.xsxRefresh(world);
  broadcastFullState();
  return original;''',1)
save(menu,s)

# 3. Use fallback physically connected NETWORK cable component to catch
# valid drives missing the stale LevelTopology.drive registry. This never
# crosses to a drive explicitly bound to another controller.
top="cellterminal/V176CellTerminalTopology.java"
s=load(top)
needle="  List<StorageDriveBlockEntity> drives=WorldTopologyBridge.xsxCellTerminalDrives(world,network);"
assert s.count(needle)==1,("B1019_GRAPH_LIST_ANCHOR_DRIFT",s.count(needle))
s=s.replace(needle,'''  // Prefer authoritative graph; supplement it with verified loaded
  // drives physically touching this same network's cable component.
  var all=new java.util.LinkedHashMap<Long,StorageDriveBlockEntity>();
  for(var drive:WorldTopologyBridge.xsxCellTerminalDrives(world,network))
   all.put(drive.getBlockPos().asLong(),drive);
  // Cable discovery is a fallback, not a per-tick full-network scan.
  boolean graphHasFree=false;
  for(var drive:all.values())
   if(drive.xsxCellTerminalFirstEmptySlot()>=0){graphHasFree=true;break;}
  if(!graphHasFree){
   for(var drive:xsxCableDrives(world,terminal,network))
    all.putIfAbsent(drive.getBlockPos().asLong(),drive);
  }
  List<StorageDriveBlockEntity> drives=new java.util.ArrayList<>(all.values());''',1)
idx=s.index(" public static Scan scan(")
helper=''' // At most 16k loaded wire positions. Never load another chunk and never
 // merge a Drive bound to a different network identity.
 private static List<StorageDriveBlockEntity> xsxCableDrives(
    ServerLevel world,BlockPos terminal,NetworkRuntime network){
  var pending=new java.util.ArrayDeque<BlockPos>();
  var seen=new java.util.HashSet<Long>();
  var found=new java.util.LinkedHashMap<Long,StorageDriveBlockEntity>();
  pending.add(terminal);
  while(!pending.isEmpty()&&seen.size()<16384&&found.size()<2048){
   BlockPos here=pending.removeFirst();
   if(!world.hasChunkAt(here)||!seen.add(here.asLong()))continue;
   if(!here.equals(terminal)){
    if(!dev.obsidiannetwork.network.NetworkSignalRelayBridge.networkWire(world,here))
     continue;
    NetworkRuntime bound=WorldTopologyBridge.runtimeForAccessory(world,here);
    if(bound!=null&&bound!=network)continue;
   }
   for(net.minecraft.core.Direction face:net.minecraft.core.Direction.values()){
    BlockPos next=here.relative(face);
    if(!world.hasChunkAt(next))continue;
    if(world.getBlockEntity(next) instanceof StorageDriveBlockEntity drive){
     NetworkRuntime attached=WorldTopologyBridge.runtimeForDrive(world,next);
     if(!drive.isRemoved()&&(attached==null||attached==network))
      found.putIfAbsent(next.asLong(),drive);
    }else if(!seen.contains(next.asLong())&&
       dev.obsidiannetwork.network.NetworkSignalRelayBridge.networkWire(world,next))
      pending.add(next);
   }
  }
  return java.util.List.copyOf(found.values());
 }
'''
s=s[:idx]+helper+s[idx:]
save(top,s)

# 4. Static assertions that detect accidental regression of working 1P
# and any reintroduction of the old unbalanced hatch/missing turret ID.
v=load(weapon)
assert "float hatchOpen=" not in v[v.index(" public static void drawArm("):v.index(" @SubscribeEvent public static void worldSuit(")]
assert v.count("nodes.submitModelPart(XSX_WORLD_BARREL,pose")==1
assert "try{" in v[v.index(" public static void drawArm("):v.index(" private static void drawRight(")]
assert "finally{" in v[v.index(" public static void drawArm("):v.index(" private static void drawRight(")]
assert "mc.level.getEntity(xsxId)" in v
assert "stand.getRightArmPose().x()<-40.0F" in v
m=load(menu)
assert "if(slotId>=0&&slotId<8)" in m
assert "broadcastFullState();" in m
assert "DriveMenu.xsxCellTerminalBacking(drive)" in m
assert "backing.setItem(target,one);" in m
assert "carried.shrink(1);" in m
assert "xsxCableDrives(world,terminal,network)" in load(top)
assert "mayPlace(ItemStack item){return false;}" in load(screen)
print("B1019_8_ACTION_SLOTS_REAL_DRIVE_ATOMIC_SYNC_WORLD_BARREL_POSE_BALANCED_TURRET_ENTITY_ID_1P_UNCHANGED_PASS")
