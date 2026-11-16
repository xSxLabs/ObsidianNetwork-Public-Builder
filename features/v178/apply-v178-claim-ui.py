#!/usr/bin/env python3
"""B1662 xSxLabs GUI visual system: consistent claims, worldmap, minimap,
waypoints, trust, and mining selection styling; never touches permission logic.
"""
import os
from pathlib import Path
ROOT=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def patch(rel,old,new):
 path=ROOT/rel;s=path.read_text(encoding="utf-8")
 count=s.count(old)
 if count!=1:
  # B1663: downstream generators produce equivalent Java with either
  # two or three leading spaces. Shift all lines together, not substrings.
  def indent_shift(value,delta):
   result=[]
   for line in value.split("\n"):
    if not line.strip():
     result.append(line);continue
    spaces=len(line)-len(line.lstrip(" "))
    if spaces+delta<0:return None
    result.append(" "*(spaces+delta)+line[spaces:])
   return "\n".join(result)
  for delta in (-1,1,-2,2):
   candidate=indent_shift(old,delta)
   replacement=indent_shift(new,delta)
   if candidate is not None and s.count(candidate)==1:
    old,new=candidate,replacement
    count=1
    break
 assert count==1,("B1662_GUI_SOURCE_DRIFT",rel,count,old[:120])
 path.write_text(s.replace(old,new,1),encoding="utf-8")

theme=ROOT/"client/V178UiTheme.java"
assert not theme.exists(),"B1662_GUI_THEME_DUPLICATE"
theme.parent.mkdir(parents=True,exist_ok=True)
theme.write_text(r'''package dev.obsidiannetwork.client;
import net.minecraft.client.gui.GuiGraphicsExtractor;
/** One lightweight reusable xSxLabs visual language for screen backgrounds.
 * Baked GUI primitives only: no textures loaded during frames or draw scans.
 */
public final class V178UiTheme {
 private V178UiTheme(){}
 public static final int CYAN=0xff65dce9,WHITE=0xffd9edf4;
 public static void panel(GuiGraphicsExtractor g,int x,int y,int w,int h){
  if(w<=6||h<=8)return;
  int xx=x+w,yy=y+h;
  g.fill(x,y,xx,yy,0xe7131c2c);           // charcoal glass
  g.fill(x+2,y+2,xx-2,y+24,0xbb263d50); // header metal
  g.fill(x,y,xx,y+2,CYAN);               // luminous cyan leading edge
  g.fill(x,yy-2,xx,yy,0xff243b50);
  g.fill(x,y+2,x+2,yy-2,0xff396478);
  g.fill(xx-2,y+2,xx,yy-2,0xff396478);
  g.fill(x+4,y+26,xx-4,y+27,0x8868bdd3);
 }
 public static void miniFrame(GuiGraphicsExtractor g,int x,int y,int w,int h){
  int xx=x+w,yy=y+h;
  g.fill(x,y,xx,yy,0xd4132030);
  g.fill(x,y,xx,y+2,CYAN);
  g.fill(x,yy-2,xx,yy,0xff355568);
  g.fill(x,y,x+2,yy,0xff355568);
  g.fill(xx-2,y,xx,yy,0xff355568);
  g.fill(x+3,y+3,xx-3,y+17,0xbb254054);
 }
}
''',encoding="utf-8")

patch("client/V178ClaimsMapScreen.java",
'''  g.fill(x0-4,y0-5,x0+w+4,y0+w+34,0xe8081a28);''',
'''  // B1662 xSxLabs themed claim/map frame, cached terrain drawing unchanged.
  V178UiTheme.panel(g,x0-8,y0-27,w+16,w+75);''')
patch("client/V178ClaimsMapScreen.java",
'''  if(!good&&claiming)g.text(font,"Updating claim ownership...",x0+2,y0+4,0xfff3c479);''',
'''  // Compact persistent legend uses the existing server-owned claim states.
  if(w>=240){
   int legendY=y0+w+34;
   g.fill(x0+1,legendY,x0+8,legendY+7,0xff4deb91);
   g.text(font,"OWN",x0+11,legendY-1,0xffa7d4e3);
   g.fill(x0+62,legendY,x0+69,legendY+7,0xff7be3f9);
   g.text(font,"TEAM",x0+72,legendY-1,0xffa7d4e3);
   g.fill(x0+130,legendY,x0+137,legendY+7,0xffdf6b75);
   g.text(font,"OTHER",x0+140,legendY-1,0xffa7d4e3);
   g.fill(x0+213,legendY,x0+220,legendY+7,0xff66ee71);
   g.text(font,"LOADED",x0+223,legendY-1,0xffa7d4e3);
  }
  if(!good&&claiming)g.text(font,"Updating claim ownership...",x0+2,y0+4,0xfff3c479);''')

# Preserve original minimap options and render, but make the minimap choose
# an unoccupied corner when the (user-positioned) HUD radar or text lives there.
patch("client/V178ClaimsClient.java",
'''  int ox=mc.getWindow().getGuiScaledWidth()-99,oy=9;
  // Avoid drawing the minimap over JARVIS radar/diagnostics.
  if(V177JarvisClient.enabled()&&V177JarvisClient.available()
      &&V177JarvisSettings.on("hud")&&V177JarvisSettings.on("hud_radar")){
   ox=9;oy=Math.max(45,mc.getWindow().getGuiScaledHeight()-111);
  }''',
'''  int infoRows=(option("coords")?2:0)+(option("chunk")?1:0)
     +(option("daytime")?1:0);
  int miniHeight=97+infoRows*10,miniCorner=1;
  // Preserve the top-right default, but avoid whichever HUD corner is busy.
  if(V177JarvisClient.enabled()&&V177JarvisClient.available()
      &&V177JarvisSettings.on("hud")){
   boolean[] busy=new boolean[4];
   if(V177JarvisSettings.on("hud_radar"))
     busy[V178HudLayout.radarCorner()]=true;
   busy[V178HudLayout.textCorner()]=true;
   if(busy[miniCorner]){
    for(int corner:new int[]{2,0,3,1})if(!busy[corner]){
     miniCorner=corner;break;
    }
   }
  }
  int ox=V178HudLayout.x(miniCorner,mc.getWindow().getGuiScaledWidth(),91);
  int oy=V178HudLayout.y(miniCorner,mc.getWindow().getGuiScaledHeight(),miniHeight);''')
patch("client/V178ClaimsClient.java",
'''   int infoRows=(option("coords")?2:0)+(option("chunk")?1:0)
      +(option("daytime")?1:0);
   g.fill(ox-2,oy-2,ox+91,oy+97+infoRows*10,0xc0081d2b);''',
'''   V178UiTheme.miniFrame(g,ox-3,oy-4,94,miniHeight+8);''')

patch("client/V178MapSettingsScreen.java",
'''  g.text(font,"MINIMAP + INFO",width/2-153,Math.max(5,height/2-113),0xff9debf2);''',
'''  V178UiTheme.panel(g,width/2-164,Math.max(7,height/2-128),328,232);
  g.text(font,"MINIMAP + INFO",width/2-153,Math.max(5,height/2-113),V178UiTheme.CYAN);''')
patch("client/V178MapSettingsScreen.java",
'''  g.text(font,"FULL MAP",width/2+5,Math.max(5,height/2-113),0xff9debf2);''',
'''  g.text(font,"FULL MAP",width/2+5,Math.max(5,height/2-113),V178UiTheme.CYAN);''')

patch("client/V178ClaimsTeamScreen.java",
'''  g.text(font,"TRUSTED PLAYERS",width/2-65,height/2-67,0xff9ce8f2);''',
'''  V178UiTheme.panel(g,width/2-120,height/2-82,240,185);
  g.text(font,"TRUSTED PLAYERS",width/2-65,height/2-67,V178UiTheme.CYAN);''')
patch("client/V178WaypointManagerScreen.java",
'''  g.text(font,"WAYPOINT MANAGER | click to edit",width/2-139,''',
'''  V178UiTheme.panel(g,width/2-150,Math.max(5,height/2-138),298,244);
  g.text(font,"WAYPOINT MANAGER | click to edit",width/2-139,''')
patch("client/V178WaypointEditorScreen.java",
'''  g.text(font,"WAYPOINT | chunk "+cx+", "+cz,x,y,0xff96e3f1);''',
'''  V178UiTheme.panel(g,x-9,y-15,228,190);
  g.text(font,"WAYPOINT | chunk "+cx+", "+cz,x,y,V178UiTheme.CYAN);''')
patch("client/V178MiningAreaScreen.java",
'''   g.fill(x0-4,y0-5,x0+w+4,y0+w+40,0xea102132);''',
'''   V178UiTheme.panel(g,x0-8,y0-27,w+16,w+85);''')

# The themed rendering path is server/network independent and touch-free.
for rel in ("client/V178ClaimsMapScreen.java","client/V178MiningAreaScreen.java",
            "client/V178MapSettingsScreen.java","client/V178ClaimsTeamScreen.java"):
 assert "V178UiTheme.panel(" in (ROOT/rel).read_text(),("B1662_GUI_THEME_GATE",rel)
assert "busy[V178HudLayout.radarCorner()]" in (ROOT/"client/V178ClaimsClient.java").read_text()
print("B1662_XSXLABS_CLAIM_MINIMAP_TRUST_MINING_GUI_STYLE_AND_HUD_AVOIDANCE_PASS")
