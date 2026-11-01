#!/usr/bin/env python3
"""B670 regression fixture: reconstructed 26.1 source uses TWO leading spaces.
Test B668 patch against the real reconstructed exact textual anchors, before
waiting for the long mod reconstruction on subsequent v1.7.6 builds.
"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/"features/v176/apply-v176-attack-wheel-668.py"
WHEEL=r'''package dev.obsidiannetwork.client;
public final class NetworkActionWheelClient {
 private static void activate(int action){
  switch(action){
     case 4->NetworkVisionClient.toggleFromWheel();
  }
 }
 private static int wheelSector(double dx,double dy,boolean vision){
  if(!vision)return Math.abs(dx)>Math.abs(dy)?(dx>0?1:3):(dy>0?2:0);
  int slice=0;
  return switch(slice){case 0->0;case 1->1;case 2->4;case 3->2;default->3;};
 }
 @SubscribeEvent public static void register(RegisterKeyMappingsEvent e){e.register(WHEEL);}
 @SubscribeEvent public static void tick(ClientTickEvent.Post e){
  selected=distance<28||distance>103?-1:
     wheelSector(dx,dy,NetworkVisionClient.installed());
 }
 @SubscribeEvent public static void render(RenderGuiEvent.Post e){
  boolean hasVision=NetworkVisionClient.installed();
  int wedge=radius2<28*28?-1:wheelSector(start,yy,hasVision);
  int next=nextR2<28*28?-1:wheelSector(stop,yy,hasVision);
  int[] order=hasVision?new int[]{0,1,4,2,3}:new int[]{0,1,2,3};
  String name=i==4?"VISION":ACTIONS[i];
 }
}
'''
class B670(unittest.TestCase):
 def test_source_reconstruction_indent_and_wheel_stability(self):
  with tempfile.TemporaryDirectory() as tmp:
   J=Path(tmp)/"dev/obsidiannetwork"
   for rel,src in {
    "powerarmor/PowerArmorCommands.java":
      '   .then(Commands.literal("nightvision").executes(c->night(c.getSource().getPlayerOrException()))));\n',
    "powerarmor/PowerArmorRuntime.java":
      '  if(!(event.getEntity() instanceof ServerPlayer p))return;\n  if(p.tickCount%5!=0)return;\n',
    "powerarmor/PowerArmorSuitWorld.java":
      '  for(EquipmentSlot slot:PowerArmorRuntime.SLOTS)worn.add(player.getItemBySlot(slot).copy());\n',
    "client/NetworkActionWheelClient.java":WHEEL,
   }.items():
    file=J/rel
    file.parent.mkdir(parents=True,exist_ok=True)
    file.write_text(src,encoding="utf-8")
   env={**os.environ,"V1_SOURCE_ROOT":str(Path(tmp))}
   r=subprocess.run([sys.executable,str(SCRIPT)],env=env,text=True,capture_output=True)
   self.assertEqual(r.returncode,0,r.stdout+r.stderr)
   self.assertIn("V176_B668_MODULE_ONLY_RADIAL_ATTACK_TOGGLE_SYNCED_ACTIONBAR_PASS",r.stdout)
   wheel=(J/"client/NetworkActionWheelClient.java").read_text()
   self.assertIn("if(vision&&attack)return new int[]{0,1,4,5,2,3};",wheel)
   self.assertIn("if(vision)return new int[]{0,1,4,2,3};",wheel)
   self.assertIn("if(attack)return new int[]{0,1,5,2,3};",wheel)
   self.assertIn("return new int[]{0,1,2,3};",wheel)
   self.assertIn("case 5->V176AttackModeClient.toggleFromWheel();",wheel)
   self.assertIn("V176AttackModeServer.maintain(p);",(J/"powerarmor/PowerArmorRuntime.java").read_text())
   self.assertIn("V176AttackModeServer.clearFromChest(worn.get(1));",(J/"powerarmor/PowerArmorSuitWorld.java").read_text())
   self.assertIn('Commands.literal("attack")',(J/"powerarmor/PowerArmorCommands.java").read_text())
   self.assertTrue((J/"powerarmor/V176AttackModeServer.java").is_file())
   self.assertTrue((J/"client/V176AttackModeClient.java").is_file())
   again=subprocess.run([sys.executable,str(SCRIPT)],env=env,text=True,capture_output=True)
   self.assertNotEqual(again.returncode,0,"fail-closed duplicate patch must be rejected")
if __name__=="__main__": unittest.main()
