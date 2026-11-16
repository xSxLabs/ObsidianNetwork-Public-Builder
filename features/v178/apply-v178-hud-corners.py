#!/usr/bin/env python3
"""B1662 HUD 2.0: independent persistent radar/text corners, no render-time I/O."""
import os
from pathlib import Path

ROOT=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def patch(rel,old,new):
 p=ROOT/rel;s=p.read_text(encoding="utf-8")
 n=s.count(old)
 assert n==1,("B1662_HUD_SOURCE_DRIFT",rel,n,old[:120])
 p.write_text(s.replace(old,new,1),encoding="utf-8")

layout=ROOT/"client/V178HudLayout.java"
assert not layout.exists(),"B1662_HUD_LAYOUT_DUPLICATE"
layout.parent.mkdir(parents=True,exist_ok=True)
layout.write_text(r'''package dev.obsidiannetwork.client;
import net.minecraft.client.Minecraft;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.io.IOException;
import java.util.Properties;

/** Independent top-left/top-right/bottom-left/bottom-right positioning.
 * Settings read lazily once per client session and written only on clicks.
 */
public final class V178HudLayout {
 private V178HudLayout(){}
 private static boolean loaded;
 private static int radar=1,text=1;
 private static Path file(){
  return Minecraft.getInstance().gameDirectory.toPath()
    .resolve("config").resolve("xsxlabs-hud2-layout.properties");
 }
 private static int valid(String v,int fallback){
  try{int i=Integer.parseInt(v);return i>=0&&i<=3?i:fallback;}
  catch(NumberFormatException bad){return fallback;}
 }
 private static void ensure(){
  if(loaded)return;
  loaded=true;
  try{
   var path=file();
   if(!Files.isRegularFile(path))return;
   Properties p=new Properties();
   try(var in=Files.newInputStream(path)){p.load(in);}
   radar=valid(p.getProperty("radar_corner","1"),1);
   text=valid(p.getProperty("text_corner","1"),1);
  }catch(IOException error){
   System.err.println("[xSxLabs] HUD 2.0 position read failed: "+error);
  }
 }
 private static void save(){
  Path temp=null;
  try{
   Path dest=file();
   Files.createDirectories(dest.getParent());
   temp=Files.createTempFile(dest.getParent(),"xsx-hud2-",".tmp");
   Properties properties=new Properties();
   properties.setProperty("radar_corner",Integer.toString(radar));
   properties.setProperty("text_corner",Integer.toString(text));
   try(var out=Files.newOutputStream(temp)){
    properties.store(out,"xSxLabs HUD 2.0 independent corners");
   }
   try{Files.move(temp,dest,StandardCopyOption.REPLACE_EXISTING,
      StandardCopyOption.ATOMIC_MOVE);}
   catch(java.nio.file.AtomicMoveNotSupportedException notAtomic){
    Files.move(temp,dest,StandardCopyOption.REPLACE_EXISTING);
   }
  }catch(IOException error){
   System.err.println("[xSxLabs] HUD 2.0 position save failed: "+error);
  }finally{
   if(temp!=null)try{Files.deleteIfExists(temp);}catch(IOException ignored){}
  }
 }
 public static int radarCorner(){ensure();return radar;}
 public static int textCorner(){ensure();return text;}
 public static void cycleRadar(){ensure();radar=(radar+1)&3;save();}
 public static void cycleText(){ensure();text=(text+1)&3;save();}
 public static String label(int corner){
  return switch(corner){
   case 0->"TOP LEFT";case 1->"TOP RIGHT";
   case 2->"BOTTOM LEFT";default->"BOTTOM RIGHT";
  };
 }
 public static int x(int corner,int screenWidth,int boxWidth){
  return (corner&1)==0?9:Math.max(9,screenWidth-boxWidth-9);
 }
 public static int y(int corner,int screenHeight,int boxHeight){
  return (corner&2)==0?9:Math.max(9,screenHeight-boxHeight-9);
 }
}
''',encoding="utf-8")

patch("client/V178JarvisHud.java",
'''  int width=mc.getWindow().getGuiScaledWidth();
  final int ox=width-131,oy=9;''',
'''  int width=mc.getWindow().getGuiScaledWidth();
  int height=mc.getWindow().getGuiScaledHeight();
  int radarCorner=V178HudLayout.radarCorner();
  final int ox=V178HudLayout.x(radarCorner,width,120);
  final int oy=V178HudLayout.y(radarCorner,height,119);''')
patch("client/V178JarvisHud.java",
'''  int x=width-131,y=on("hud_radar")?oy+123:oy;''',
'''  // B1662: text and radar have separate persisted anchors.
  int textCorner=V178HudLayout.textCorner();
  int rows=(on("hud_distance")?1:0)+(on("hud_compass")?1:0)
    +(on("hud_altitude")?1:0)+(on("hud_speed")?1:0)
    +(on("hud_health")?1:0)+(on("hud_energy")?1:0)
    +(on("hud_integrity")?1:0)+(on("hud_warnings")?2:0);
  int textHeight=Math.max(16,rows*12+2);
  int x=V178HudLayout.x(textCorner,width,128);
  int y=V178HudLayout.y(textCorner,height,textHeight);
  // If both share an anchor, keep them apart (also at bottom corners).
  if(on("hud_radar")&&radarCorner==textCorner){
   if((textCorner&2)!=0)y=oy-textHeight-5;
   else y=oy+123;
  }
  y=Math.max(3,Math.min(height-12,y));''')
patch("client/V177JarvisSettingsScreen.java",
'''  // Only a voluntary click resets current player's voice flags.''',
'''  // HUD layout controls remain in the JARVIS action-wheel HUD tab.
  // Third HUD subpage has only two indicator toggles, leaving room here.
  if(page==4&&subpage==2){
   button(x,y+69,238,"Radar corner: "+V178HudLayout.label(V178HudLayout.radarCorner()),
     V178HudLayout::cycleRadar);
   button(x,y+92,238,"HUD text corner: "+V178HudLayout.label(V178HudLayout.textCorner()),
     V178HudLayout::cycleText);
  }
  // Only a voluntary click resets current player's voice flags.''')
# Fail-closed generated-contract validation.
hud=(ROOT/"client/V178JarvisHud.java").read_text(encoding="utf-8")
screen=(ROOT/"client/V177JarvisSettingsScreen.java").read_text(encoding="utf-8")
for token in ("V178HudLayout.radarCorner()","V178HudLayout.textCorner()",
              "int height=mc.getWindow().getGuiScaledHeight();",
              "if(on(\"hud_radar\")&&radarCorner==textCorner)"):
 assert token in hud,("B1662_HUD_RENDER_GATE",token)
for token in ("Radar corner: ","HUD text corner: ","V178HudLayout::cycleRadar",
              "V178HudLayout::cycleText"):
 assert token in screen,("B1662_HUD_SETTINGS_GATE",token)
print("B1662_HUD_INDEPENDENT_FOUR_CORNERS_PERSISTENT_PASS")
