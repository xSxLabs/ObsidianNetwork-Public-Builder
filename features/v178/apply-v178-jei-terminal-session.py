#!/usr/bin/env python3
"""v1.7.8 AE2-style JEI search session semantics.
Recipe views preserve search; only a fresh Crafting Terminal menu resets it.
No server scans, no recipe re-indexing, no per-frame work or gameplay changes.
"""
import os
from pathlib import Path
root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def rep(rel,old,new):
 p=root/rel
 src=p.read_text(encoding="utf-8")
 assert src.count(old)==1,("V178_JEI_SESSION_SOURCE_DRIFT",rel,old[:120],src.count(old))
 p.write_text(src.replace(old,new,1),encoding="utf-8")

# JEI is optional. This bridge is loaded only with JEI, matching the v177
# pre-existing conditional API; never load classes of an absent optional mod.
rep("client/V177JeiSearchFocusBridge.java",
 ''' static boolean searchFocused(){
  IJeiRuntime active=runtime;
  return active!=null&&active.getIngredientListOverlay().hasKeyboardFocus();
 }
}''',
 ''' static boolean searchFocused(){
  IJeiRuntime active=runtime;
  return active!=null&&active.getIngredientListOverlay().hasKeyboardFocus();
 }
 static String filterText(){
  IJeiRuntime active=runtime;
  return active==null?"":active.getIngredientFilter().getFilterText();
 }
 static void filterText(String text){
  IJeiRuntime active=runtime;
  if(active!=null)active.getIngredientFilter().setFilterText(text);
 }
}''')

rep("client/V177GuiInventoryKeyFocus.java",
 ''' private V177GuiInventoryKeyFocus(){}

 private static final class TextFocus {''',
 ''' private V177GuiInventoryKeyFocus(){}

 // V178_JEI_SESSION: recipe view and JEI uses pages are NOT terminal exits.
 // Only one short query string is cached. No off-thread global state.
 private static Object xsxTerminalMenu=null;
 private static String xsxJeiQuery="";
 private static boolean xsxTerminalVisible=false;
 private static boolean xsxJeiAvailable(){
  return net.neoforged.fml.ModList.get().isLoaded("jei");
 }

 @SubscribeEvent
 public static void xsxTerminalOpening(ScreenEvent.Opening event){
  Minecraft mc=Minecraft.getInstance();
  // Capture the last keystroke even if JEI opens immediately this frame.
  if(mc.screen instanceof StorageTerminalScreen oldScreen
       &&oldScreen.getMenu()==xsxTerminalMenu&&xsxJeiAvailable())
   xsxJeiQuery=V177JeiSearchFocusBridge.filterText();
  if(!(event.getNewScreen() instanceof StorageTerminalScreen terminal))return;
  Object menu=terminal.getMenu();
  if(menu==xsxTerminalMenu&&menu!=null){
   // Same menu instance: return from JEI recipe/uses, preserve typed filter.
   if(xsxJeiAvailable())V177JeiSearchFocusBridge.filterText(xsxJeiQuery);
  }else{
   // Different menu instance: terminal really closed and reopened.
   xsxTerminalMenu=menu;
   xsxJeiQuery="";
   if(xsxJeiAvailable())V177JeiSearchFocusBridge.filterText("");
  }
 }

 @SubscribeEvent
 public static void xsxTerminalTick(net.neoforged.neoforge.client.event.ClientTickEvent.Post event){
  var mc=Minecraft.getInstance();
  if(mc.player==null){
   xsxTerminalMenu=null;xsxJeiQuery="";xsxTerminalVisible=false;
   return;
  }
  boolean terminal=mc.screen instanceof StorageTerminalScreen screen
      &&screen.getMenu()==xsxTerminalMenu;
  if(terminal&&xsxTerminalMenu!=null&&xsxJeiAvailable()){
   // Restore once when returning from a JEI recipe Screen. Updates while
   // the terminal is visible never call setFilterText (no GUI redraw loops).
   if(!xsxTerminalVisible)
    V177JeiSearchFocusBridge.filterText(xsxJeiQuery);
   xsxJeiQuery=V177JeiSearchFocusBridge.filterText();
  }
  xsxTerminalVisible=terminal;
 }

 private static final class TextFocus {''')
print("V178_JEI_RECIPE_SEARCH_PRESERVE_NEW_MENU_RESET_PASS")
