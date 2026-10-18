#!/usr/bin/env python3
"""Exercise the wireless GUI roster invalidation patch on generated-code anchors."""
import ast
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/wireless-energy/apply-wireless-menu-roster-guard.py"
TEXT=PATCH.read_text()


class WirelessMenuRosterGuardTest(unittest.TestCase):
    def test_revision_is_transient_and_tracks_roster_only(self):
        self.assertIn("private long rosterRevision;",TEXT)
        self.assertIn("public long rosterRevision(){return rosterRevision;}",TEXT)
        self.assertEqual(TEXT.count("rosterRevision++;"),3)
        self.assertNotIn("setChunkForced(",TEXT)
        self.assertNotIn("forceChunk(",TEXT)
        self.assertIn("observedRosterRevision=revision;",TEXT)
        self.assertIn("var fresh=storage.available(owner);",TEXT)
        self.assertIn("device.getLevel()!=owner.level()",TEXT)
        self.assertIn("owner.level().getBlockEntity(pos)!=device",TEXT)
        self.assertIn("!device.canConfigure(owner)",TEXT)

    def test_generator_uses_fail_closed_anchors_and_inserts_functional_guards(self):
        tree=ast.parse(TEXT)
        operations={"data":[],"menu":[]}
        for node in ast.walk(tree):
            if not isinstance(node,ast.Call) or not isinstance(node.func,ast.Name):
                continue
            if node.func.id!="replace" or len(node.args)!=3:
                continue
            scope=node.args[0]
            if not isinstance(scope,ast.Name) or scope.id not in operations:
                continue
            operations[scope.id].append((ast.literal_eval(node.args[1]),
                                          ast.literal_eval(node.args[2])))
        self.assertEqual(len(operations["data"]),4)
        self.assertEqual(len(operations["menu"]),3)
        with tempfile.TemporaryDirectory() as tmp:
            java=Path(tmp)/"dev/obsidiannetwork"
            for group,relative in (
                ("data","wireless/WirelessNetworkData.java"),
                ("menu","menu/WirelessNetworkMenu.java"),
            ):
                target=java/relative
                target.parent.mkdir(parents=True,exist_ok=True)
                # A synthetic fixture with each exact postpatch source anchor.
                target.write_text("\n".join(old for old,_ in operations[group]))
            env=dict(os.environ,V1_SOURCE_ROOT=tmp)
            result=subprocess.run([sys.executable,str(PATCH)],env=env,
                                  capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn("WIRELESS_MENU_ROSTER_INVALIDATION_V1 PASS",result.stdout)
            data=(java/"wireless/WirelessNetworkData.java").read_text()
            menu=(java/"menu/WirelessNetworkMenu.java").read_text()
            self.assertEqual(data.count("rosterRevision++;"),3)
            self.assertIn("matches=ids.get(i).equals(entry.id())&&names.get(i).equals(entry.name());",menu)
            self.assertIn("if(!matches){",menu)
            self.assertIn("observedRosterRevision=revision;",menu)
            self.assertIn("!device.canConfigure(owner)",menu)
            # An already transformed fixture must not silently apply twice.
            again=subprocess.run([sys.executable,str(PATCH)],env=env,
                                 capture_output=True,text=True)
            self.assertNotEqual(again.returncode,0)


if __name__=="__main__":
    unittest.main()
