#!/usr/bin/env python3
"""Build 106: Draconic-inspired real translucent 3D energy field (visual-only).
Runs AFTER Build104 / Build105. Replaces only PowerArmorShieldClient.java
and adds its dedicated texture. Never touches damage, items, equipment,
energy costs, recipes, station, cards, recovery, networking or saved data.
"""
import json
import math
import os
import struct
import zlib
from pathlib import Path

source=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
resources=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
client=source/"client/PowerArmorShieldClient.java"
previous=client.read_text(encoding="utf-8")
assert "BUILD104_FORCEFIELD_AURA" in previous
assert "DustParticleOptions" in previous
assert 'if(id.equals("energy_shield"))card=true;' in previous

# Retain the original only-card-installed, complete matching suit and FE gates.
# Switch from independent particle samples to a continuous tessellated ellipsoid
# around the body. Surface cells use an original procedurally drawn hex texture.
client.write_text(r'''package dev.obsidiannetwork.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import dev.obsidiannetwork.core.EnergyTool;
import dev.obsidiannetwork.powerarmor.PowerArmorRuntime;
import dev.obsidiannetwork.registry.ModDataComponents;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.RenderPlayerEvent;

/**
 * BUILD106_DRACONIC_STYLE_SHIELD_SHELL
 * Closed 3D translucent energy bubble (NOT point particles). Tessellation and
 * softly glowing hex cells follow the player, no cross-frame buffers/state.
 * Pure client effect: Build104 keeps sole authority over actual FE and damage.
 */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class PowerArmorShieldClient {
 private PowerArmorShieldClient(){}
 private static final ResourceLocation SKIN=ResourceLocation.fromNamespaceAndPath(
      "obsidiannetwork","textures/entity/power_armor_shield_hex.png");
 private static final RenderType SHIELD_RENDER=RenderTypes.entityTranslucent(SKIN);
 private static final int LONGITUDE=28;
 private static final int LATITUDE=16;
 private static final float RX=.83F, RY=1.06F, RZ=.83F;

 private static boolean hasActiveShield(Player wearer){
  int tier=PowerArmorRuntime.tier(wearer.getItemBySlot(EquipmentSlot.HEAD),0);
  if(tier<1||tier>24)return false;
  boolean card=false;
  for(int i=0;i<PowerArmorRuntime.SLOTS.length;i++){
   EquipmentSlot slot=PowerArmorRuntime.SLOTS[i];
   var armor=wearer.getItemBySlot(slot);
   if(PowerArmorRuntime.tier(armor,i)!=tier||EnergyTool.energy(armor)<20L)return false;
   String installed=armor.get(ModDataComponents.POWER_ARMOR_UPGRADES.get());
   if(installed==null)continue;
   for(String id:installed.split(","))if(id.equals("energy_shield"))card=true;
  }
  return card;
 }

 /** Post-player render includes all 4-piece suit textures; shell is drawn over them. */
 @SubscribeEvent
 public static void onRenderPlayer(RenderPlayerEvent.Post<?> event){
  Minecraft mc=Minecraft.getInstance();
  if(mc.level==null||mc.player==null)return;
  var state=event.getRenderState();
  if(state.isSpectator||state.isInvisible||state.distanceToCameraSq>48.0D*48.0D)return;
  if(!(mc.level.getEntity(state.id) instanceof Player wearer))return;
  if(!hasActiveShield(wearer))return;
  // Player render is omitted in vanilla first person; no unwanted HUD obstruction.
  float time=wearer.tickCount+event.getPartialTick();
  float pulse=(float)(.5D+.5D*Math.sin(time*.075D));
  // Soft cyan membrane at idle, strongly luminous across the ENTIRE hit surface.
  float impact=Math.min(1.0F,Math.max(0F,wearer.hurtTime-event.getPartialTick())/8.0F);
  int membraneAlpha=Math.min(230,(int)(60F+9F*pulse+165F*impact));
  final float ticks=time,hit=impact;
  event.getSubmitNodeCollector().submitCustomGeometry(
      event.getPoseStack(),SHIELD_RENDER,
      (pose,buffer)->drawShell(pose,buffer,ticks,hit,membraneAlpha));
 }

 private static void drawShell(PoseStack.Pose pose,VertexConsumer vertex,
                               float time,float hit,int alpha){
  // Every longitude/latitude tile is a filled quad. The tiling texture has
  // connected energy cells, not floating particles, and wraps around the shell.
  for(int y=0;y<LATITUDE;y++){
   float v0=(float)y/LATITUDE,v1=(float)(y+1)/LATITUDE;
   double lat0=-Math.PI/2+Math.PI*v0;
   double lat1=-Math.PI/2+Math.PI*v1;
   for(int x=0;x<LONGITUDE;x++){
    double lon0=2*Math.PI*x/LONGITUDE,lon1=2*Math.PI*(x+1)/LONGITUDE;
    // A slender animated ripple travels around the field while it's hit.
    float ripple=(float)(.5D+.5D*Math.sin(time*.45D+x*.38D-y*.51D));
    int opacity=Math.min(255,alpha+(int)(hit*25F*ripple));
    // Surface points: outside normal is preserved for the entity lighting.
    vertex(pose,vertex,lat0,lon0,0F,0F,opacity);
    vertex(pose,vertex,lat1,lon0,0F,1F,opacity);
    vertex(pose,vertex,lat1,lon1,1F,1F,opacity);
    vertex(pose,vertex,lat0,lon1,1F,0F,opacity);
   }
  }
 }

 private static void vertex(PoseStack.Pose pose,VertexConsumer out,
                            double latitude,double longitude,float u,float v,int alpha){
  float c=(float)Math.cos(latitude),s=(float)Math.sin(latitude);
  float nx=c*(float)Math.cos(longitude),nz=c*(float)Math.sin(longitude);
  float x=RX*nx,z=RZ*nz,y=.95F+RY*s;
  out.addVertex(pose,x,y,z)
     .setColor(93,221,255,alpha)
     .setUv(u,v)
     .setOverlay(OverlayTexture.NO_OVERLAY)
     .setLight(LightTexture.FULL_BRIGHT)
     .setNormal(pose,nx,s,nz);
 }
}
''',encoding="utf-8")

# Original 64px soft cell texture. Warm shaded faces + sharp turquoise outlines
# give the shield a connected honeycomb appearance, not a particle cloud.
tex=resources/"textures/entity/power_armor_shield_hex.png"
assert not tex.exists(),"BUILD106 texture already exists"
tex.parent.mkdir(parents=True,exist_ok=True)
N=64
pixels=[]
def segment_distance(px,py,ax,ay,bx,by):
 dx,dy=bx-ax,by-ay
 t=max(0.0,min(1.0,((px-ax)*dx+(py-ay)*dy)/(dx*dx+dy*dy)))
 return math.hypot(px-(ax+t*dx),py-(ay+t*dy))
for yy in range(N):
 row=bytearray([0])
 for xx in range(N):
  px,py=xx+.5,yy+.5
  # 18px hex radii, stagger rows. Overdraw copies around edges for seamless tile.
  distance=999.0
  for j in range(-2,5):
   cy=32+j*27
   for i in range(-3,5):
    cx=32+i*31.2+(15.6 if (j&1) else 0)
    p=[(cx+18*math.cos(math.pi/3*k+math.pi/6),
        cy+18*math.sin(math.pi/3*k+math.pi/6)) for k in range(6)]
    distance=min(distance,*(
       segment_distance(px,py,*p[k],*p[(k+1)%6])
       for k in range(6)))
  bright=max(0.0,min(1.0,(2.9-distance)/2.5))
  line=max(0.0,min(1.0,(1.15-distance)/.8))
  # Depth stays very translucent; hit flash increases the per-vertex alpha.
  red=int(24+90*bright+35*line)
  green=int(107+94*bright+40*line)
  blue=int(169+48*bright+28*line)
  alpha=int(125+38*bright+62*line)
  row.extend((min(255,red),min(255,green),min(255,blue),min(255,alpha)))
 pixels.append(bytes(row))
raw=b"".join(pixels)
def chunk(kind,data):
 return struct.pack(">I",len(data))+kind+data+struct.pack(">I",zlib.crc32(kind+data)&0xffffffff)
png=b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",N,N,8,6,0,0,0))+chunk(b"IDAT",zlib.compress(raw,9))+chunk(b"IEND",b"")
tex.write_bytes(png)

for lang,title in (
 ("en_us","Energy Shield: continuous semi-transparent 3D energy field. Flashes brightly on hit."),
 ("de_de","Energieschild: geschlossene, transparente 3D-Energiehülle. Leuchtet bei Treffern auf."),
):
 path=resources/"lang"/(lang+".json")
 data=json.loads(path.read_text(encoding="utf-8"))
 data["message.obsidiannetwork.power_armor.energy_shield_info"]=title
 data["jade.obsidiannetwork.power_armor.energy_shield"]=title
 path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

assert 'submitCustomGeometry(' in client.read_text(encoding="utf-8")
assert 'RenderPlayerEvent.Post<?>' in client.read_text(encoding="utf-8")
assert 'onRenderPlayer' in client.read_text(encoding="utf-8")
assert "DustParticleOptions" not in client.read_text(encoding="utf-8")
assert len(png)>1024
print("BUILD106_3D_HEX_ENERGY_SHELL PASS: full translucent 28x16 quad 3D body shell, damage flash on entire surface, server power and FE logic unchanged")
