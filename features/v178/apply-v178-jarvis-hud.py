#!/usr/bin/env python3
"""v1.7.8 JARVIS HUD 2.0: local, independently toggled and scan-throttled.
Run after the complete v1.7.7 voice/status and armor patch chain.
"""
import os
from pathlib import Path

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"

def replace_one(rel,before,after):
 p=root/rel
 s=p.read_text(encoding="utf-8")
 assert s.count(before)==1,("V178_HUD_SOURCE_DRIFT",rel,before[:100],s.count(before))
 p.write_text(s.replace(before,after,1),encoding="utf-8")

def add(rel,java):
 p=root/rel
 p.parent.mkdir(parents=True,exist_ok=True)
 assert not p.exists(),("V178_HUD_DUPLICATE",rel)
 p.write_text(java,encoding="utf-8")

replace_one("client/V177JarvisSettings.java",
 '"startup_paste","startup_outcome"})',
 '"startup_paste","startup_outcome",\n'+
 '       "hud","hud_radar","hud_hostiles","hud_players","hud_distance",\n'+
 '       "hud_altitude","hud_speed","hud_compass","hud_health",\n'+
 '       "hud_energy","hud_integrity","hud_warnings"})')

replace_one("client/V177JarvisSettingsScreen.java",
 '''   {"home|Welcome back at home","actions|General action sounds",
    "sleep|General sleep sounds"}
  }
 };''',
 '''   {"home|Welcome back at home","actions|General action sounds",
    "sleep|General sleep sounds"}
  },
  { // v1.7.8 HUD 2.0 - every indicator independently configurable
   {"hud|HUD 2.0 master","hud_radar|Local radar",
    "hud_hostiles|Enemy markers","hud_players|Player markers",
    "hud_distance|Nearest enemy distance"},
   {"hud_altitude|Altitude","hud_speed|Speed (blocks/s)",
    "hud_compass|Heading","hud_health|Health",
    "hud_energy|Armor energy"},
   {"hud_integrity|Armor integrity","hud_warnings|Danger warnings"}
  }
 };''')

replace_one("client/V177JarvisSettingsScreen.java",
 '''  button(x,y,58,"VOICE",()->{page=0;subpage=0;});
  button(x+60,y,58,"SCAN",()->{page=1;subpage=0;});
  button(x+120,y,58,"ALERTS",()->{page=2;subpage=0;});
  button(x+180,y,58,"MODULES",()->{page=3;subpage=0;});''',
 '''  button(x,y,46,"VOICE",()->{page=0;subpage=0;});
  button(x+48,y,46,"SCAN",()->{page=1;subpage=0;});
  button(x+96,y,46,"ALERTS",()->{page=2;subpage=0;});
  button(x+144,y,46,"MODS",()->{page=3;subpage=0;});
  button(x+192,y,46,"HUD",()->{page=4;subpage=0;});''')

replace_one("client/V177JarvisClient.java",
 '''  g.pose().popMatrix();
 }
}
''',
 '''  g.pose().popMatrix();
  V178JarvisHud.draw(event);
 }
}
''')

add("client/V178JarvisHud.java",r'''package dev.obsidiannetwork.client;

import dev.obsidiannetwork.core.EnergyTool;
import dev.obsidiannetwork.powerarmor.PowerArmorRuntime;
import dev.obsidiannetwork.powerarmor.V177ArmorIntegrity;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.AABB;
import net.neoforged.neoforge.client.event.RenderGuiEvent;
import java.util.ArrayList;
import java.util.List;

/** No packets or server ticks. Scan loaded nearby entities at most once per 10
 * client ticks; render immutable tiny marker snapshots between scans.
 * Never asks the world to load chunks, and never accesses off-thread state.
 */
public final class V178JarvisHud {
 private V178JarvisHud(){}
 private record Dot(double dx,double dz,boolean hostile){}
 private static List<Dot> dots=List.of();
 private static long lastScanTick=Long.MIN_VALUE;
 private static net.minecraft.resources.ResourceKey<net.minecraft.world.level.Level> scanDimension;
 private static java.util.UUID scanPlayer;
 private static int nearestHostile=-1;
 private static int energyPercent=0,integrityPercent=0,healthPercent=100;
 private static final int MAX_DOTS=64;
 private static final int SCAN_PERIOD=10;

 private static boolean on(String key){return V177JarvisSettings.on(key);}
 private static void refresh(LocalPlayer p){
  if(!on("hud"))return;
  long tick=p.level().getGameTime();
  if(scanPlayer!=null&&scanPlayer.equals(p.getUUID())
      &&p.level().dimension()==scanDimension
      &&tick>=lastScanTick&&tick-lastScanTick<SCAN_PERIOD)return;
  lastScanTick=tick;
  scanPlayer=p.getUUID();
  scanDimension=p.level().dimension();
  final int radius=V177JarvisSettings.radius;
  final double radiusSquared=(double)radius*radius;
  ArrayList<Dot> found=new ArrayList<>(24);
  double closest=Double.POSITIVE_INFINITY;
  // The client's loaded entity index bounds the search. No chunk lookups.
  for(Entity entity:p.level().getEntities(p,p.getBoundingBox().inflate(radius),
           e->e instanceof Monster||e instanceof Player)){
   if(entity.isRemoved())continue;
   boolean hostile=entity instanceof Monster;
   double dx=entity.getX()-p.getX(),dz=entity.getZ()-p.getZ();
   double d=dx*dx+dz*dz;
   if(d>radiusSquared)continue;
   if(hostile&&d<closest)closest=d;
   if((hostile&&on("hud_hostiles"))||(!hostile&&on("hud_players"))){
    if(found.size()<MAX_DOTS)found.add(new Dot(dx,dz,hostile));
   }
  }
  dots=List.copyOf(found);
  nearestHostile=closest==Double.POSITIVE_INFINITY?-1:(int)Math.round(Math.sqrt(closest));
  if(on("hud_energy")){
   long stored=0,max=0;
   for(var slot:PowerArmorRuntime.SLOTS){
    var stack=p.getItemBySlot(slot);
    stored+=Math.max(0,EnergyTool.energy(stack));
    max+=Math.max(0,EnergyTool.capacity(stack));
   }
   energyPercent=max==0?0:(int)Math.round(100.0*stored/max);
  }
  if(on("hud_integrity"))integrityPercent=V177ArmorIntegrity.totalPercent(p);
  if(on("hud_health"))healthPercent=(int)Math.round(100.0*
      p.getHealth()/Math.max(1.0,p.getMaxHealth()));
 }

 public static void draw(RenderGuiEvent.Post event){
  Minecraft mc=Minecraft.getInstance();
  LocalPlayer p=mc.player;
  if(p==null||mc.level==null||!V177JarvisClient.enabled()
     ||!V177JarvisClient.available()||!on("hud"))return;
  refresh(p);
  var g=event.getGuiGraphics();
  int width=mc.getWindow().getGuiScaledWidth();
  final int ox=width-131,oy=9;
  if(on("hud_radar")){
   g.fill(ox,oy,ox+120,oy+119,0xb0102733);
   g.fill(ox+4,oy+15,ox+116,oy+16,0xff2f6980);
   g.fill(ox+4,oy+112,ox+116,oy+113,0xff2f6980);
   g.fill(ox+4,oy+16,ox+5,oy+113,0xff2f6980);
   g.fill(ox+115,oy+16,ox+116,oy+113,0xff2f6980);
   g.text(mc.font,"RADAR "+V177JarvisSettings.radius+"m",ox+6,oy+4,0xff85e7f5);
   int cx=ox+60,cy=oy+64;
   g.fill(cx-1,cy-1,cx+2,cy+2,0xffffffff);
   int radius=V177JarvisSettings.radius;
   for(Dot d:dots){
    int x=cx+(int)Math.round(49*d.dx/radius);
    int y=cy+(int)Math.round(46*d.dz/radius);
    if(x<ox+6||x>ox+113||y<oy+17||y>oy+110)continue;
    g.fill(x-1,y-1,x+2,y+2,d.hostile?0xfffa6578:0xff63d6ff);
   }
   g.text(mc.font,"N",cx-3,oy+18,0xff93dfea);
  }
  int x=width-131,y=on("hud_radar")?oy+123:oy;
  if(on("hud_distance")&&nearestHostile>=0){
   g.text(mc.font,"HOSTILE "+nearestHostile+"m",x+4,y,nearestHostile<=8?0xffff8d78:0xffa5e9f4);
   y+=12;
  }
  if(on("hud_compass")){
   double heading=(p.getYRot()%360+360)%360;
   String direction=heading<45||heading>=315?"S":heading<135?"W":heading<225?"N":"E";
   g.text(mc.font,"HEADING "+direction+" "+(int)heading, x+4,y,0xff93dfea);
   y+=12;
  }
  if(on("hud_altitude")){
   g.text(mc.font,"ALTITUDE "+p.blockPosition().getY(),x+4,y,0xff93dfea);
   y+=12;
  }
  if(on("hud_speed")){
   var motion=p.getDeltaMovement();
   int speed=(int)Math.round(Math.sqrt(motion.x*motion.x+motion.z*motion.z)*20);
   g.text(mc.font,"SPEED "+speed+" b/s",x+4,y,0xff93dfea);
   y+=12;
  }
  if(on("hud_health")){
   g.text(mc.font,"HEALTH "+healthPercent+"%",x+4,y,0xff8eeec4);
   y+=12;
  }
  if(on("hud_energy")){
   g.text(mc.font,"ENERGY "+energyPercent+"%",x+4,y,energyPercent<20?0xffffa07c:0xff8eeec4);
   y+=12;
  }
  if(on("hud_integrity")){
   g.text(mc.font,"INTEGRITY "+integrityPercent+"%",x+4,y,integrityPercent<20?0xffffa07c:0xff8eeec4);
   y+=12;
  }
  if(on("hud_warnings")){
   if(nearestHostile>=0&&nearestHostile<=8){
    g.text(mc.font,"WARNING: HOSTILE NEAR",x+4,y,0xffff7777);
    y+=12;
   }
   if(integrityPercent<=15&&on("hud_integrity"))
    g.text(mc.font,"WARNING: ARMOR DAMAGE",x+4,y,0xffff7777);
  }
 }
}
''')
print("V178_JARVIS_HUD_2_CLIENT_LOCAL_CACHED_12_TOGGLES_INSTALLED")
