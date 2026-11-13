#!/usr/bin/env python3
"""JARVIS per-player voice queue and preferences regression."""
import ast
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
VOICE=(ROOT/"features/v177/apply-v177-jarvis-voice.py").read_text(encoding="utf-8")
FLOW=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")

class PlayerJarvisVoiceRecovery(unittest.TestCase):
 def test_player_only_reset_button_and_queued_voice_test(self):
  ast.parse(VOICE)
  self.assertIn('resolve("xsxlabs-jarvis-"+(owner==null?"default":owner)+".properties")',VOICE)
  self.assertIn('public static void restoreVoiceDefaults()',VOICE)
  self.assertIn('for(String key:switches.keySet())switches.put(key,true);',VOICE)
  self.assertIn('button(x,y+23,238,"RESET MY VOICE OPTIONS"',VOICE)
  self.assertIn('button(x,y,238,"TEST QUEUED VOICE"',VOICE)
  self.assertIn('if(page==0&&subpage==3)',VOICE)
  self.assertIn('V177JarvisClient::testQueue',VOICE)
  self.assertIn('V177JarvisSettings::restoreVoiceDefaults',VOICE)

 def test_audio_failure_does_not_starve_queue_or_persist_after_reentry(self):
  self.assertIn('private static boolean speak(String text)',VOICE)
  self.assertIn('return V177JarvisAudio.enqueue(text,V177JarvisSettings.german,V177JarvisSettings.volume);',VOICE)
  self.assertIn('if(speak(line))nextTalk=p.tickCount+Math.max(50,line.split(',VOICE)
  self.assertIn('else nextTalk=p.tickCount+1;',VOICE)
  self.assertIn('messages.clear();nextTalk=0;initial=true;return;',VOICE)
  self.assertIn('wasInArmor=true;messages.clear();nextTalk=0;',VOICE)
  self.assertIn('wasInArmor=false;messages.clear();nextTalk=0;lastTick=Integer.MIN_VALUE;',VOICE)
  self.assertIn('enqueue(4,"Attack mode activated."',VOICE)
  self.assertIn('enqueue(4,"Attack mode deactivated."',VOICE)
  self.assertIn('enqueue(5,"At your service, sir."',VOICE)

 def test_ci_integration(self):
  self.assertIn('test_v177_jarvis_player_voice_recovery.py',FLOW)
  self.assertIn('cancel-in-progress: true',FLOW)

if __name__=="__main__":
 unittest.main()
