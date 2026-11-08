#!/usr/bin/env python3
"""v1.7.7: inventory key closes only when a mod GUI text field is not focused.

One client-only NeoForge listener covers every xSxLabs screen (including GUIs
generated from earlier branches); no invasive per-screen overrides. The key
press is consumed while text entry is active, but Minecraft's separate
CharacterTyped callback still inserts 'e' into the focused edit box.
"""
import os
from pathlib import Path

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
target=root/"client/V177GuiInventoryKeyFocus.java"
assert not target.exists(),"V177_GUI_E_ALREADY_PRESENT"
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
 * All xSxLabs GUIs with text fields:
 * - focused EditBox / MultiLineEditBox: E is TEXT, never closes the screen
 * - no focused text field: the inventory key closes the GUI as normal.
 *
 * Only a single key event triggers this (no client/server tick, no network).
 * Does not affect vanilla, other mods, ESC, or other key mappings.
 */
@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)
public final class V177GuiInventoryKeyFocus {
 private V177GuiInventoryKeyFocus(){}

 private static final class TextFocus {
  boolean hasField;
  boolean isEditing;
 }

 private static void inspect(ContainerEventHandler root,TextFocus state,
                             java.util.IdentityHashMap<GuiEventListener,Boolean> seen,
                             int depth) {
  if(depth>8||seen.size()>256)return; // bounded on arbitrarily nested UIs
  for(GuiEventListener child:root.children()){
   if(seen.put(child,Boolean.TRUE)!=null)continue;
   if(child instanceof EditBox box){
    state.hasField=true;
    if(box.isFocused()&&box.isActive())state.isEditing=true;
   }else if(child instanceof MultiLineEditBox box){
    state.hasField=true;
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
   return; // never interfere with third-party or vanilla screens
  Minecraft mc=Minecraft.getInstance();
  if(mc.screen!=screen||!mc.options.keyInventory.matches(event.getKeyEvent()))return;
  TextFocus state=new TextFocus();
  inspect(screen,state,new java.util.IdentityHashMap<>(),0);
  if(!state.hasField)return; // non-text GUIs keep their existing semantics
  if(state.isEditing){
   // NeoForge KeyPressed.Pre stops inventory-close handling. The separate
   // CharacterTyped event still routes 'e' to the focused edit widget.
   event.setCanceled(true);
  }else{
   event.setCanceled(true); // avoid double-closing or menu side effects
   screen.onClose();
  }
 }
}
''',encoding="utf-8")
print("V177_GLOBAL_MOD_GUI_E_FOCUSED_TEXT_INPUT_INSTALLED")
