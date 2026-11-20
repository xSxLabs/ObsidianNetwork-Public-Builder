#!/usr/bin/env python3
"""B1725: non-overlapping, responsive map toolbar and actual minimap options.

Why: pre-existing Team at x=347, Teams at width-67 and Settings at width-82
overlap. Minecraft handles the earlier widget, so Settings opens chunk/team
management instead. Replace only map init/navigation and client settings UI.
All original actions remain, with separate visible buttons; no server packets,
new render ticks, data mutations or changes to minimap preferences.
"""
import os
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/client"
screen=J/"V178ClaimsMapScreen.java"
src=screen.read_text(encoding="utf-8")
start_tag=" @Override protected void init(){"
assert src.count(start_tag)==1,("B1725_MAP_INIT_MISSING",src.count(start_tag))
start=src.index(start_tag)
brace=src.index("{",start)
depth=0
end=None
for index in range(brace,len(src)):
    if src[index]=="{":depth+=1
    elif src[index]=="}":
        depth-=1
        if depth==0:
            end=index+1
            break
assert end is not None
old=src[start:end]
for required in ("Button.builder(", "V178ClaimsClient.toggleMinimap()",
                 "V178WaypointEditorScreen", "V178WaypointManagerScreen",
                 "V178ClaimTeamScreen", "V178ClaimsTeamScreen",
                 "V178MapSettingsScreen"):
    assert required in old,("B1725_MAP_OLD_NAV_DRIFT",required)
assert "toolbarBottom" not in src

# Every world-map action gets its own independent click rectangle. There are
# no overlapping buttons; for narrow GUI scales the toolbar wraps to rows.
# Reserve real vertical space for these rows in the map viewport.
insertion=r'''
 private int toolbarBottom=30;
 private void nav(String label,int buttonWidth,Runnable action,int[] cursor){
  if(cursor[0]+buttonWidth>width-8){
   cursor[0]=8;
   cursor[1]+=25;
  }
  addRenderableWidget(Button.builder(Component.literal(label),b->action.run())
      .bounds(cursor[0],cursor[1],buttonWidth,20).build());
  toolbarBottom=Math.max(toolbarBottom,cursor[1]+21);
  cursor[0]+=buttonWidth+5;
 }
'''
assert " private void center(){" in src
src=src.replace(" private void center(){",insertion+" private void center(){",1)
start=src.index(start_tag);brace=src.index("{",start)
depth=0;end=None
for index in range(brace,len(src)):
    if src[index]=="{":depth+=1
    elif src[index]=="}":
        depth-=1
        if depth==0:end=index+1;break
assert end is not None
new=r''' @Override protected void init(){
  toolbarBottom=30;
  if(cx==Integer.MIN_VALUE)center();
  int[] cursor={8,6};
  nav("Weltkarte",82,()->claiming=false,cursor);
  nav("Claims",65,()->claiming=true,cursor);
  nav("Zentrieren",94,this::center,cursor);
  nav("Mini AN/AUS",97,V178ClaimsClient::toggleMinimap,cursor);
  nav("+ Wegpunkt",96,()->Minecraft.getInstance().setScreen(
       new V178WaypointEditorScreen(this,centerX(),centerZ())),cursor);
  nav("Wegpunkte",91,()->Minecraft.getInstance().setScreen(
       new V178WaypointManagerScreen(this)),cursor);
  nav("Teams",70,()->Minecraft.getInstance().setScreen(
       new V178ClaimTeamScreen(this)),cursor);
  nav("Team (alt)",87,()->Minecraft.getInstance().setScreen(
       new V178ClaimsTeamScreen(this)),cursor);
  nav("Minimap-Optionen",154,()->Minecraft.getInstance().setScreen(
       new V178MapSettingsScreen(this)),cursor);
  nav("Hilfe",55,()->help=!help,cursor);
  adapt();
 }'''
src=src[:start]+new+src[end:]
# Keep existing M/N/S keyboard shortcuts. Size the map AFTER laying out
# actual buttons, so no controls cover a claimable chunk.
assert "private void adapt(){" in src
assert "private int top(){return (height-DIAMETER*tile())/2;}" in src
src=src.replace(
  "private int top(){return (height-DIAMETER*tile())/2;}",
  "private int top(){return Math.max(toolbarBottom+27,(height-DIAMETER*tile())/2);}",1)
old_adapt='''  DIAMETER=Math.max(5,Math.min(25,
      (Math.min(width,height)-MARGIN)/Math.max(1,zoom)));'''
new_adapt='''  int availableHeight=Math.max(5*zoom,height-toolbarBottom-66);
  int availableWidth=Math.max(5*zoom,width-35);
  DIAMETER=Math.max(5,Math.min(25,
      Math.min(availableHeight,availableWidth)/Math.max(1,zoom)));'''
assert src.count(old_adapt)==1,("B1725_MAP_ADAPT_DRIFT",src.count(old_adapt))
src=src.replace(old_adapt,new_adapt,1)
for token in ('nav("Minimap-Optionen"', 'new V178MapSettingsScreen(this)',
              'nav("Teams"', 'nav("Team (alt)"','nav("Wegpunkte"',
              "toolbarBottom+27"):
    assert token in src,("B1725_MAP_NAV_MISSING",token)
assert '.bounds(Math.max(5,width-82),5,77,20)' not in src
assert '.bounds(347,5,47,20)' not in src
screen.write_text(src,encoding="utf-8")

settings=J/"V178MapSettingsScreen.java"
old_settings=settings.read_text(encoding="utf-8")
for token in ("V178ClaimsClient.toggleOption(key)","V178MiniPreferences::cycleZoom",
              "V178MiniPreferences::cycleCorner","V178MiniPreferences::toggleMobs",
              "V178UiTheme.panel"):
    assert token in old_settings,("B1725_SETTINGS_DRIFT",token)
settings.write_text(r'''package dev.obsidiannetwork.client;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

/** All client-side map preferences, accessible from M -> Minimap-Optionen.
 * Persisted on click by the existing preference classes, with zero IO in draw.
 * No network requests, world scans or server settings required.
 */
public final class V178MapSettingsScreen extends Screen {
 private final Screen previous;
 private int page;
 private static final String[][] KEYS={
  {"minimap","terrain","player"},
  {"claims","loaded","waypoints","coords","chunk","daytime"},
  {"map_terrain","map_claims","map_waypoints","map_player"}
 };
 private static final String[][] LABELS={
  {"Minimap anzeigen","Gelaende","Spielermarker"},
  {"Claims anzeigen","Chunkloading","Wegpunkte","XYZ-Koordinaten",
   "Chunk-Koordinaten","Spieltag"},
  {"Welt-Gelaende","Welt-Claims","Welt-Wegpunkte","Welt-Spieler"}
 };
 public V178MapSettingsScreen(Screen previous){
  super(Component.literal("xSxLabs | Minimap-Einstellungen"));
  this.previous=previous;
 }
 private void refresh(){rebuildWidgets();}
 private void button(int x,int y,int w,String label,Runnable action){
  addRenderableWidget(Button.builder(Component.literal(label),b->{
   action.run();
   refresh();
  }).bounds(x,y,w,20).build());
 }
 private void optionButton(int x,int y,int w,String key,String title){
  button(x,y,w,title+": "+(V178ClaimsClient.option(key)?"AN":"AUS"),
    ()->V178ClaimsClient.toggleOption(key));
 }
 private void option(int left,int top,int w,int index){
  int col=index%2,row=index/2;
  optionButton(left+col*(w+6),top+row*25,w,
      KEYS[page][index],LABELS[page][index]);
 }
 private void display(int left,int top,int w,int index,
                      String label,Runnable toggle){
  int col=index%2,row=index/2;
  button(left+col*(w+6),top+row*25,w,label,toggle);
 }
 @Override protected void init(){
  int w=Math.max(112,Math.min(152,(width-28)/2));
  int left=(width-(2*w+6))/2;
  int top=Math.max(51,(height-210)/2);
  int tab=Math.max(82,(2*w+6-10)/3);
  button(left,top-32,tab,"MINIMAP",()->page=0);
  button(left+tab+5,top-32,tab,"ANZEIGEN",()->page=1);
  button(left+2*(tab+5),top-32,tab,"WELTKARTE",()->page=2);

  for(int i=0;i<KEYS[page].length;i++)option(left,top,w,i);
  if(page==0){
   display(left,top,w,4,"Form: "+V178MiniPreferences.shapeLabel(),
           V178MiniPreferences::toggleShape);
   display(left,top,w,5,"Groesse: "+V178MiniPreferences.sizeLabel(),
           V178MiniPreferences::cycleSize);
   display(left,top,w,6,"Position: "+V178MiniPreferences.positionLabel(),
           V178MiniPreferences::cycleCorner);
   display(left,top,w,7,"Zoom: "+V178MiniPreferences.zoomLabel(),
           V178MiniPreferences::cycleZoom);
  }else if(page==1){
   display(left,top,w,6,"Mobs: "+(V178MiniPreferences.mobs()?"AN":"AUS"),
           V178MiniPreferences::toggleMobs);
   display(left,top,w,7,"Nur Feinde: "+(V178MiniPreferences.hostileOnly()?"AN":"AUS"),
           V178MiniPreferences::toggleHostileOnly);
   display(left,top,w,8,"Mob-Reichweite: "+V178MiniPreferences.mobRangeLabel(),
           V178MiniPreferences::cycleMobRange);
  }
  addRenderableWidget(Button.builder(Component.literal("Zurueck zur Karte"),
      b->onClose()).bounds(left,top+134,2*w+6,20).build());
 }
 @Override public void extractBackground(GuiGraphicsExtractor g,int mx,int my,float delta){
  super.extractBackground(g,mx,my,delta);
  int top=Math.max(51,(height-210)/2);
  int panelWidth=Math.min(width-8,336);
  int left=(width-panelWidth)/2;
  V178UiTheme.panel(g,left,top-48,panelWidth,216);
  g.text(font,"xSxLabs  |  MINIMAP & WELTKARTE",
        left+12,top-44,V178UiTheme.CYAN);
  g.text(font,"Einstellungen werden automatisch gespeichert",
        left+12,top+161,0xffaecdda);
 }
 @Override public void onClose(){Minecraft.getInstance().setScreen(previous);}
 @Override public boolean isPauseScreen(){return false;}
}
''',encoding="utf-8")

assert 'optionButton(left+col*(w+6)' in settings.read_text(encoding="utf-8")
assert "new V178MapSettingsScreen(this)" in screen.read_text(encoding="utf-8")
print("B1725_WORLD_MAP_NON_OVERLAPPING_TOOLBAR_MINIMAP_THREE_TABS_ACCESSIBLE_PASS")
