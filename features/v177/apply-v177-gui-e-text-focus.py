#!/usr/bin/env python3
"""v1.7.7: E closes xSxLabs GUIs unless an xSxLabs or JEI search field is focused.

JEI draws its search bar as an independent overlay, outside Screen.children().
Register a tiny optional JEI plugin for the public IIngredientListOverlay.hasKeyboardFocus()
API; never reflect into JEI internals or require JEI at runtime. KeyPressed.Pre
stops GUI closing but leaves CharacterTyped events to whichever editor owns focus.
"""
import os
from pathlib import Path

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
target=root/"client/V177GuiInventoryKeyFocus.java"
bridge=root/"client/V177JeiSearchFocusBridge.java"
assert not target.exists(),"V177_GUI_E_ALREADY_PRESENT"
assert not bridge.exists(),"V177_JEI_FOCUS_BRIDGE_ALREADY_PRESENT"
target.parent.mkdir(parents=True,exist_ok=True)
target.write_text(r'''package dev.obsidiannetwork.client;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.components.MultiLineEditBox;
import net.minecraft.client.gui.components.events.ContainerEventHandler;
import net.minecraft.client.gui.components.events.GuiEventListener;
import net.minecraft.client.gui.screens.Screen;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ScreenEvent;

/**
 * xSxLabs screens:
 * - focused xSxLabs text field: E types into the editor, no GUI close
 * - focused JEI overlay search: E types into JEI, no GUI close
 * - neither field focused: E closes the GUI, even without local text fields.
 *
 * No polling, packets, reflection, or changes to other mods' inventory screens.
 */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class V177GuiInventoryKeyFocus {
 private V177GuiInventoryKeyFocus(){}

 private static final class TextFocus {
  boolean isEditing;
 }

 private static void inspect(ContainerEventHandler root,TextFocus state,
                             java.util.IdentityHashMap<GuiEventListener,Boolean> seen,
                             int depth) {
  if(depth>8||seen.size()>256)return; // bounded on arbitrarily nested UIs
  for(GuiEventListener child:root.children()){
   if(seen.put(child,Boolean.TRUE)!=null)continue;
   if(child instanceof EditBox box){
    if(box.isFocused()&&box.isActive())state.isEditing=true;
   }else if(child instanceof MultiLineEditBox box){
    if(box.isFocused()&&box.isActive())state.isEditing=true;
   }
   if(child instanceof ContainerEventHandler nested)
    inspect(nested,state,seen,depth+1);
  }
 }

 @SubscribeEvent
 public static void inventoryKey(ScreenEvent.KeyPressed.Pre event){
  Screen screen=event.getScreen();
  if(screen==null||!screen.getClass().getName().startsWith("dev.obsidiannetwork."))
   return; // never alter vanilla or third-party screen semantics
  Minecraft mc=Minecraft.getInstance();
  if(mc.screen!=screen||!mc.options.keyInventory.matches(event.getKeyEvent()))return;
  TextFocus state=new TextFocus();
  inspect(screen,state,new java.util.IdentityHashMap<>(),0);

  // JEI's search widget does not belong to Screen.children(), so check the
  // official optional JEI runtime API, which reports the visible search focus.
  boolean jeiEditing=net.neoforged.fml.ModList.get().isLoaded("jei")
      &&V177JeiSearchFocusBridge.searchFocused();
  if(state.isEditing||jeiEditing){
   // Consume the inventory-close key; CharacterTyped still reaches the
   // focused xSxLabs or JEI text widget on its own input event.
   event.setCanceled(true);
   return;
  }
  event.setCanceled(true); // one close; never double-dispatch the inventory key
  screen.onClose();
 }
}
''',encoding="utf-8")

# Compiled against optional JEI API only; JEI discovers this @JeiPlugin only
# when installed. No JEI-specific type is referenced by the always-loaded
# listener unless the ModList guard reports that JEI is installed.
bridge.write_text(r'''package dev.obsidiannetwork.client;

import mezz.jei.api.IModPlugin;
import mezz.jei.api.JeiPlugin;
import mezz.jei.api.runtime.IJeiRuntime;
import net.minecraft.resources.Identifier;

/** Optional JEI runtime focus bridge; never required to load the mod. */
@JeiPlugin
public final class V177JeiSearchFocusBridge implements IModPlugin {
 private static volatile IJeiRuntime runtime;

 @Override public Identifier getPluginUid(){
  return Identifier.fromNamespaceAndPath("obsidiannetwork","v177_jei_search_focus");
 }

 @Override public void onRuntimeAvailable(IJeiRuntime available){
  runtime=available;
 }

 @Override public void onRuntimeUnavailable(){
  runtime=null; // do not hold the old JEI UI across world changes
 }

 static boolean searchFocused(){
  IJeiRuntime active=runtime;
  return active!=null&&active.getIngredientListOverlay().hasKeyboardFocus();
 }
}
''',encoding="utf-8")
print("V177_GLOBAL_GUI_E_JEI_SEARCH_FOCUS_BRIDGE_INSTALLED")
