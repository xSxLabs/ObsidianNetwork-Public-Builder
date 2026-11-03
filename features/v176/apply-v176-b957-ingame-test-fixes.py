#!/usr/bin/env python3
"""B957 v1.7.6 Ingame test findings: authoritative visual and control fixes.
Applied after B937. No modification of real equipment ownership or recipes.
"""
import os,re,json
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"

def edit(path,old,new):
 p=J/path;s=p.read_text(encoding="utf-8")
 n=s.count(old)
 assert n==1,("B957_SOURCE_DRIFT",path,n,old[:75])
 p.write_text(s.replace(old,new,1),encoding="utf-8")

def add(path,code):
 p=J/path
 assert not p.exists(),("B957_DUPLICATE",path)
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(code,encoding="utf-8")

# Reuse the established Network Storage identifier, instead of the old
# Power Armor-specific category. All other Power Armor, Recall and Backpack
# bindings already reference PowerArmorExitKeyClient.CATEGORY.
power_keys=J/"powerarmor/PowerArmorExitKeyClient.java"
power_src=power_keys.read_text(encoding="utf-8")
power_src,count=re.subn(
 r'Identifier\.fromNamespaceAndPath\(\s*"obsidiannetwork"\s*,\s*"xsxlabs"\s*\)',
 'Identifier.fromNamespaceAndPath("obsidiannetwork","network_storage")',
 power_src)
assert count==1,("B957_CATEGORY_ANCHOR_DRIFT",count)
power_keys.write_text(power_src,encoding="utf-8")
# One shared category, already used by Power Armor and Network Backpack.
keys="client/V176CreativeFlightParticles.java"
edit(keys,"  KeyMapping.Category.MISC);",
 "  dev.obsidiannetwork.powerarmor.PowerArmorExitKeyClient.CATEGORY);")
edit(keys,'enabled?"Creative Flight-Partikel AN":"Creative Flight-Partikel AUS"',
 'enabled?"Creative Flight Particles: ON":"Creative Flight Particles: OFF"')
edit(keys,
 '   enabled=!enabled;\n   Minecraft mc=Minecraft.getInstance();',
 '''   enabled=!enabled;
   Minecraft mc=Minecraft.getInstance();
   if(mc.player!=null && mc.player.connection!=null)
    mc.player.connection.sendCommand("powerarmor flightparticles");''')

# Unlike the B937 CLIENT emitter, creative hover jets are ALSO spawned by
# PowerArmorCreativeFlightJets on the SERVER, and must be disabled there.
add("powerarmor/V176CreativeFlightParticlesServer.java",'''package dev.obsidiannetwork.powerarmor;
import net.minecraft.server.level.ServerPlayer;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
/** Player-owned particle preference only; flight, FE and Elytra untouched. */
public final class V176CreativeFlightParticlesServer {
 private V176CreativeFlightParticlesServer(){}
 private static final Map<UUID,Boolean> VISIBLE=new HashMap<>();
 public static boolean enabled(ServerPlayer player){
  return VISIBLE.getOrDefault(player.getUUID(),true);
 }
 public static int toggle(ServerPlayer player){
  VISIBLE.put(player.getUUID(),!enabled(player));
  return 1;
 }
}''')
cmd="powerarmor/PowerArmorCommands.java"
edit(cmd,
 '   .then(Commands.literal("sleep").executes(c->V176PowerSleepServer.toggle(c.getSource().getPlayerOrException()))));',
 '''   .then(Commands.literal("sleep").executes(c->V176PowerSleepServer.toggle(c.getSource().getPlayerOrException())))
   .then(Commands.literal("flightparticles").executes(c->V176CreativeFlightParticlesServer.toggle(c.getSource().getPlayerOrException()))));''')
jets=J/"powerarmor/PowerArmorCreativeFlightJets.java"
src=jets.read_text(encoding="utf-8")
m=re.search(r'public static void onPlayerTick\([^{]+\)\s*\{',src)
assert m, "B957_SERVER_JETS_METHOD_MISSING"
src=src[:m.end()]+'''
  // This is the actual server-synced Creative Flight emitter. Honor hotkey.
  if(event.getEntity() instanceof net.minecraft.server.level.ServerPlayer xsxPlayer
     && !V176CreativeFlightParticlesServer.enabled(xsxPlayer))return;
'''+src[m.end():]
jets.write_text(src,encoding="utf-8")

# The 1P arm was translated to the left without actually changing its Y yaw.
# Apply matched yaw to the real arm and single weapon submission, Attack only.
gun="client/V176MicroMgVisualClient.java"
edit(gun,
 "  pose.mulPose(com.mojang.math.Axis.XP.rotationDegrees(-78.0F));",
 """  pose.mulPose(com.mojang.math.Axis.XP.rotationDegrees(-78.0F));
  pose.mulPose(com.mojang.math.Axis.YP.rotationDegrees(32.0F));""")
edit(gun,
 "  pose.translate(0.43F,-0.30F,-0.53F);",
 """  pose.translate(0.43F,-0.30F,-0.53F);
  pose.mulPose(com.mojang.math.Axis.YP.rotationDegrees(32.0F));""")
p=J/gun;s=p.read_text(encoding="utf-8")
# Black detached HATCH quad is unacceptable even during transitions. Keep
# arm/barrel and its slide timing, but never submit this floating plate.
pattern=r'(?m)^[ \t]*(?:nodes|event\.getSubmitNodeCollector\(\))\.submitModelPart\(HATCH,pose,[\s\S]*?OverlayTexture\.NO_OVERLAY,null,false,false,0xFFFFFFFF,null,0\);'
s,count=re.subn(pattern,"\n   // B957: detached hatch plate deliberately not rendered.",s)
assert 1<=count<=3,("B957_FLOATING_HATCH_NOT_FOUND",count)
# The turret server uses ENTITY TAG xsxlabs_v176_turret. Old renderer only
# tested a non-synced legacy CHEST upgrade and therefore hid the barrel.
start=s.index(" @SubscribeEvent public static void worldSuit(")
suffix=s[start:]
old='has(chest,"micro_mg_turret_on")'
assert suffix.count(old)==1,("B957_TURRET_RENDER_GATE_DRIFT",suffix.count(old))
suffix=suffix.replace(old,'stand.entityTags().contains("xsxlabs_v176_turret")',1)
s=s[:start]+suffix
p.write_text(s,encoding="utf-8")

# Camera ray determines the real impact aim. Bullet still starts at the real
# muzzle, is NOT hitscan, and is NOT guided after launch. Zero random spread.
fire="powerarmor/V176MicroMgFire.java"
edit(fire,
 '  shot.shoot(dir.x,dir.y,dir.z,3.0F,0.8F);',
 '''   Vec3 eye=p.getEyePosition();
   Vec3 far=eye.add(dir.scale(128.0D));
   var hit=world.clip(new net.minecraft.world.level.ClipContext(eye,far,
        net.minecraft.world.level.ClipContext.Block.COLLIDER,
        net.minecraft.world.level.ClipContext.Fluid.NONE,p));
   Vec3 target=hit.getType()==net.minecraft.world.phys.HitResult.Type.MISS
       ?far:hit.getLocation();
   Vec3 corrected=target.subtract(origin).normalize();
   if(corrected.lengthSqr()<0.000001D)corrected=dir;
   shot.shoot(corrected.x,corrected.y,corrected.z,3.0F,0.0F);''')
# Do not add random turret spread.
turret="powerarmor/V176CompanionMode.java"
p=J/turret
src=p.read_text(encoding="utf-8")
src,count=re.subn(
 r'(?m)^([ \t]*)shot\.shoot\(dir\.x,dir\.y,dir\.z,3\.0F,0\.7F\);',
 lambda m:m.group(1)+"shot.shoot(dir.x,dir.y,dir.z,3.0F,0.0F);",src)
assert count==1,("B957_TURRET_SPREAD_DRIFT",count)
p.write_text(src,encoding="utf-8")

# Stable 200-tick black surface impact marks, synced to nearby players.
# Cap per dimension and throttle particle refresh to limit the server cost.
add("powerarmor/V176MicroMgImpactMarks.java",'''package dev.obsidiannetwork.powerarmor;
import java.util.ArrayDeque;
import java.util.Map;
import java.util.WeakHashMap;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.BlockHitResult;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;
@EventBusSubscriber(modid="obsidiannetwork")
public final class V176MicroMgImpactMarks {
 private V176MicroMgImpactMarks(){}
 private record Mark(double x,double y,double z,long until){}
 private static final Map<ServerLevel,ArrayDeque<Mark>> MARKS=new WeakHashMap<>();
 private static final Map<ServerLevel,Long> LAST=new WeakHashMap<>();
 private static final int MAX=96;
 public static void hit(ServerLevel level,BlockHitResult hit){
  var face=hit.getDirection();
  var p=hit.getLocation();
  double x=p.x+face.getStepX()*0.014D;
  double y=p.y+face.getStepY()*0.014D;
  double z=p.z+face.getStepZ()*0.014D;
  var marks=MARKS.computeIfAbsent(level,k->new ArrayDeque<>());
  if(marks.size()>=MAX)marks.removeFirst();
  marks.addLast(new Mark(x,y,z,level.getGameTime()+200L));
 }
 @SubscribeEvent public static void tick(PlayerTickEvent.Post event){
  if(!(event.getEntity() instanceof ServerPlayer p))return;
  ServerLevel level=p.level();
  long time=level.getGameTime();
  if(time%5!=0||LAST.getOrDefault(level,-1L)==time)return;
  LAST.put(level,time);
  var marks=MARKS.get(level);
  if(marks==null||marks.isEmpty())return;
  marks.removeIf(m->m.until()<=time);
  var particle=new DustParticleOptions(0x101010,0.25F);
  for(var mark:marks)
   level.sendParticles(particle,mark.x(),mark.y(),mark.z(),1,0,0,0,0);
 }
}''')
projectile="powerarmor/V176MicroMgProjectile.java"
p=J/projectile;s=p.read_text(encoding="utf-8")
m=re.search(r'@Override\s+protected void onHitBlock\(BlockHitResult hit\)\s*\{',s)
assert m, "B957_IMPACT_EVENT_NOT_FOUND"
s=s[:m.end()]+'''
  if(level() instanceof ServerLevel impactWorld)
   V176MicroMgImpactMarks.hit(impactWorld,hit);
'''+s[m.end():]
p.write_text(s,encoding="utf-8")

# Render worn bags at the player's shoulder/back, not -0.69 below the feet.
# This is common to chest equipment and Curios, so both receive the fix.
worn="client/V176BackpackWornRenderer.java"
edit(worn,
 'pose.translate(0.0F,event.getRenderState().isCrouching?-.51F:-.69F,.29F);',
 'pose.translate(0.0F,event.getRenderState().isCrouching?1.04F:1.35F,.29F);')

# Shift-left click + drag: one server-verified max natural stack per unique
# list entry per gesture. Existing shiftWithdraw already limits 1/16/64 and
# checks inventory space before committing. Never send a second request to a
# previously visited entry during the same drag.
screen="client/V176BackpackScreen.java"
p=J/screen;s=p.read_text(encoding="utf-8")
anchor=" public V176BackpackScreen("
assert s.count(anchor)==1
s=s.replace(anchor,''' private final java.util.Set<Integer> xsxShiftVisited=new java.util.HashSet<>();
'''+anchor,1)
needle="  double mx=event.x(),my=event.y(); int button=event.button();"
assert s.count(needle)==1
s=s.replace(needle,needle+'''
  if(!event.hasShiftDown() || button!=0)xsxShiftVisited.clear();
  else {
   int gx=(int)mx-getLeftPos(),gy=(int)my-getTopPos();
   if(gx>=8&&gx<170&&gy>=38&&gy<128){
    int id=4+((gy-38)/18)*9+(gx-8)/18;
    if(id>=4&&id<49)xsxShiftVisited.add(id);
   }
  }''',1)
# Screen receives drag events with MouseButtonEvent (same 26.1 API as click).
insert=''' @Override public boolean mouseDragged(
   net.minecraft.client.input.MouseButtonEvent event,double dx,double dy){
  if(event.button()==0&&event.hasShiftDown()&&!filterEditor){
   int gx=(int)event.x()-getLeftPos(),gy=(int)event.y()-getTopPos();
   if(gx>=8&&gx<170&&gy>=38&&gy<128){
    int col=(gx-8)/18,row=(gy-38)/18;
    if(col<9&&row<5){
     int id=4+row*9+col;
     var game=net.minecraft.client.Minecraft.getInstance();
     if(!menu.getSlot(id).getItem().isEmpty()
         &&xsxShiftVisited.add(id)&&game.player!=null&&game.gameMode!=null)
      game.gameMode.handleContainerInput(menu.containerId,id,0,
        net.minecraft.world.inventory.ContainerInput.QUICK_MOVE,game.player);
     return true;
    }
   }
  }
  return super.mouseDragged(event,dx,dy);
 }
 @Override public boolean mouseReleased(net.minecraft.client.input.MouseButtonEvent event){
  xsxShiftVisited.clear();
  return super.mouseReleased(event);
 }
'''
anchor=' @Override public boolean mouseScrolled('
assert s.count(anchor)==1
s=s.replace(anchor,insert+anchor,1)
p.write_text(s,encoding="utf-8")

# Adaptive Recall pursuit: predict the player and always exceed their current
# movement speed. Fall triggers a fast catch-up, while docking stays unchanged.
recall=J/"powerarmor/PowerArmorRecall.java"
s=recall.read_text(encoding="utf-8")
match=re.search(r'Math\.min\(\s*SPEED\s*,\s*distance\s*-\s*2(?:\.0)?D?\s*\)',s)
assert match is not None, "B957_RECALL_SPEED_FORMULA_MISSING"
s=s[:match.start()]+'Math.min(V176RecallChaseSpeed.speed(player,visual,distance),Math.max(0D,distance-2D))'+s[match.end():]
# Replace destination prediction in flight only; preserve arrival and docking.
old='Vec3 delta=player.position().subtract(visual.position());'
assert s.count(old)==1,("B957_RECALL_TARGET_ANCHOR",s.count(old))
s=s.replace(old,'''Vec3 delta=V176RecallChaseSpeed.predict(player,visual).subtract(visual.position());''',1)
recall.write_text(s,encoding="utf-8")
add("powerarmor/V176RecallChaseSpeed.java",'''package dev.obsidiannetwork.powerarmor;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;
public final class V176RecallChaseSpeed {
 private V176RecallChaseSpeed(){}
 public static Vec3 predict(ServerPlayer player,PowerArmorVisualEntity suit){
  double distance=player.position().distanceTo(suit.position());
  double lead=Math.min(5.0D,distance/6.0D);
  return player.position().add(player.getDeltaMovement().scale(lead));
 }
 public static double speed(ServerPlayer player,PowerArmorVisualEntity suit,double distance){
  double playerSpeed=player.getDeltaMovement().length();
  double base=Math.max(1.10D,playerSpeed*1.60D+0.55D);
  if(player.getDeltaMovement().y<-.35D && !player.onGround())
   base=Math.max(base,Math.min(10.0D,distance*.55D+1.5D));
  return Math.min(12.0D,Math.max(base,distance/38.0D));
 }
}''')

assert "Creative Flight Particles: OFF" in (J/keys).read_text()
assert 'stand.entityTags().contains("xsxlabs_v176_turret")' in (J/gun).read_text()
assert "mouseDragged(" in (J/screen).read_text()
assert "V176RecallChaseSpeed.speed" in recall.read_text()
print("B957_CREATIVE_SERVER_OFF_ENGLISH_KEYS_ARM_YAW_NO_HATCH_TURRET_CROSSHAIR_IMPACTS_BACKPACK_DRAG_WORN_RECALL_PASS")
