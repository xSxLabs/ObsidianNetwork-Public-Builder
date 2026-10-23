#!/usr/bin/env python3
"""Build98: Power Armor visual HUD, real-tier first-person arms, Elytra jets,
night-vision action bar and safe replaceable-only suit placement.
Runs AFTER stage93, network Elytra94 and Jade95 on reconstructed sources.
"""
import os, json, struct, zlib
from pathlib import Path

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
res=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
MARK="BUILD98_POWER_ARMOR_VISUAL_AND_PLACEMENT"
def read(path):return path.read_text(encoding="utf-8")
def write(path,data):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(data,encoding="utf-8")
def once(text,old,new,label):
 n=text.count(old)
 assert n==1, f"{MARK} {label} anchor count {n}"
 return text.replace(old,new,1)

# Server-authoritative actionbar notification, never chat and never on every tick.
cmd=root/"powerarmor/PowerArmorCommands.java"
s=read(cmd)
old='''  chest.set(dev.obsidiannetwork.registry.ModDataComponents.POWER_ARMOR_UPGRADES.get(),String.join(",",cards));
  return Command.SINGLE_SUCCESS;
 }'''
new='''  chest.set(dev.obsidiannetwork.registry.ModDataComponents.POWER_ARMOR_UPGRADES.get(),String.join(",",cards));
  // BUILD98: temporary action bar (true), NEVER the chat log.
  p.displayClientMessage(Component.translatable(
    cards.contains("nightvision_on")?
      "message.obsidiannetwork.power_armor.night_on":
      "message.obsidiannetwork.power_armor.night_off"),true);
  return Command.SINGLE_SUCCESS;
 }'''
write(cmd,once(s,old,new,"nightvision command"))

# Only air or explicit harmless foliage, thin snow and invisible light.
# NEVER air-replace a solid snow block, farmland/crops, fluid, machines,
# cables, containers or any other arbitrary block.
world=root/"powerarmor/PowerArmorSuitWorld.java"
s=read(world)
anchor=''' private static BlockPos available(ServerPlayer player){'''
addon=''' // BUILD98_SUIT_REPLACEABLE: fail closed, no BlockTags.REPLACEABLE catchall.
 private static boolean suitPassable(net.minecraft.world.level.block.state.BlockState state){
  if(state.isAir())return true;
  var b=state.getBlock();
  return state.is(net.minecraft.tags.BlockTags.FLOWERS)
      || b==net.minecraft.world.level.block.Blocks.LIGHT
      || b==net.minecraft.world.level.block.Blocks.SNOW
      || b==net.minecraft.world.level.block.Blocks.SHORT_GRASS
      || b==net.minecraft.world.level.block.Blocks.TALL_GRASS
      || b==net.minecraft.world.level.block.Blocks.FERN
      || b==net.minecraft.world.level.block.Blocks.LARGE_FERN
      || b==net.minecraft.world.level.block.Blocks.DEAD_BUSH
      || b==net.minecraft.world.level.block.Blocks.SHORT_DRY_GRASS
      || b==net.minecraft.world.level.block.Blocks.TALL_DRY_GRASS;
 }
 private static boolean suitVolumeClearable(Level level,BlockPos pos){
  return suitPassable(level.getBlockState(pos))
      && suitPassable(level.getBlockState(pos.above()));
 }
 private static boolean clearSuitVolume(Level level,BlockPos pos){
  if(!suitVolumeClearable(level,pos))return false;
  var lower=level.getBlockState(pos);
  var upper=level.getBlockState(pos.above());
  if(!lower.isAir()&&!level.setBlock(pos,net.minecraft.world.level.block.Blocks.AIR.defaultBlockState(),3))
   return false;
  if(!upper.isAir()&&!level.getBlockState(pos.above()).isAir()
      && !level.setBlock(pos.above(),net.minecraft.world.level.block.Blocks.AIR.defaultBlockState(),3)){
    level.setBlock(pos,lower,3);
    return false;
  }
  return true;
 }
'''
s=once(s,anchor,addon+anchor,"volume helpers")
old='''   if(!level.isEmptyBlock(candidate)||!level.isEmptyBlock(candidate.above()))continue;'''
s=once(s,old,'''   if(!suitVolumeClearable(level,candidate))continue;''',"station candidate")
old='''   if(!level.isEmptyBlock(p)||!level.isEmptyBlock(p.above()))continue;'''
s=once(s,old,'''   if(!suitVolumeClearable(level,p))continue;''',"nearby candidate")
# Capture and restore only two world states on failed entity add. A successful
# exit owns exactly one stand; existing transfer-before-spawn code is preserved.
old='''  if(!level.addFreshEntity(stand))return null;'''
new='''  // BUILD98: remove harmless obstacles only after the suit spawn was prepared.
  if(!suitVolumeClearable(level,pos))return null;
  var oldLower=level.getBlockState(pos);
  var oldUpper=level.getBlockState(pos.above());
  if(!clearSuitVolume(level,pos))return null;
  if(!level.addFreshEntity(stand)){
   level.setBlock(pos,oldLower,3);
   level.setBlock(pos.above(),oldUpper,3);
   return null;
  }'''
s=once(s,old,new,"atomic spawn")
write(world,s)

# Client-only FE HUD + small white reactor jets. Flight physics/FE drains
# continue to be owned by the existing Network Elytra code.
hud=root/"client/PowerArmorBuild98Client.java"
assert not hud.exists(),MARK+" duplicate visual client"
write(hud,r'''package dev.obsidiannetwork.client;

import dev.obsidiannetwork.core.EnergyTool;
import dev.obsidiannetwork.powerarmor.PowerArmorElytraBridge;
import dev.obsidiannetwork.powerarmor.PowerArmorRuntime;
import java.util.concurrent.ThreadLocalRandom;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.phys.Vec3;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.RenderGuiEvent;
import net.neoforged.neoforge.event.tick.ClientTickEvent;

/** BUILD98_POWER_ARMOR_VISUAL_AND_PLACEMENT: all cosmetic effects are local. */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class PowerArmorBuild98Client {
 private PowerArmorBuild98Client(){}

 // Upper-left HUD near the vanilla armor points, never over hearts or hunger.
 @SubscribeEvent public static void hud(RenderGuiEvent.Post event){
  Minecraft mc=Minecraft.getInstance();
  if(mc.player==null || mc.options.hideGui)return;
  var p=mc.player;
  int tier=PowerArmorRuntime.tier(p.getItemBySlot(EquipmentSlot.HEAD),0);
  if(tier==0)return;
  long stored=0L, capacity=0L;
  for(int i=0;i<PowerArmorRuntime.SLOTS.length;i++){
   var item=p.getItemBySlot(PowerArmorRuntime.SLOTS[i]);
   if(PowerArmorRuntime.tier(item,i)!=tier)return;
   stored+=Math.max(0L,EnergyTool.energy(item));
   capacity+=Math.max(0L,EnergyTool.capacity(item));
  }
  if(capacity<=0)return;
  double fraction=Math.max(0D,Math.min(1D,stored/(double)capacity));
  int pct=(int)Math.round(fraction*100D);
  int x=mc.getWindow().getGuiScaledWidth()/2-91;
  int y=mc.getWindow().getGuiScaledHeight()-70;
  GuiGraphicsExtractor g=event.getGuiGraphics();
  int col=fraction<0.15?0xffdf5050:fraction<0.32?0xffe9b34e:0xff63cbea;
  g.fill(x-1,y-2,x+91,y+10,0x9b101923);
  g.fill(x,y+5,x+90,y+8,0xff243642);
  g.fill(x,y+5,x+(int)Math.round(90*fraction),y+8,col);
  g.text(mc.font,"POWER ARMOR",x,y-5,0xffb9d6df);
  g.text(mc.font,pct+"%",x+72,y-5,col);
 }

 @SubscribeEvent public static void jetThrusters(ClientTickEvent.Post event){
  Minecraft mc=Minecraft.getInstance();
  if(mc.level==null||mc.player==null)return;
  var p=mc.player;
  // Only complete MK1-MK12 suit with the actual Network Elytra module.
  if(!p.isFallFlying() || p.onGround())return;
  var chest=PowerArmorElytraBridge.chest(p);
  if(chest.isEmpty()||EnergyTool.energy(chest)<125L)return;
  boolean boost=p.isShiftKeyDown() && EnergyTool.energy(chest)>=1500L;
  if(!boost && p.tickCount%2!=0)return;
  Vec3 look=p.getLookAngle();
  Vec3 right=new Vec3(-look.z,0,look.x);
  if(right.lengthSqr()<1.0e-5)right=new Vec3(1,0,0);
  right=right.normalize();
  Vec3 backwards=look.scale(-0.3);
  ThreadLocalRandom rand=ThreadLocalRandom.current();
  for(int limb=0;limb<4;limb++){
   double lateral=(limb%2==0?-0.36:0.36);
   double y=limb<2?p.getEyeY()-0.60:p.getY()+0.20;
   Vec3 spawn=new Vec3(p.getX(),y,p.getZ()).add(right.scale(lateral)).add(backwards);
   int count=boost?3:1;
   for(int i=0;i<count;i++){
    double jitter=boost?0.045:0.02;
    double px=spawn.x+(rand.nextDouble()-.5)*jitter;
    double py=spawn.y+(rand.nextDouble()-.5)*jitter;
    double pz=spawn.z+(rand.nextDouble()-.5)*jitter;
    // White energy thrusters stream opposite travel, not noisy smoke.
    mc.level.addParticle(ParticleTypes.END_ROD,px,py,pz,
      -look.x*(boost?0.18:0.06),-look.y*(boost?0.18:0.06)-0.02,
      -look.z*(boost?0.18:0.06));
    if(boost && i==0)
     mc.level.addParticle(ParticleTypes.CLOUD,px,py,pz,
       -look.x*.12,-look.y*.12,-look.z*.12);
   }
  }
 }
}
''')

# Render a real suite-textured first-person arm: the actual upper-body armor
# right-arm pixel region is mapped into Minecraft's 64x64 player arm UVs for
# both arms. The renderer replaces vanilla skin ONLY when all suit parts match.
arms=root/"client/PowerArmorFirstPersonArms.java"
assert not arms.exists(),MARK+" duplicate arms"
write(arms,r'''package dev.obsidiannetwork.client;

import dev.obsidiannetwork.powerarmor.PowerArmorRuntime;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.entity.player.AvatarRenderer;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.HumanoidArm;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.RenderArmEvent;

/** BUILD98 actual MK1..MK12 first-person arms, no player-skin rewriting. */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class PowerArmorFirstPersonArms {
 private PowerArmorFirstPersonArms(){}
 @SubscribeEvent public static void renderArm(RenderArmEvent event){
  Minecraft mc=Minecraft.getInstance();
  if(event.getPlayer()!=mc.player)return;
  int tier=PowerArmorRuntime.tier(mc.player.getItemBySlot(EquipmentSlot.HEAD),0);
  if(tier<1||tier>12)return;
  for(int i=1;i<PowerArmorRuntime.SLOTS.length;i++)
   if(PowerArmorRuntime.tier(mc.player.getItemBySlot(PowerArmorRuntime.SLOTS[i]),i)!=tier)return;
  var renderer=mc.getEntityRenderDispatcher().getPlayerRenderer(event.getPlayer());
  var model=renderer.getModel();
  var part=event.getArm()==HumanoidArm.RIGHT?model.rightArm:model.leftArm;
  part.resetPose();
  part.zRot=event.getArm()==HumanoidArm.RIGHT?0.1f:-0.1f;
  Identifier texture=Identifier.fromNamespaceAndPath("obsidiannetwork",
      "textures/entity/power_armor_firstperson_mk"+tier+".png");
  event.getSubmitNodeCollector().submitModelPart(
    part,event.getPoseStack(),RenderTypes.entityTranslucent(texture),
    event.getPackedLight(),OverlayTexture.NO_OVERLAY,null);
  event.setCanceled(true);
 }
}
''')

# A tiny self-contained PNG decoder avoids adding Python image dependencies.
# Handles paletted MK1/MK2 and truecolor RGBA MK3..MK12 armor atlases.
def png_pixels(data):
 assert data[:8]==b"\x89PNG\r\n\x1a\n"
 chunks=[];k=8
 while k<len(data):
  n=int.from_bytes(data[k:k+4],"big");name=data[k+4:k+8]
  chunks.append((name,data[k+8:k+8+n]));k+=12+n
  if name==b"IEND":break
 header=next(x for key,x in chunks if key==b"IHDR")
 w,h,depth,mode,compression,filter_type,interlace=struct.unpack(">IIBBBBB",header)
 assert (w,h,depth,compression,filter_type,interlace)==(64,32,8,0,0,0)
 assert mode in (2,3,6),f"unexpected Power Armor PNG pixel type {mode}"
 bpp={2:3,3:1,6:4}[mode]
 palette=next((x for k,x in chunks if k==b"PLTE"),b"")
 alpha=next((x for k,x in chunks if k==b"tRNS"),b"")
 raw=zlib.decompress(b"".join(x for key,x in chunks if key==b"IDAT"))
 previous=bytearray(w*bpp);out=[];off=0
 for y in range(h):
  op=raw[off];off+=1
  scan=bytearray(raw[off:off+w*bpp]);off+=w*bpp
  for z in range(len(scan)):
   a=scan[z-bpp] if z>=bpp else 0
   b=previous[z];c=previous[z-bpp] if z>=bpp else 0
   if op==0:pred=0
   elif op==1:pred=a
   elif op==2:pred=b
   elif op==3:pred=(a+b)//2
   elif op==4:
    p=a+b-c;delta=(abs(p-a),abs(p-b),abs(p-c))
    pred=(a,b,c)[delta.index(min(delta))]
   else:raise AssertionError("unsupported PNG filter")
   scan[z]=(scan[z]+pred)&255
  previous=scan[:]
  pixels=[]
  for x in range(w):
   sub=scan[x*bpp:(x+1)*bpp]
   if mode==3:
    idx=sub[0];rgba=(*palette[idx*3:idx*3+3],alpha[idx] if idx<len(alpha) else 255)
   elif mode==2:rgba=(*sub,255)
   else:rgba=tuple(sub)
   assert len(rgba)==4
   pixels.append(rgba)
  out.append(pixels)
 assert off==len(raw)
 return out
def part(kind,data):
 return struct.pack(">I",len(data))+kind+data+struct.pack(">I",zlib.crc32(kind+data)&0xffffffff)
def make_arms(original):
 image=png_pixels(original)
 dest=[[(0,0,0,0) for _ in range(64)] for _ in range(64)]
 for y in range(16):
  for x in range(16):
   dest[16+y][40+x]=image[16+y][40+x]  # right arm
   dest[48+y][32+x]=image[16+y][55-x]  # opposite-side sleeve
 raw=b"".join(b"\0"+b"".join(bytes(color) for color in line) for line in dest)
 return (b"\x89PNG\r\n\x1a\n"+
   part(b"IHDR",struct.pack(">IIBBBBB",64,64,8,6,0,0,0))+
   part(b"IDAT",zlib.compress(raw,9))+part(b"IEND",b""))
for tier in range(1,13):
 name="power_armor"+(f"_mk{tier}" if tier>1 else "")+".png"
 source=res/"textures/entity/equipment/humanoid"/name
 assert source.is_file(),f"missing actual armor skin for MK{tier}: {source}"
 target=res/f"textures/entity/power_armor_firstperson_mk{tier}.png"
 target.parent.mkdir(parents=True,exist_ok=True)
 target.write_bytes(make_arms(source.read_bytes()))

# Localized actionbar messages (true flag, not system chat).
for lang,on,off in (
  ("en_us","Night Vision ON","Night Vision OFF"),
  ("de_de","Nachtsicht aktiviert","Nachtsicht deaktiviert")):
 target=res/"lang"/(lang+".json")
 data=json.loads(read(target))
 data["message.obsidiannetwork.power_armor.night_on"]=on
 data["message.obsidiannetwork.power_armor.night_off"]=off
 write(target,json.dumps(data,ensure_ascii=False,indent=2)+"\n")

assert "suitVolumeClearable(level,pos)" in read(world)
assert "p.displayClientMessage(Component.translatable(" in read(cmd)
assert all((res/f"textures/entity/power_armor_firstperson_mk{i}.png").is_file() for i in range(1,13))
print(MARK+" PASS: safe air/light/snow/grass/flower/bush replacement; 12 matching first-person suit arms; 4-limb white flight particles; actionbar nightvision; compact FE HUD")
