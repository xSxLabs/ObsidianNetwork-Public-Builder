#!/usr/bin/env python3
"""B757: 756 ingame feedback: right-arm aim, hatch/barrel both camera modes,
turret body direction, 16 rounds/sec, glass and ice hits, smaller particles.
Apply AFTER B750; preserve all real suit inventory and recall owners.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"

def edit(rel,old,new):
 p=J/rel
 s=p.read_text(encoding="utf-8")
 assert s.count(old)==1,("V176_B757_DRIFT",rel,s.count(old),old[:140])
 p.write_text(s.replace(old,new,1),encoding="utf-8")

# Client requests at most one physical round/tick; server enforces the
# four-of-five-tick beat (16/sec) plus 3000FE/round and real projectile.
edit("client/V176MicroMgFireClient.java",
'''  if(!first&&tick%5L!=0L&&tick%5L!=2L)return; // doubled 2/3 tick beat
  if(next>=0L && tick<next)return;
  next=tick+2L;''',
'''  // Let the SERVER decide the 4/5-tick shot schedule.
  if(next>=0L && tick<next)return;
  next=tick+1L;''')
edit("client/V176MicroMgFireClient.java",
''' private static int cooldown(){return 2;}''',
''' private static int cooldown(){return 1;}''')

# Attacking by glass/ice intentionally consumes a REAL shot and its FE.
# Only specific vanilla glass and ice, never arbitrary blocks/containers.
# Drop=false prevents 16/sec free glass/ice item farming.
edit("powerarmor/V176MicroMgProjectile.java",
'''import net.minecraft.server.level.ServerLevel;''',
'''import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.core.registries.BuiltInRegistries;''')
edit("powerarmor/V176MicroMgProjectile.java",
'''  if(level() instanceof ServerLevel server){
   server.sendParticles(ParticleTypes.CRIT,hit.getLocation().x,
      hit.getLocation().y,hit.getLocation().z,3,0.035,0.035,0.035,0.03);
   discard();
  }
 }
 @Override public void tick(){''',
'''  if(level() instanceof ServerLevel server){
   var position=hit.getBlockPos();
   var state=server.getBlockState(position);
   String blockId=BuiltInRegistries.BLOCK.getKey(state.getBlock()).getPath();
   boolean glass=blockId.equals("glass")||blockId.equals("glass_pane")
       ||blockId.equals("tinted_glass")||blockId.endsWith("_stained_glass")
       ||blockId.endsWith("_stained_glass_pane");
   boolean ice=blockId.equals("ice")||blockId.equals("packed_ice")
       ||blockId.equals("blue_ice")||blockId.equals("frosted_ice");
   // Respect base server permissions and world border; no container damage.
   if((glass||ice)&&getOwner() instanceof ServerPlayer shooter
      &&server.getWorldBorder().isWithinBounds(position)
      &&shooter.mayInteract(server,position))
    server.destroyBlock(position,false,shooter);
   server.sendParticles(ParticleTypes.CRIT,hit.getLocation().x,
      hit.getLocation().y,hit.getLocation().z,2,0.025,0.025,0.025,0.015);
   discard();
  }
 }
 @Override public void tick(){''')
# White END_ROD squares in 756 obscure boots and weapon silhouette.
edit("powerarmor/V176MicroMgProjectile.java",
'''level().addParticle(ParticleTypes.END_ROD,getX(),getY(),getZ(),0,0,0);''',
'''level().addParticle(ParticleTypes.CRIT,getX(),getY(),getZ(),0,0,0);''')
edit("powerarmor/V176MicroMgFire.java",
'''world.sendParticles(ParticleTypes.END_ROD,origin.x,origin.y,origin.z,
     2,0.035,0.035,0.035,0.015);''',
'''world.sendParticles(ParticleTypes.CRIT,origin.x,origin.y,origin.z,
     1,0.012,0.012,0.012,0.005);''')
edit("powerarmor/V176CompanionMode.java",
'''world.sendParticles(ParticleTypes.END_ROD,muzzle.x,muzzle.y,muzzle.z,
     2,0.05,0.05,0.05,0.02);''',
'''world.sendParticles(ParticleTypes.CRIT,muzzle.x,muzzle.y,muzzle.z,
     1,0.012,0.012,0.012,0.005);''')

# Any real movement changes the WHOLE stand orientation, not only position.
edit("powerarmor/V176CompanionMode.java",
'''  if(player.tickCount%5==0){ // preserve original companion movement cadence
  double dist=suit.distanceToSqr(player);''',
'''  if(player.tickCount%5==0){ // preserve original companion movement cadence
  Vec3 beforeMove=suit.position();
  double dist=suit.distanceToSqr(player);''')
edit("powerarmor/V176CompanionMode.java",
'''  }
  // Keep limb movement separate from the five-tick position update.''',
'''  Vec3 travelled=suit.position().subtract(beforeMove);
  if(travelled.horizontalDistanceSqr()>0.0004D){
   float yaw=(float)Math.toDegrees(Math.atan2(-travelled.x,travelled.z));
   suit.setYRot(yaw);
   suit.setYBodyRot(yaw);
   suit.setYHeadRot(yaw);
  }
  }
  // Keep limb movement separate from the five-tick position update.''')

# Pre event fires before setupAnim, so manipulating model.rightArm there gets
# reset. Set the actual player render-state ArmPose instead, then attach a gun
# in Post without drawing a duplicate arm (which creates phantom limb/leg noise).
edit("client/V176MicroMgVisualClient.java",
'''  var arm=event.getRenderer().getModel().rightArm;
  float raised=phase(extend,0.0F,4.0F/12.0F);''',
'''  // Changes the actual animated PLAYER/ARMOR model at setupAnim, not a
  // temporary model-part rotation that the renderer immediately overwrites.
  event.getRenderState().rightArmPose=HumanoidModel.ArmPose.BLOCK;
  var arm=event.getRenderer().getModel().rightArm;
  float raised=phase(extend,0.0F,4.0F/12.0F);''')
edit("client/V176MicroMgVisualClient.java",
'''   if(raised>0.01F)
    event.getSubmitNodeCollector().submitModelPart(model.rightArm,
       event.getPoseStack(),RenderTypes.entitySolid(wornArmorTexture(tier)),
       event.getRenderState().lightCoords,OverlayTexture.NO_OVERLAY,
       null,false,false,0xFFFFFFFF,null,0);
   drawArm(event.getPoseStack(),event.getSubmitNodeCollector(),''',
'''   // Do NOT submit a second whole arm: the existing armor arm is posed via
   // rightArmPose; submitting it again caused overlapping moving geometry.
   drawArm(event.getPoseStack(),event.getSubmitNodeCollector(),''')

# World stand pose is already network-watched. Use it as fallback for Turret
# activation when the owner chest token arrives a client tick later.
edit("client/V176MicroMgVisualClient.java",
'''boolean armed=has(chest,"micro_mg")&&has(chest,"micro_mg_turret_on");''',
'''boolean armed=has(chest,"micro_mg")&&
      (has(chest,"micro_mg_turret_on")||stand.getRightArmPose().x()<-45F);''')
edit("client/V176MicroMgVisualClient.java",
'''var box=new AABB(state.x-0.20,state.y-0.20,state.z-0.20,
                    state.x+0.20,state.y+0.20,state.z+0.20);''',
'''// An ArmorStand changes position in discrete 5-tick steps: renderer state
  // interpolates between updates. Do not require a .15-block match.
  var box=new AABB(state.x-0.90,state.y-0.30,state.z-0.90,
                    state.x+0.90,state.y+0.30,state.z+0.90);''')
edit("client/V176MicroMgVisualClient.java",
'''if(Math.abs(stand.getX()-state.x)>.15||Math.abs(stand.getZ()-state.z)>.15)continue;''',
'''if(Math.abs(stand.getX()-state.x)>.85||Math.abs(stand.getZ()-state.z)>.85)continue;''')

# Show upper arm hatch from the first tick, angle it open over the FIRST
# person sleeve and then extend the barrel. Do not skip a held item hand.
edit("client/V176MicroMgVisualClient.java",
'''  // First-person weapon sits higher, at the shoulder/upper arm, not the wrist.
  pose.translate(0.14F,-0.18F,-0.08F);''',
'''  // Directly over the upper-right sleeve in camera hand coordinates.
  pose.translate(0.18F,-0.16F,-0.38F);''')
edit("client/V176MicroMgVisualClient.java",
'''  if(hatchOpen>0.001F){
   pose.pushPose();
   pose.mulPose(com.mojang.math.Axis.XP.rotationDegrees(-16.0F*hatchOpen));''',
'''  if(progress>0.001F){
   pose.pushPose();
   pose.mulPose(com.mojang.math.Axis.XP.rotationDegrees(-16.0F*hatchOpen));''')
edit("client/V176MicroMgVisualClient.java",
'''  if(hatch>0F){
   pose.pushPose();
   pose.mulPose(com.mojang.math.Axis.XP.rotationDegrees(-16F*hatch));''',
'''  if(amount>0F){
   pose.pushPose();
   pose.mulPose(com.mojang.math.Axis.XP.rotationDegrees(-16F*hatch));''')
# World/player hatch visible when still closed while shoulder starts raising.
edit("client/V176MicroMgVisualClient.java",
'''  if(hatchOpen>0.001F){
   pose.pushPose();
   pose.translate(0.0F,3.1F/16.0F,-2.25F/16.0F);''',
'''  if(extension>0.001F){
   pose.pushPose();
   pose.translate(0.0F,3.1F/16.0F,-2.25F/16.0F);''')

# Turret muzzle is actually on the RIGHT upper arm, not at the left/wrist.
edit("powerarmor/V176MicroMgFire.java",
'''Vec3 origin=p.getEyePosition().add(dir.scale(0.50D))
             .add(right.scale(0.34D)).add(0,-0.19D,0);''',
'''Vec3 origin=p.getEyePosition().add(dir.scale(0.38D))
             .add(right.scale(0.34D)).add(0,-0.21D,0);''')
edit("powerarmor/V176CompanionMode.java",
'''Vec3 muzzle=start.add(right.scale(0.34D)).add(0,0.02D,0);''',
'''Vec3 muzzle=start.add(right.scale(0.34D)).add(0,0.08D,0);''')

# This is not a generic rifle board: the other power armor upgrade cards
# use the nether-star base icon. Keep it visible with a small micro-MG emblem.
import json
from PIL import Image,ImageDraw
model=R/"models/item/power_card_micro_mg.json"
info=json.loads(model.read_text(encoding="utf-8"))
assert info["textures"]["layer0"]=="obsidiannetwork:item/power_card_micro_mg"
info["textures"]={"layer0":"minecraft:item/nether_star",
                  "layer1":"obsidiannetwork:item/power_card_micro_mg"}
model.write_text(json.dumps(info,indent=2)+"\n",encoding="utf-8")
icon=R/"textures/item/power_card_micro_mg.png"
assert icon.is_file()
im=Image.new("RGBA",(32,32),(0,0,0,0))
d=ImageDraw.Draw(im)
# Small metal-blue panel inset over the star; single right-hand mini barrel.
d.rounded_rectangle((11,12,25,24),radius=2,fill=(19,36,55,236),outline=(101,189,208,255),width=1)
d.rectangle((13,17,22,19),fill=(163,186,196,255))
d.rectangle((16,16,24,17),fill=(54,85,105,255))
d.rectangle((21,18,28,19),fill=(158,197,208,255))
d.point((28,18),fill=(64,245,255,255))
d.rectangle((13,21,17,22),fill=(62,227,233,255))
im.save(icon,optimize=True)

renderer=(J/"client/V176MicroMgVisualClient.java").read_text(encoding="utf-8")
mode=(J/"powerarmor/V176CompanionMode.java").read_text(encoding="utf-8")
projectile=(J/"powerarmor/V176MicroMgProjectile.java").read_text(encoding="utf-8")
assert "rightArmPose=HumanoidModel.ArmPose.BLOCK" in renderer
assert "submitModelPart(model.rightArm," not in renderer
assert "getRightArmPose().x()<-45F" in renderer
assert "setYBodyRot(yaw)" in mode
assert "destroyBlock(position,false,shooter)" in projectile
assert "END_ROD" not in projectile
print("V176_B757_16RPS_PLAYER_FIRSTPERSON_TURRET_FOLLOW_GLASS_ICE_ICON_PASS")
