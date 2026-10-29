#!/usr/bin/env python3
"""Build351: real projection size and action-wheel Vision feedback.

Strict visual-only patch after Build348; no saved data, network, FE or block edits.
"""
import os
from pathlib import Path

J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
render=J/"client/V173WorldGhostRenderer.java"
s=render.read_text(encoding="utf-8")
old='''  double scale=Math.max(.045D,Math.min(1D,be.holoWidth()/Math.max(dx,Math.max(dy,dz))));'''
new='''  // V173_B351_EXACT_NETWORK_SIZE: selected SIZE is the longest 3D extent.
  // No max-1 ceiling: small networks MUST grow when the player selects SIZE 8/16/32.
  // X, Y and Z share one scale so a cable junction cannot become stretched.
  double scale=(double)Math.max(1,be.holoWidth())/
        Math.max(1D,Math.max(dx,Math.max(dy,dz)));'''
assert s.count(old)==1,("V173_B351_SCALE_DRIFT",s.count(old))
render.write_text(s.replace(old,new,1),encoding="utf-8")

vision=J/"client/NetworkVisionClient.java"
s=vision.read_text(encoding="utf-8")
old=''' public static void toggleFromWheel(){
  if(!ready()){enabled=false;return;}
  enabled=!enabled;
 }'''
new=''' // V173_B351_VISION_FEEDBACK: the action wheel is the only Vision toggle.
 public static void toggleFromWheel(){
  var mc=Minecraft.getInstance();
  if(!ready()){
   enabled=false;
   if(mc.player!=null)
    mc.player.sendOverlayMessage(net.minecraft.network.chat.Component.literal(
      installed()?"Network Vision: charge and wear a complete armor set":
        "Network Vision: upgrade not installed"));
   return;
  }
  enabled=!enabled;
  if(mc.player!=null)
   mc.player.sendOverlayMessage(net.minecraft.network.chat.Component.literal(
       enabled?"Network Vision: ON":"Network Vision: OFF"));
 }'''
assert s.count(old)==1,("V173_B351_VISION_TOGGLE_DRIFT",s.count(old))
vision.write_text(s.replace(old,new,1),encoding="utf-8")

assert "V173_B351_EXACT_NETWORK_SIZE" in render.read_text(encoding="utf-8")
assert "V173_B351_VISION_FEEDBACK" in vision.read_text(encoding="utf-8")
print("V173_B351_SCALE_AND_WHEEL_FEEDBACK_PASS")
