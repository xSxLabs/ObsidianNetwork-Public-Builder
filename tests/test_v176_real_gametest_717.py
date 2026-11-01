#!/usr/bin/env python3
"""B717 fast anchor regression before long Minecraft 26.1 build."""
import os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NETWORK=ROOT/"features/v176/apply-v176-test-feedback-717.py"
GAME=ROOT/"features/v176/inject-v176-real-gametest-717.py"

class LiveWeaponTestWiring(unittest.TestCase):
 def test_fake_player_feedback_and_real_game_fixture(self):
  with tempfile.TemporaryDirectory() as tmp:
   J=Path(tmp)/"dev/obsidiannetwork"
   fixtures={
    "powerarmor/V176AttackModeServer.java":
      '  p.connection.send(new ClientboundSetActionBarTextPacket(\n'
      '    Component.literal(V176MicroMgRules.actionbar(active))));\n',
    "powerarmor/V176CompanionMode.java":
      '  p.connection.send(new ClientboundSetActionBarTextPacket(Component.literal(message)));\n',
    "build103/Build103GameTests.java":
      '''// POWER_ARMOR_REAL_ROUNDTRIP_V69
                  check(dev.obsidiannetwork.powerarmor.PowerArmorRuntime.full(player),"missing tier "+tier+" before first exit");
                  stands.get(0).discard();
                  System.out.println("POWER_ARMOR_REAL_ROUNDTRIP_V69 PASS tier=MK"+(tier+1)+
                      " first_exit=true duplicate_click_guard=true previous_armor_restored=true protection5_roundtrip=true");
// End of isolated roundtrip fixture
'''
   }
   for name,src in fixtures.items():
    p=J/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(src)
   env={**os.environ,"V1_SOURCE_ROOT":tmp}
   for script in (NETWORK,GAME):
    proc=subprocess.run([sys.executable,str(script)],capture_output=True,text=True,env=env)
    self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
   source=(J/"build103/Build103GameTests.java").read_text()
   self.assertIn("V176_B717_REAL_BULLET_FE_LOOTING PASS",source)
   self.assertIn("V176_B717_REAL_COMPANION_EXCLUSIVE PASS",source)
   # B755: the weapon toggle replaces the equipped chest stack for client sync;
   # all GameTest FE checks must read the current server equipment slot.
   self.assertEqual(source.count("chest=player.getItemBySlot(slots[1]);"),3)
   self.assertIn("B755 disabling Attack changed remaining FE",source)
   for snippet in ("V176MicroMgFire.fire(player)==1","EnergyTool.energy(chest)==before-3000L",
                   "V176LootingSupport.restore(","V176CompanionMode.toggle(player,true)==1"):
    self.assertIn(snippet,source)
   for name in ("powerarmor/V176AttackModeServer.java","powerarmor/V176CompanionMode.java"):
    self.assertIn("if(p.connection!=null)",(J/name).read_text())
   for script in (NETWORK,GAME):
    proc=subprocess.run([sys.executable,str(script)],capture_output=True,text=True,env=env)
    self.assertNotEqual(proc.returncode,0,"duplicate source injection must fail closed")
if __name__=="__main__":unittest.main()
