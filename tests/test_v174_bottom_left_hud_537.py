#!/usr/bin/env python3
"""B539: B121 violet FE and B533 paste HUD; bottom-left placement gates."""
import os,subprocess,sys,tempfile,unittest
from pathlib import Path
SCRIPT=Path(__file__).resolve().parents[1]/"features/v174/apply-v174-bottom-left-hud-537.py"
SOURCE='''public class PowerArmorBuild98Client {
 void hud(){
  // BUILD121_UNFRAMED_VIOLET_FE_HUD
  int x=mc.getWindow().getGuiScaledWidth()/2+10;
  int y=mc.getWindow().getGuiScaledHeight()-52;
  g.text(mc.font,"ARMOR FE",x+2,y-1,0xffb9d6df);
  // B533_NUTRIPASTE_ARMOR_ROW
  int pasteWidth=70,px=mc.getWindow().getGuiScaledWidth()/2-91;
  int py=mc.getWindow().getGuiScaledHeight()-66;
  String pasteLabel="PASTE "+pastePct+"%";
  g.fill(px,py+10,px+pasteWidth,py+12,0x88435855);
 }
}'''
class BottomLeftHUDTest(unittest.TestCase):
 def setUp(self):
  tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
  self.root=Path(tmp.name)
  self.hud=self.root/"dev/obsidiannetwork/client/PowerArmorBuild98Client.java"
  self.hud.parent.mkdir(parents=True)
  self.hud.write_text(SOURCE,encoding="utf-8")
 def run_script(self):
  return subprocess.run([sys.executable,str(SCRIPT)],
     env=dict(os.environ,V1_SOURCE_ROOT=str(self.root)),
     text=True,capture_output=True)
 def test_fe_paste_two_rows_and_no_background(self):
  r=self.run_script();self.assertEqual(r.returncode,0,r.stderr)
  result=self.hud.read_text()
  self.assertIn("int x=8; // B537_HUD_BOTTOM_LEFT_FE",result)
  self.assertIn("int pasteWidth=80,px=8; // B537_HUD_BOTTOM_LEFT_PASTE",result)
  self.assertIn("getGuiScaledHeight()-61",result)
  self.assertIn("getGuiScaledHeight()-85",result)
  self.assertNotIn("0x9b101923",result)
  self.assertIn('g.text(mc.font,"ARMOR FE"',result)
  self.assertIn('String pasteLabel="PASTE "+pastePct+"%";',result)
 def test_breaking_original_hud_is_detected(self):
  self.hud.write_text(SOURCE.replace("getGuiScaledWidth()/2+10","getGuiScaledWidth()/2+20"))
  r=self.run_script();self.assertNotEqual(r.returncode,0)
  self.assertIn("B537_HUD_POSITION_SOURCE_DRIFT",r.stderr)
 def test_repeating_patch_does_not_double_apply(self):
  r=self.run_script();self.assertEqual(r.returncode,0,r.stderr)
  again=self.run_script();self.assertNotEqual(again.returncode,0)
  self.assertIn("B537_ALREADY_APPLIED",again.stderr)
if __name__=="__main__":unittest.main()
