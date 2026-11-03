#!/usr/bin/env python3
"""B1037: act on B1034 persistent invisible 3P/turret + Cell Terminal failures.
Applied strictly AFTER B1035 on Minecraft/NeoForge 26.1.
- Native RenderLayer already receives model-space PoseStack. Do not apply
  SECOND world->model transform (would shift/flip 3P barrel).
- Turret's server authority is ArmorStand scoreboard tag, not an optional
  chest NBT token. Replicate that tag into a vanilla render-state modifier.
- Ensure both server-side action pad and shift-click can accept real Cells,
  and fake players can exercise their exact transfer route in GameTests.
"""
import os
from pathlib import Path
ROOT=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def read(p): return (ROOT/p).read_text(encoding="utf-8")
def save(p,s): (ROOT/p).write_text(s,encoding="utf-8")
def replace(rel,old,new):
 src=read(rel); n=src.count(old)
 assert n==1,("B1037_SOURCE_DRIFT",rel,n,old[:110])
 save(rel,src.replace(old,new,1))

# The model-space pose and body yaw are ALREADY applied at RenderLayer.submit;
# adding a second 1.5-block translation and -1 scale is not valid.
p="client/V176MicroMgLayer.java"
replace(p,
"""  xsxWeaponPose.mulPose(new org.joml.Matrix4f(pose.last().pose()));
  xsxWeaponPose.translate(0.0F,1.5F,0.0F);
  xsxWeaponPose.scale(-1.0F,-1.0F,1.0F);
  V176MicroMgVisualClient.drawArm""",
"""  xsxWeaponPose.mulPose(new org.joml.Matrix4f(pose.last().pose()));
  // Model-space: no extra world-frame conversion. Body yaw is inherited.
  V176MicroMgVisualClient.drawArm""")
# Never silently reject a clearly armed player due to 26.1 transition state.
replace(p,
"""  if(deployment<=0.001F)return;
  // The RenderLayer pose already includes actual body yaw""",
"""  if(deployment<=0.001F)return;
  if(attack&&LOGGED_PLAYERS.add(state.id))
   System.out.println("XSXLABS_B1037_PLAYER_MG_SUBMIT id="+state.id+
     " tier="+equippedTier+" active="+attack);
  // The RenderLayer pose already includes actual body yaw""")
replace(p,
""" @Override public void submit(PoseStack pose,SubmitNodeCollector nodes,int light,""",
""" private static final java.util.Set<Integer> LOGGED_PLAYERS=
    java.util.concurrent.ConcurrentHashMap.newKeySet();
 @Override public void submit(PoseStack pose,SubmitNodeCollector nodes,int light,""")

p="client/V176MicroMgStandLayer.java"
replace(p,
"""  gunPose.mulPose(new org.joml.Matrix4f(pose.last().pose()));
  gunPose.translate(0.0F,1.5F,0.0F);
  gunPose.scale(-1.0F,-1.0F,1.0F);
  RIGHT_ARM_PIVOT.xRot=""",
"""  gunPose.mulPose(new org.joml.Matrix4f(pose.last().pose()));
  // Native ArmorStandRenderer layers are already in the rotated model frame.
  RIGHT_ARM_PIVOT.xRot=""")
# The companion toggles xsxlabs_v176_turret on the ArmorStand, but it does NOT
# set micro_mg_turret_on in the armor ItemStack. Capture this exact server-synced
# tag while the renderer extracts the entity state.
replace(p,
""" public final class V176MicroMgStandLayer
    extends RenderLayer<ArmorStandRenderState,EntityModel<ArmorStandRenderState>> {
 private static final ModelPart RIGHT_ARM_PIVOT""",
""" public final class V176MicroMgStandLayer
    extends RenderLayer<ArmorStandRenderState,EntityModel<ArmorStandRenderState>> {
 private static final net.minecraft.util.context.ContextKey<Boolean> TURRET_ACTIVE=
    new net.minecraft.util.context.ContextKey<>(
      net.minecraft.resources.Identifier.fromNamespaceAndPath(
       "obsidiannetwork","v176_turret_tag_active"));
 private static final java.util.Set<Integer> LOGGED_STANDS=
    java.util.concurrent.ConcurrentHashMap.newKeySet();
 private static final ModelPart RIGHT_ARM_PIVOT""")
replace(p,
"""  boolean active=has(state.chestEquipment,"micro_mg_turret_on")
       ||has(state.chestEquipment,"micro_mg_on")
       ||state.rightArmPose.x()<-35.0F;
  if(!active)return;""",
"""  boolean active=Boolean.TRUE.equals(state.getRenderData(TURRET_ACTIVE))
       ||has(state.chestEquipment,"micro_mg_turret_on")
       ||state.rightArmPose.x()<-35.0F;
  if(!active)return;
  if(LOGGED_STANDS.add(state.id))
   System.out.println("XSXLABS_B1037_STAND_MG_SUBMIT id="+state.id+
       " tier="+variant+" arm="+state.rightArmPose.x());""")
replace(p,
"""  @SubscribeEvent public static void layers(EntityRenderersEvent.AddLayers event){""",
"""  @SubscribeEvent public static void captureTurretTag(
      net.neoforged.neoforge.client.renderstate.RegisterRenderStateModifiersEvent event){
   event.registerEntityModifier(ArmorStandRenderer.class,
       (stand,state)->state.setRenderData(TURRET_ACTIVE,
          stand.entityTags().contains("xsxlabs_v176_turret")));
   System.out.println("XSXLABS_B1037_STAND_TURRET_STATE_REGISTERED");
  }
  @SubscribeEvent public static void layers(EntityRenderersEvent.AddLayers event){""")

# The terminal click path is intended to be testable by a real ServerPlayer or
# FakePlayer; fake player has no network connection to send the ActionBar.
# A null connection is not a reason to roll back an otherwise valid cell.
p="cellterminal/V176CellTerminalMenu.java"
m=read(p)
count=m.count("server.connection.send(")
assert 2<=count<=5,("B1037_CELL_UI_NOTIFY_DRIFT",count)
m=m.replace("server.connection.send(","if(server.connection!=null)server.connection.send(")
# Equipment Cell is also supported by the real drive backing, including
# Shift-click from the player's inventory (not just cursor pad).
old="if(carried.isEmpty()||!(carried.getItem() instanceof StorageCellItem))"
assert m.count(old)==1,("B1037_SHIFT_CELL_TYPE_DRIFT",m.count(old))
m=m.replace(old,"""if(carried.isEmpty()||!(carried.getItem() instanceof StorageCellItem
     ||carried.getItem() instanceof dev.obsidiannetwork.item.EquipmentCellItem))""",1)
for guard in ("backing.setItem(target,one);","carried.shrink(1);",
              "if(slotId>=0&&slotId<8)","DriveMenu.xsxCellTerminalBacking"):
 assert guard in m,("B1037_CELL_SERVER_TRANSFER_MISSING",guard)
save(p,m)
# Do NOT edit the skin mixin, first-person renderer, drive inventory or
# weapon FE policy.
assert "TURRET_ACTIVE" in read("client/V176MicroMgStandLayer.java")
assert "state.rightArmPose.x()" in read("client/V176MicroMgStandLayer.java")
assert "V176MicroMgVisualClient.drawArm(xsxWeaponPose" in read("client/V176MicroMgLayer.java")
assert "XSXLABS_B1032_CELL_INPUT" in read("cellterminal/V176CellTerminalMenu.java")
print("B1037_NATIVE_LAYER_MODEL_SPACE_SERVER_TURRET_TAG_REAL_CELL_TYPE_SAFE_ACTION_PASS")
