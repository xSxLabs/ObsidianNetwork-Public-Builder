#!/usr/bin/env python3
"""B1716: configurable GPU-atlas minimap, dedicated controls category and GUI.

Runs AFTER the B1715 visual overlay on the generated 1.7.8 source.
All options are local per-client properties; no new network packets, ticks,
server-world queries, dynamic rendering work or keycode overrides.
"""
import json
import os
import re
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
R=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"

def patch(rel,old,new):
    p=J/rel
    s=p.read_text(encoding="utf-8")
    assert s.count(old)==1,("B1716_ANCHOR_DRIFT",rel,old[:90],s.count(old))
    p.write_text(s.replace(old,new,1),encoding="utf-8")

# Keep the existing persisted set of options and add real zoom (7/5/3 chunk
# viewport) and configurable Mob range (32/64/96/128 blocks).
pref="client/V178MiniPreferences.java"
patch(pref,"private static int size=1,corner=-1;",
      "private static int size=1,corner=-1,zoom=0,mobRange=2;")
patch(pref,'   corner=Integer.parseInt(p.getProperty("corner","-1"));',
      '''   corner=Integer.parseInt(p.getProperty("corner","-1"));
   zoom=Integer.parseInt(p.getProperty("zoom","0"));
   mobRange=Integer.parseInt(p.getProperty("mobRange","2"));''')
patch(pref,'   if(corner< -1||corner>3)corner=-1;',
      '''   if(corner< -1||corner>3)corner=-1;
   if(zoom<0||zoom>2)zoom=0;
   if(mobRange<0||mobRange>3)mobRange=2;''')
patch(pref,'    p.setProperty("corner",Integer.toString(corner));',
      '''    p.setProperty("corner",Integer.toString(corner));
    p.setProperty("zoom",Integer.toString(zoom));
    p.setProperty("mobRange",Integer.toString(mobRange));''')
patch(pref,' public static int corner(){ensure();return corner;}',
      ''' public static int corner(){ensure();return corner;}
 public static int visibleChunks(){ensure();return switch(zoom){
   case 1->5;case 2->3;default->7;
 };}
 public static String zoomLabel(){return visibleChunks()+"x"+visibleChunks()+" chunks";}
 public static void cycleZoom(){ensure();zoom=(zoom+1)%3;save();}
 public static int mobRange(){ensure();return switch(mobRange){
   case 0->32;case 1->64;case 3->128;default->96;
 };}
 public static String mobRangeLabel(){return mobRange()+" blocks";}
 public static void cycleMobRange(){ensure();mobRange=(mobRange+1)%4;save();}''')
patch(pref,'  return !circle()||dx*dx+dz*dz<=10;',
      '''  int radius=visibleChunks()/2;
  return !circle()||dx*dx+dz*dz<=radius*radius+1;''')

# B1700 already cached the entire 7x7 world around the player in the GPU.
# Zoom crops this EXISTING texture, not a larger CPU render or extra uploads.
terrain="client/V178TerrainMap.java"
patch(terrain,'''   g.blit(net.minecraft.client.renderer.RenderPipelines.GUI_TEXTURED,
        id,ox,oy,0.0f,0.0f,width,width,side,side,side,side);''',
'''   int source=diameter==7 ? V178MiniPreferences.visibleChunks()*RES : side;
   int crop=(side-source)/2;
   g.blit(net.minecraft.client.renderer.RenderPipelines.GUI_TEXTURED,
        id,ox,oy,(float)crop,(float)crop,width,width,source,source,side,side);''')

# Use one consistent view size for terrain, claims and player marker.
mini="client/V178ClaimsClient.java"
patch(mini,'''  int step=V178MiniPreferences.step();
  int miniWidth=7*step+7,miniHeight=7*step+20+infoRows*10,miniCorner=1;''',
'''  int step=V178MiniPreferences.step();
  int view=V178MiniPreferences.visibleChunks(),radius=view/2;
  int markerStep=7*step/view;
  int miniWidth=7*step+7,miniHeight=7*step+20+infoRows*10,miniCorner=1;''')
patch(mini,'''   for(int dz=-3;dz<=3;dz++)for(int dx=-3;dx<=3;dx++){
     if(!V178MiniPreferences.visible(dx,dz))continue;
     int x=ox+4+(dx+3)*step,y=oy+15+(dz+3)*step;''',
'''   for(int dz=-radius;dz<=radius;dz++)for(int dx=-radius;dx<=radius;dx++){
     if(!V178MiniPreferences.visible(dx,dz))continue;
     int x=ox+4+(dx+radius)*markerStep,y=oy+15+(dz+radius)*markerStep;''')
patch(mini,'''else g.fill(x,y,x+step,y+step,0xff1c2530);''',
      '''else g.fill(x,y,x+markerStep,y+markerStep,0xff1c2530);''')
patch(mini,'''if(drawClaims)V178TerrainMap.drawClaim(g,x,y,step,''',
      '''if(drawClaims)V178TerrainMap.drawClaim(g,x,y,markerStep,''')
patch(mini,'''g.fill(x+step-4,y+step-4,x+step-1,y+step-1,0xff66ee71);''',
      '''g.fill(x+markerStep-4,y+markerStep-4,x+markerStep-1,y+markerStep-1,0xff66ee71);''')
patch(mini,'''int px=ox+4+3*step+Math.floorMod(mc.player.blockPosition().getX(),16)*step/16;
     int py=oy+15+3*step+Math.floorMod(mc.player.blockPosition().getZ(),16)*step/16;''',
'''int px=ox+4+radius*markerStep+
         Math.floorMod(mc.player.blockPosition().getX(),16)*markerStep/16;
     int py=oy+15+radius*markerStep+
         Math.floorMod(mc.player.blockPosition().getZ(),16)*markerStep/16;''')

# Mob and waypoint icons must share the cropped terrain grid, not the original
# fixed 7x7 coordinates. Mob scanning retains the 10-tick throttle and 48 cap.
mob="client/V178MapMobCache.java"
patch(mob,'''mc.player.getBoundingBox().inflate(96),''',
      '''mc.player.getBoundingBox().inflate(V178MiniPreferences.mobRange()),''')
patch(mob,'''   if(dx< -3||dx>3||dz< -3||dz>3||!V178MiniPreferences.visible(dx,dz))continue;
   int x=left+(dx+3)*step+Math.floorMod(m.x(),16)*step/16;
   int y=top+(dz+3)*step+Math.floorMod(m.z(),16)*step/16;''',
'''   int r=V178MiniPreferences.visibleChunks()/2;
   if(dx< -r||dx>r||dz< -r||dz>r||!V178MiniPreferences.visible(dx,dz))continue;
   int tile=7*step/(2*r+1);
   int x=left+(dx+r)*tile+Math.floorMod(m.x(),16)*tile/16;
   int y=top+(dz+r)*tile+Math.floorMod(m.z(),16)*tile/16;''')
way="client/V178Waypoints.java"
patch(way,'''   if(!V178MiniPreferences.visible(dx,dz))continue;
   int x=ox+(dx+3)*step+step/2,y=oy+(dz+3)*step+step/2;''',
'''   int r=V178MiniPreferences.visibleChunks()/2;
   if(dx< -r||dx>r||dz< -r||dz>r||!V178MiniPreferences.visible(dx,dz))continue;
   int tile=7*step/(2*r+1);
   int x=ox+(dx+r)*tile+tile/2,y=oy+(dz+r)*tile+tile/2;''')

# Replace the cramped two-column screen by three purpose-specific tabs.
# All original persisted booleans and options are still editable.
settings=J/"client/V178MapSettingsScreen.java"
assert settings.exists() and 'V178ClaimsClient.toggleOption(key)' in settings.read_text()
settings.write_text(r'''package dev.obsidiannetwork.client;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

/** xSxLabs minimap/world map – every toggle is saved on click. */
public final class V178MapSettingsScreen extends Screen {
 private final Screen previous;
 private int page=0;
 private static final String[][] KEYS={
  {"minimap","terrain","claims","loaded","waypoints","player","coords","chunk","daytime"},
  {"map_terrain","map_claims","map_waypoints","map_player"},
 };
 private static final String[][] LABELS={
  {"Minimap Visible","Terrain","Claim Borders","Chunk Loading",
   "Waypoints","Player Arrow","XYZ Coordinates","Chunk Coordinates","Game Day"},
  {"World Terrain","World Claims","World Waypoints","World Player"}
 };
 public V178MapSettingsScreen(Screen previous){
  super(Component.literal("xSxLabs | Minimap Settings"));
  this.previous=previous;
 }
 private void refresh(){rebuildWidgets();}
 private void button(int x,int y,String label,Runnable action){
  addRenderableWidget(Button.builder(Component.literal(label),b->{
   action.run();refresh();
  }).bounds(x,y,152,20).build());
 }
 private void optionButton(int x,int y,String key,String title){
  button(x,y,title+": "+(V178ClaimsClient.option(key)?"ON":"OFF"),
         ()->V178ClaimsClient.toggleOption(key));
 }
 @Override protected void init(){
  int left=width/2-156,top=Math.max(17,height/2-109);
  button(left,top-25,"MINIMAP",()->page=0);
  button(left+158,top-25,"WORLD MAP",()->page=1);
  if(page==0){
   for(int i=0;i<KEYS[0].length;i++){
    int col=i%2,row=i/2;
    optionButton(left+col*158,top+row*23,KEYS[0][i],LABELS[0][i]);
   }
   int base=top+120;
   button(left,base,"Shape: "+V178MiniPreferences.shapeLabel(),V178MiniPreferences::toggleShape);
   button(left+158,base,"Size: "+V178MiniPreferences.sizeLabel(),V178MiniPreferences::cycleSize);
   button(left,base+23,"Position: "+V178MiniPreferences.positionLabel(),V178MiniPreferences::cycleCorner);
   button(left+158,base+23,"Zoom: "+V178MiniPreferences.zoomLabel(),V178MiniPreferences::cycleZoom);
   button(left,base+46,"Show Mobs: "+(V178MiniPreferences.mobs()?"ON":"OFF"),V178MiniPreferences::toggleMobs);
   button(left+158,base+46,"Hostile Only: "+(V178MiniPreferences.hostileOnly()?"ON":"OFF"),V178MiniPreferences::toggleHostileOnly);
   button(left,base+69,"Mob Range: "+V178MiniPreferences.mobRangeLabel(),V178MiniPreferences::cycleMobRange);
  }else{
   for(int i=0;i<KEYS[1].length;i++){
    int col=i%2,row=i/2;
    optionButton(left+col*158,top+row*23,KEYS[1][i],LABELS[1][i]);
   }
  }
  button(left+158,top+207,"DONE / BACK",this::onClose);
 }
 @Override public void extractBackground(GuiGraphicsExtractor g,int mx,int my,float delta){
  super.extractBackground(g,mx,my,delta);
  int y=Math.max(17,height/2-109);
  V178UiTheme.panel(g,width/2-166,y-55,332,291);
  g.text(font,page==0?"MINIMAP + INFO / DISPLAY":"WORLD MAP / LAYERS",
         width/2-153,y-43,V178UiTheme.CYAN);
 }
 @Override public void onClose(){Minecraft.getInstance().setScreen(previous);}
 @Override public boolean isPauseScreen(){return false;}
}
''',encoding="utf-8")

# Put every xSxLabs KeyMapping in one category. Preserve every original
# translation key, default key, event subscriber and consumeClick handler.
# Register the category through NeoForge's MOD-BUS event (26.1 API).
category=J/"client/V178KeybindCategory.java"
assert not category.exists(),"B1716_CATEGORY_DUPLICATE"
# B964 already registers obsidiannetwork:network_storage once. Creating
# a second Category and registering it crashes the client on startup.
# Reuse the exact established CATEGORY instance for every mapped key.
category.write_text(r'''package dev.obsidiannetwork.client;

import net.minecraft.client.KeyMapping;

public final class V178KeybindCategory {
 private V178KeybindCategory(){}
 public static final KeyMapping.Category XSXLABS =
     dev.obsidiannetwork.powerarmor.PowerArmorExitKeyClient.CATEGORY;
}
''',encoding="utf-8")
mappingfiles=[]
for p in J.rglob("*.java"):
    if p==category:continue
    s=p.read_text(encoding="utf-8")
    if "new KeyMapping(" not in s and "new net.minecraft.client.KeyMapping(" not in s:
        continue
    # Only existing KeyMapping.Category tokens; never change arbitrary
    # gameplay category variables or components.
    pattern=r'(?:(?:net\.minecraft\.client\.)?KeyMapping)\.Category\.(?:MISC|GAMEPLAY|INVENTORY|MULTIPLAYER|CREATIVE|MOVEMENT|UI)'
    updated,n=re.subn(pattern,"dev.obsidiannetwork.client.V178KeybindCategory.XSXLABS",s)
    if n:
        p.write_text(updated,encoding="utf-8")
        mappingfiles.append((str(p.relative_to(J)),n))
assert mappingfiles and sum(n for _,n in mappingfiles)>=3,("B1716_NO_MAPPING_REASSIGNMENT",mappingfiles)
# N & M already work; add direct configurable minimap settings shortcut,
# UNBOUND by default to avoid stealing existing keyboard combinations.
client=J/"client/V178ClaimsClient.java"
s=client.read_text(encoding="utf-8")
needle='''  @SubscribeEvent public static void bindings(RegisterKeyMappingsEvent event){'''
assert s.count(needle)==1,"B1716_BINDINGS_REGISTER_DRIFT"
s=s.replace(needle,'''  private static final KeyMapping MINIMAP_SETTINGS=new KeyMapping(
    "key.obsidiannetwork.minimap_settings",InputConstants.Type.KEYSYM,
    GLFW.GLFW_KEY_UNKNOWN,V178KeybindCategory.XSXLABS);
'''+needle,1)
needle='''   event.register(TOGGLE_MINIMAP);'''
assert s.count(needle)==1,"B1716_BINDINGS_TOGGLE_DRIFT"
s=s.replace(needle,needle+'''
   event.register(MINIMAP_SETTINGS);''',1)
needle='''  while(TOGGLE_MINIMAP.consumeClick())toggleMinimap();'''
assert s.count(needle)==1,"B1716_MINIMAP_KEY_DRIFT"
s=s.replace(needle,needle+'''
  while(MINIMAP_SETTINGS.consumeClick()){
   if(mc.screen==null&&mc.level!=null)
    mc.setScreen(new V178MapSettingsScreen(null));
  }''',1)
client.write_text(s,encoding="utf-8")

# Translation keys used by vanilla Controls screen and the new direct bind.
for language,display in (("en_us","xSxLabs Network Storage"),
                         ("de_de","xSxLabs Network Storage")):
    path=R/("lang/"+language+".json")
    content=json.loads(path.read_text(encoding="utf-8"))
    content["key.category.obsidiannetwork.network_storage"]=display
    content["key.obsidiannetwork.minimap_settings"] = (
      "Open Minimap Settings" if language=="en_us" else "Minimap-Einstellungen öffnen")
    path.write_text(json.dumps(content,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

# Source-only contracts; no extra render loops, no new network payloads.
assert "V178MiniPreferences.visibleChunks()" in (J/terrain).read_text()
assert "PowerArmorExitKeyClient.CATEGORY" in category.read_text()
assert "registerCategory(" not in category.read_text()
assert 'MINIMAP_SETTINGS.consumeClick()' in client.read_text()
assert "V178ClaimsClient.toggleOption(key)" in settings.read_text()
print("B1716_MINIMAP_ALL_SETTINGS_PERSISTED_GPU_CROP_ZOOM_MOB_RANGE_PASS",
      "KEYBINDS_GROUPED",mappingfiles)
