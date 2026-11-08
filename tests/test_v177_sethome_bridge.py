#!/usr/bin/env python3
"""Fail-closed source contract for third-party /sethome support on 1.7.7."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PATCH = ROOT / "features/v177/apply-v177-jarvis-sethome-bridge.py"
FLOW = ROOT / ".github/workflows/networkstorage-v1.7-clean.yml"

class HomeBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patch = PATCH.read_text(encoding="utf-8")
        cls.workflow = FLOW.read_text(encoding="utf-8")

    def test_successful_existing_commands_only(self):
        s = self.patch
        self.assertIn("CommandEvent event", s)
        self.assertIn("if(event.isCanceled())return;", s)
        self.assertIn("if(parsed.getReader().canRead())return;", s)
        self.assertIn('op.equals("sethome")', s)
        self.assertIn('op.equals("delhome")', s)
        self.assertIn('op.equals("deletehome")', s)
        self.assertIn('op.equals("ftbessentials")', s)
        self.assertIn("if(!success||result<=0)return;", s)
        self.assertIn("withCallback(observer,CommandResultCallback::chain)", s)
        self.assertNotIn("Commands.literal", s)  # never hijack third-party commands
        self.assertNotIn("sendCommand", s)

    def test_server_owned_persistence_is_player_dimension_scoped(self):
        s = self.patch
        for text in ("SavedDataType<V177HomeIndex>", "V177HomeIndex::new",
                     "getDataStorage().computeIfAbsent(TYPE)",
                     "player.getUUID().toString()", "player.level().dimension().identifier()",
                     "home.owner().equals(owner)", "home.dimension().equals(dim)",
                     "entries.remove(", "setDirty()"):
            self.assertIn(text, s)
        self.assertIn(">=64)return;", s)

    def test_radius_and_no_tick_spam(self):
        s = self.patch
        for text in ("<=64D", "<144D", "player.tickCount%20!=0",
                     "previous==null||previous!=near",
                     "PacketDistributor.sendToPlayer(player,new V177HomeProximityPayload(near))"):
            self.assertIn(text, s)
        self.assertNotIn("sendSystemMessage", s)
        self.assertNotIn("player.connection.connection", s)
        self.assertIn("if(player.connection==null)return;", s)

    def test_client_uses_spawn_and_command_home_and_only_audio(self):
        s = self.patch
        for text in ("nearCommandHome||atSpawn", "if(!nearHome&&(nearCommandHome||atSpawn))",
                     "nearHome=false;nearCommandHome=false", 'g.text(mc.font,subtitle'):
            if text == 'g.text(mc.font,subtitle':
                self.assertNotIn(text, s)
            else:
                self.assertIn(text, s)
        self.assertIn('enqueue(2,"Welcome home, sir.","Willkommen zu Hause, Sir.")', s)

    def test_play_to_client_only(self):
        s = self.patch
        self.assertIn('registrar("1").playToClient', s)
        self.assertIn('context.enqueueWork', s)
        self.assertIn('V177JarvisClient.setNearCommandHome(payload.near())', s)
        self.assertNotIn("playToServer", s)

    def test_build_injector_after_voice_stays_1_7_7_only(self):
        t = self.workflow
        a = t.index('if [ "$GITHUB_REF_NAME" = "1.7.7" ]; then\n              python3 features/v177/apply-v177-armor-integrity-repair.py')
        b = t.index('              python3 features/v177/apply-v177-jarvis-voice.py', a)
        c = t.index('              python3 features/v177/apply-v177-jarvis-sethome-bridge.py', b)
        d = t.index('              python3 features/v177/generate-v177-natural-voice.py', c)
        self.assertTrue(a < b < c < d)

if __name__ == "__main__":
    unittest.main()
