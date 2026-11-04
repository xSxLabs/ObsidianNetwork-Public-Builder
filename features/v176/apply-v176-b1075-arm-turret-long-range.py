#!/usr/bin/env python3
"""B1075: owner-authorized long-range Follow/Turret and arm-parented world Micro-MG.

Runs after B1045/B1041. Never edits Cell Terminal, Drive, inventory, saved
power-armor equipment, first-person gun, FE policy, or projectile implementation.
Fail closed on all source anchor drift.
"""
import os
from pathlib import Path
from PIL import Image, ImageDraw

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
A=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"

def read(rel):
    return (J/rel).read_text(encoding="utf-8")

def put(rel,s):
    (J/rel).write_text(s,encoding="utf-8")

def change(rel,old,new):
    s=read(rel)
    assert s.count(old)==1,("B1075_ANCHOR_DRIFT",rel,s.count(old),old[:100])
    put(rel,s.replace(old,new,1))

def method_section(src,needle):
    a=src.index(needle)
    b=src.index("{",a)
    depth=0
    for p in range(b,len(src)):
        if src[p]=="{":depth+=1
        elif src[p]=="}":
            depth-=1
            if depth==0:return a,p+1,src[a:p+1]
    raise AssertionError(("B1075_METHOD_UNBALANCED",needle))

def patch_method(rel,needle,transform):
    s=read(rel)
    a,b,old=method_section(s,needle)
    new=transform(old)
    assert new!=old,(rel,needle)
    put(rel,s[:a]+new+s[b:])

# RenderPlayerEvent.Post is AFTER the vanilla humanoid render transform has
# been popped. Convert the Post root into the live body-yaw pose ONCE before
# the actual right-arm shoulder pivot; keep the rest of B1041's gun path.
def fix_player(old):
    assert "renderedArm=event.getRenderer().getModel().rightArm" in old
    assert "drawArm(pose,event.getSubmitNodeCollector()" in old
    anchor="  try{\n   pose.translate(0.0F,1.5F,0.0F);"
    assert old.count(anchor)==1,("B1075_PLAYER_POST_ROOT",old[:300])
    return old.replace(anchor,
       "  try{\n   // Post is the unrotated entity root; supply body yaw before arm pivot.\n"
       "   pose.mulPose(com.mojang.math.Axis.YP.rotationDegrees(180.0F-player.yBodyRot));\n"
       "   pose.translate(0.0F,1.5F,0.0F);",1)
patch_method("client/V176MicroMgVisualClient.java",
             " @SubscribeEvent public static void wornFallback(",fix_player)

# ArmorStand Post also lacks its model's body yaw. The id is supplied by the
# existing B1037 registered render-state modifier, not proximity guesses.
def fix_stand(old):
    assert "RIGHT_ARM_PIVOT" in old and "drawArm(post,nodes,light," in old
    anchor="  post.pushPose();\n  try{\n   post.translate(0.0F,1.5F,0.0F);"
    assert old.count(anchor)==1,("B1075_STAND_POST_ROOT",old[:300])
    return old.replace(anchor,
       "  Integer xsxRenderId=state.getRenderData(TURRET_STAND_ID);\n"
       "  Minecraft mc=Minecraft.getInstance();\n"
       "  if(xsxRenderId==null||mc.level==null)return;\n"
       "  Entity xsxEntity=mc.level.getEntity(xsxRenderId);\n"
       "  if(!(xsxEntity instanceof ArmorStand xsxStand)||!xsxStand.isAlive())return;\n"
       "  post.pushPose();\n  try{\n"
       "   post.mulPose(com.mojang.math.Axis.YP.rotationDegrees(180.0F-xsxStand.getYRot()));\n"
       "   post.translate(0.0F,1.5F,0.0F);",1)
patch_method("client/V176MicroMgStandLayer.java",
             " public static void submitFromPost(",fix_stand)
# Imports for the stand render are independent of the current model class.
change("client/V176MicroMgStandLayer.java",
       "import net.minecraft.client.model.EntityModel;",
       "import net.minecraft.client.Minecraft;\n"
       "import net.minecraft.world.entity.Entity;\n"
       "import net.minecraft.world.entity.decoration.ArmorStand;\n"
       "import net.minecraft.client.model.EntityModel;")

# The B1014 standalone 32x32 atlas has violet/blue tint in game. Make the
# entire geometry neutral gunmetal with steel edges, preserving its UV and
# the 1st-person atlas.
gun=A/"textures/entity/micro_mg_world_barrel.png"
assert gun.is_file(),"B1075_MISSING_EXISTING_WORLD_GUN_MATERIAL"
assert Image.open(gun).size==(32,32),"B1075_WORLD_BARREL_ATLAS_DRIFT"
im=Image.new("RGBA",(32,32),(67,74,80,255))
d=ImageDraw.Draw(im)
d.rectangle((0,0,31,4),fill=(151,159,163,255))
d.rectangle((0,5,31,9),fill=(99,106,111,255))
d.rectangle((0,10,31,14),fill=(55,62,68,255))
d.rectangle((0,15,31,20),fill=(116,123,128,255))
d.rectangle((0,21,31,27),fill=(48,53,58,255))
d.line((0,30,31,30),fill=(128,140,145,255),width=1)
im.save(gun,optimize=True)

# The client used to suppress Follow/Turret when the owned suit was outside
# 16 blocks, so a server-side long-range command was impossible via wheel.
# The server still authenticates the durable UUID/owner and Micro-MG module.
client="client/V176CompanionClient.java"
change(client,"  if(suit==null)return null;",
'''  if(suit==null){
   var mc=Minecraft.getInstance();
   if(mc.player==null || PowerArmorRuntime.tier(
         mc.player.getItemBySlot(EquipmentSlot.HEAD),0)!=0)return null;
   return vision?new int[]{0,1,4,6,7,2,3}:new int[]{0,1,6,7,2,3};
  }''')
def follow_client(old):
    return '''public static void toggleFollow(){
  var mc=Minecraft.getInstance();
  if(mc.player!=null&&mc.player.connection!=null)
   mc.player.connection.sendCommand("powerarmor follow");
 }'''
def turret_client(old):
    return '''public static void toggleTurret(){
  var mc=Minecraft.getInstance();
  if(mc.player!=null&&mc.player.connection!=null)
   mc.player.connection.sendCommand("powerarmor turret");
 }'''
patch_method(client," public static void toggleFollow(",follow_client)
patch_method(client," public static void toggleTurret(",turret_client)

helper=J/"powerarmor/V176CompanionLongRange.java"
assert not helper.exists(),"B1075_DUPLICATE_LONG_RANGE_CONTROLLER"
helper.parent.mkdir(parents=True,exist_ok=True)
helper.write_text(r'''package dev.obsidiannetwork.powerarmor;

import java.util.*;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import dev.obsidiannetwork.registry.ModDataComponents;

/** B1075: one real owner-tagged ArmorStand, no cloned equipment and no flight.
 * Reuses v1.7.2 persisted recall index + temporary source chunk tickets.
 * Never touches the existing transactional armor equip/recall sequence.
 */
public final class V176CompanionLongRange {
 private V176CompanionLongRange(){}
 private static final String OWNER="xsxlabs_power_armor_owner_";
 private static final String STAND="xsxlabs_power_armor_suit_v17";
 private static final String FOLLOW="xsxlabs_v176_follow";
 private static final String TURRET="xsxlabs_v176_turret";
 private record Pending(PowerArmorRecallIndex.Location loc,Boolean turret,int ticks){}
 private static final Map<UUID,Pending> WAITING=new HashMap<>();
 private static final Set<UUID> ACTIVE=new HashSet<>();
 private static void syncVisibleTurret(ArmorStand suit){
  var chest=suit.getItemBySlot(EquipmentSlot.CHEST);
  String current=chest.get(ModDataComponents.POWER_ARMOR_UPGRADES.get());
  if(current==null)return;
  var all=new ArrayList<String>(Arrays.asList(current.split(",")));
  all.removeIf("micro_mg_turret_on"::equals);
  if(suit.entityTags().contains(TURRET)&&all.contains("micro_mg"))
   all.add("micro_mg_turret_on");
  chest.set(ModDataComponents.POWER_ARMOR_UPGRADES.get(),String.join(",",all));
  suit.setItemSlot(EquipmentSlot.CHEST,chest.copy());
 }
 private static void notice(ServerPlayer p,String message){
  if(p.connection!=null)p.sendSystemMessage(Component.literal("Power Armor: "+message));
 }
 private static boolean owned(ArmorStand suit,UUID owner){
  return suit!=null&&!suit.isRemoved()&&suit.isAlive()
      &&suit.entityTags().contains(STAND)
      &&suit.entityTags().contains(OWNER+owner)
      &&PowerArmorSuitWorld.full(suit);
 }
 private static boolean module(ArmorStand suit){
  String raw=suit.getItemBySlot(EquipmentSlot.CHEST)
      .get(ModDataComponents.POWER_ARMOR_UPGRADES.get());
  return raw!=null&&Arrays.asList(raw.split(",")).contains("micro_mg");
 }
 private static ServerLevel source(ServerPlayer player,PowerArmorRecallIndex.Location loc){
  try{
   return player.level().getServer().getLevel(
       ResourceKey.create(Registries.DIMENSION,Identifier.parse(loc.dimension())));
  }catch(IllegalArgumentException ex){return null;}
 }
 private static PowerArmorRecallIndex.Location selected(ServerPlayer p){
  var matches=PowerArmorRecallIndex.get(p.level().getServer()).owned(p.getUUID());
  if(matches.size()==1)return matches.get(0);
  if(matches.isEmpty())return null;
  UUID last=PowerArmorRecallPreference.get(p.level().getServer()).preferred(p.getUUID());
  for(var loc:matches)if(loc.suitUUID().equals(last))return loc;
  return null; // Never seize another owned suit on ambiguous recall.
 }
 private static void release(ServerPlayer p,Pending pending){
  ServerLevel src=source(p,pending.loc());
  if(src!=null){
   BlockPos at=BlockPos.containing(
       pending.loc().x(),pending.loc().y(),pending.loc().z());
   PowerArmorRecallTickets.ticket(src,p.getUUID(),
       at.getX()>>4,at.getZ()>>4,false);
  }
  WAITING.remove(p.getUUID());
 }
 private static boolean begin(ServerPlayer p,Boolean turret){
  if(WAITING.containsKey(p.getUUID()))return true;
  var loc=selected(p);
  if(loc==null){notice(p,"kein eindeutig zugeordnetes Ruestungs-Gestell.");return false;}
  ServerLevel src=source(p,loc);
  if(src==null){notice(p,"Ursprungsdimension nicht verfuegbar.");return false;}
  BlockPos at=BlockPos.containing(loc.x(),loc.y(),loc.z());
  boolean ticket=PowerArmorRecallTickets.ticket(src,p.getUUID(),
      at.getX()>>4,at.getZ()>>4,true);
  if(!ticket&&!src.hasChunkAt(at)){
   notice(p,"Ruestungs-Chunk konnte nicht geladen werden.");return false;
  }
  WAITING.put(p.getUUID(),new Pending(loc,turret,0));
  return true;
 }
 /** Called by the original server-authoritative /powerarmor mode toggle. */
 public static int request(ServerPlayer p,boolean turret){
  if(!begin(p,turret))return 0;
  notice(p,"Ruestung aus beliebiger Entfernung angefordert.");
  return 1;
 }
 public static double horizontalSq(ArmorStand stand,ServerPlayer player){
  double dx=stand.getX()-player.getX(),dz=stand.getZ()-player.getZ();
  return dx*dx+dz*dz;
 }
 private static boolean clearSpace(ServerLevel world,ArmorStand suit,BlockPos feet){
  if(!world.hasChunkAt(feet)||!world.hasChunkAt(feet.below()))return false;
  if(!world.getBlockState(feet.below()).isSolid()
      ||!world.getBlockState(feet).isAir()
      ||!world.getBlockState(feet.above()).isAir())return false;
  Vec3 target=Vec3.atBottomCenterOf(feet);
  return world.noCollision(suit,suit.getBoundingBox().move(target.subtract(suit.position())));
 }
 private static Vec3 ground(ServerPlayer p,ArmorStand suit){
  ServerLevel world=(ServerLevel)p.level();
  // Prefer a safe floor near the player's actual Y (important in caves).
  // A flying player has no floor nearby: use the world heightmap below.
  int[][] offsets={{2,0},{-2,0},{0,2},{0,-2},{3,2},{-3,-2},{2,-3},{-2,3}};
  for(int[] offset:offsets){
   int x=p.blockPosition().getX()+offset[0],z=p.blockPosition().getZ()+offset[1];
   BlockPos from=new BlockPos(x,p.blockPosition().getY(),z);
   if(!world.hasChunkAt(from))continue;
   for(int depth=0;depth<96;depth++){
    BlockPos candidate=from.below(depth);
    if(clearSpace(world,suit,candidate))return Vec3.atBottomCenterOf(candidate);
   }
   BlockPos surface=world.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,from);
   if(clearSpace(world,suit,surface))return Vec3.atBottomCenterOf(surface);
  }
  return null; // No mid-air fallback that makes the suit fly.
 }
 /** Moves the SAME ArmorStand; never copies four ItemStacks or their components. */
 public static boolean teleportToGroundNear(ServerPlayer p,ArmorStand suit){
  if(!owned(suit,p.getUUID()))return false;
  Vec3 spot=ground(p,suit);
  if(spot==null)return false;
  suit.setNoGravity(false);
  suit.setDeltaMovement(Vec3.ZERO);
  ServerLevel dest=(ServerLevel)p.level();
  boolean moved;
  if(suit.level()==dest){
   suit.setPos(spot.x,spot.y,spot.z);
   moved=true;
  }else{
   // Standard vanilla dimension move preserves the entity and its equipment.
   moved=suit.teleportTo(dest,spot.x,spot.y,spot.z,
       Set.of(),suit.getYRot(),suit.getXRot(),false);
  }
  if(!moved)return false;
  Entity arrived=dest.getEntity(suit.getUUID());
  if(arrived instanceof ArmorStand actual && owned(actual,p.getUUID())){
   actual.setNoGravity(false);
   actual.setDeltaMovement(new Vec3(0.0D,-0.1D,0.0D));
   PowerArmorRecallIndex.get(dest.getServer()).index(actual,dest,p.getUUID());
  }
  return true;
 }
 public static void onModeEnabled(ServerPlayer p,ArmorStand suit){
  if(!owned(suit,p.getUUID()))return;
  ACTIVE.add(p.getUUID());
  PowerArmorRecallIndex.get(p.level().getServer()).index(suit,
      (ServerLevel)suit.level(),p.getUUID());
  if(!teleportToGroundNear(p,suit))
   notice(p,"kein sicherer Boden zum Teleportieren gefunden.");
 }
 public static void onModeDisabled(ServerPlayer p){
  ACTIVE.remove(p.getUUID());
 }
 /** Runs BEFORE the existing Follow/Turret movement and firing on the same tick. */
 public static void tick(ServerPlayer p){
  UUID owner=p.getUUID();
  ArmorStand nearby=p.level().getEntitiesOfClass(ArmorStand.class,
      p.getBoundingBox().inflate(72.0D),s->owned(s,owner))
       .stream().min(Comparator.comparingDouble(p::distanceToSqr)).orElse(null);
  if(nearby!=null){
   PowerArmorRecallIndex.get(p.level().getServer()).index(nearby,
       (ServerLevel)nearby.level(),owner);
   nearby.setNoGravity(false);
   if(nearby.entityTags().contains(FOLLOW)||nearby.entityTags().contains(TURRET))
    ACTIVE.add(owner);
   else ACTIVE.remove(owner);
  }
  Pending pending=WAITING.get(owner);
  if(pending==null){
   if(nearby!=null||!ACTIVE.contains(owner))return;
   if(!begin(p,null))return;
   pending=WAITING.get(owner);
   if(pending==null)return;
  }
  ServerLevel src=source(p,pending.loc());
  if(src==null){release(p,pending);return;}
  Entity sourceEntity=src.getEntity(pending.loc().suitUUID());
  if(!(sourceEntity instanceof ArmorStand suit)){
   if(pending.ticks()>=160){
    release(p,pending);notice(p,"Ruestung im gespeicherten Chunk nicht gefunden.");
   }else WAITING.put(owner,new Pending(pending.loc(),pending.turret(),pending.ticks()+5));
   return;
  }
  if(!owned(suit,owner)){
   release(p,pending);notice(p,"Besitz- oder Ruestungspruefung fehlgeschlagen.");return;
  }
  if(pending.turret()!=null){
   boolean wantTurret=pending.turret();
   if(wantTurret&&!module(suit)){
    release(p,pending);notice(p,"Micro-MG-Upgrade fehlt.");return;
   }
   String desired=wantTurret?TURRET:FOLLOW;
   boolean already=suit.entityTags().contains(desired);
   suit.removeTag(FOLLOW);suit.removeTag(TURRET);
   if(already){
    syncVisibleTurret(suit);
    ACTIVE.remove(owner); release(p,pending);
    notice(p,(wantTurret?"Turret":"Follow")+" Mode OFF");return;
   }
   suit.addTag(desired);
   syncVisibleTurret(suit);
   ACTIVE.add(owner);
  }else if(!suit.entityTags().contains(FOLLOW)&&!suit.entityTags().contains(TURRET)){
   ACTIVE.remove(owner);release(p,pending);return;
  }
  if(teleportToGroundNear(p,suit)){
   release(p,pending);
   notice(p,"Ruestung am Boden in deiner Naehe.");
  }else if(pending.ticks()>=160){
   release(p,pending);notice(p,"kein sicherer Boden fuer die Ruestung.");
  }else WAITING.put(owner,new Pending(pending.loc(),pending.turret(),pending.ticks()+5));
 }
}
''',encoding="utf-8")

mode="powerarmor/V176CompanionMode.java"
change(mode,"  ArmorStand suit=find(player,20.0D);",
'''  ArmorStand suit=find(player,20.0D);
  if(suit==null)return V176CompanionLongRange.request(player,turret);''')
change(mode,"  if(!was)suit.addTag(requested);",
'''  if(!was){
   suit.addTag(requested);
   V176CompanionLongRange.onModeEnabled(player,suit);
  }else V176CompanionLongRange.onModeDisabled(player);''')
change(mode,
'''  if(!(event.getEntity() instanceof ServerPlayer player))return;''',
'''  if(!(event.getEntity() instanceof ServerPlayer player))return;
  if(player.tickCount%5==0)V176CompanionLongRange.tick(player);''')
change(mode,"   double dist=suit.distanceToSqr(player);",
'''   // Horizontal follow only; never chase a flying owner into mid-air.
   double dist=V176CompanionLongRange.horizontalSq(suit,player);''')
# Keep original safe short-distance horizontal movement, but the >14 block
# correction MUST also land on solid ground instead of player's flight Y.
s=read(mode)
start=s.index("  if(dist>14D*14D){")
end=s.index("  }else if(dist>3.5D*3.5D){",start)
assert "suit.setPos(spot.x,spot.y,spot.z);" in s[start:end],"B1075_OLD_FLOATING_RECALL_DRIFT"
s=s[:start]+'''  if(dist>14D*14D){
   V176CompanionLongRange.teleportToGroundNear(player,suit);
'''+s[end:]
put(mode,s)
change(mode,
'''  if(!turret)return;
  ItemStack chest=suit.getItemBySlot(EquipmentSlot.CHEST);''',
'''  if(!turret)return;
  // FOLLOW has priority while the owner is moving or the suit is catching up.
  if(player.getDeltaMovement().lengthSqr()>0.0025D
     ||V176CompanionLongRange.horizontalSq(suit,player)>3.5D*3.5D)return;
  ItemStack chest=suit.getItemBySlot(EquipmentSlot.CHEST);''')
s=read(mode)
assert "V176MicroMgRules.canTurretFire" in s
assert "suit.setYBodyRot(xsxYaw)" in s
assert "V176CompanionLongRange.tick(player)" in s
assert 'if(player.tickCount%5==0)V176CompanionLongRange.tick(player);' in s
assert 'syncVisibleTurret(suit);' in helper.read_text(encoding='utf-8')
assert "PowerArmorRecallTickets.ticket" in helper.read_text(encoding="utf-8")
assert "PowerArmorRecallIndex.get(" in helper.read_text(encoding="utf-8")
assert "setNoGravity(false)" in helper.read_text(encoding="utf-8")
assert "teleportToGroundNear(player,suit)" in s
assert "V176CompanionLongRange.request(player,turret)" in s
assert "pose.mulPose(com.mojang.math.Axis.YP.rotationDegrees(180.0F-player.yBodyRot))" in read("client/V176MicroMgVisualClient.java")
assert "xsxStand.getYRot()" in read("client/V176MicroMgStandLayer.java")
print("B1075_ARMPARENT_BODY_YAW_TURRET_FOLLOW_REMOTE_OWNED_GROUND_ONLY_NO_CELL_MODS_PASS")
