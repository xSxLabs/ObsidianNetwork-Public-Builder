#!/usr/bin/env python3
"""Guard old Planter ItemKey migration across cells and terminal sessions."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
LEGACY=ROOT/"features/v173/apply-planter-legacy-merge.py"
EXACT=ROOT/"features/v173/apply-planter-exact-item-identity.py"
BASE=ROOT/"features/v172/apply-network-planter-146.py"
PLANTER="dev/obsidiannetwork/blockentity/NetworkPlanterBlockEntity.java"
MENU="dev/obsidiannetwork/menu/StorageTerminalMenu.java"
HELPER="dev/obsidiannetwork/network/LegacyPlanterKeyMigration.java"
MENU_BASE="""package dev.obsidiannetwork.menu;
public class StorageTerminalMenu {
 private boolean wireless;
 private final Object player=null;
 public StorageTerminalMenu(){
   ServerLevel openingLevel = this.terminalServerLevel();
 }
 public BlockPos terminalPos(){return null;}
}
"""
def source():
    blob=BASE.read_text(encoding="utf-8")
    token='java("blockentity/NetworkPlanterBlockEntity.java",r'+"'''"
    if blob.count(token)!=1: raise RuntimeError("Planter reconstruction source changed")
    return blob.split(token,1)[1].split("'''",1)[0]

def patch(planter=None,menu=MENU_BASE,repeat=False):
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        p=root/PLANTER;p.parent.mkdir(parents=True,exist_ok=True)
        m=root/MENU;m.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(planter if planter is not None else source(),encoding="utf-8")
        m.write_text(menu,encoding="utf-8")
        env=dict(os.environ,V1_SOURCE_ROOT=tmp)
        first=subprocess.run([sys.executable,str(EXACT)],env=env,
                             capture_output=True,text=True,timeout=30)
        if first.returncode!=0:
            return first, {"planter":p.read_text(),"menu":m.read_text()}
        done=subprocess.run([sys.executable,str(LEGACY)],env=env,
                            capture_output=True,text=True,timeout=30)
        result={"planter":p.read_text(),"menu":m.read_text(),
                "java":(root/HELPER).read_text() if (root/HELPER).exists() else ""}
        if repeat and done.returncode==0:
            result["again"]=subprocess.run([sys.executable,str(LEGACY)],env=env,
                            capture_output=True,text=True,timeout=30).returncode
        return done,result

class LegacyMigration(unittest.TestCase):
    def test_reconstruction_guards_and_automatic_entrypoints(self):
        result,files=patch()
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn("V173_LEGACY_PLANTER_MIGRATION_APPLIED",result.stdout)
        self.assertIn("V173_PLANTER_LEGACY_MIGRATION",files["planter"])
        self.assertIn("V173_PLANTER_TERMINAL_CONTINUOUS_MIGRATION",files["menu"])
        self.assertIn("public void broadcastChanges()",files["menu"])
        self.assertIn("super.broadcastChanges()",files["menu"])
        self.assertIn("LegacyPlanterKeyMigration.tick",files["planter"])
        self.assertIn("LegacyPlanterKeyMigration.tick",files["menu"])
        self.assertIn("runtime.descriptors().registerKnown(descriptor.key(),descriptor.canonicalPayload())",files["planter"])
        self.assertIn("this.wireless",files["menu"])

    def test_old_id_only_key_is_moved_to_canonical_key_with_rollback(self):
        result,files=patch()
        self.assertEqual(result.returncode,0,result.stderr)
        j=files["java"]
        for condition in (
            "ItemKey.simple(BuiltInRegistries.ITEM.getKey(item).toString())",
            "new MinecraftItemStackCodec(level.registryAccess()).describe(new ItemStack(item))",
            "storage.index().amount(old)",
            "storage.index().amount(exact.key())",
            "storage.extract(old,requested)",
            "storage.insertExact(exact.key(),exact.canonicalPayload(),removed)",
            "storage.extract(exact.key(),newDelta)",
            "storage.insert(old,oldDeficit)",
            "storage.index().amount(old)!=originalOld-removed",
            "storage.index().amount(exact.key())!=originalExact+removed",
        ):
            self.assertIn(condition,j)
        self.assertIn("private static final int PER_KEY=512;",j)
        self.assertIn("private static final int KEYS_PER_TICK=8;",j)
        self.assertIn("new WeakHashMap<>()",j)
        self.assertIn("if(exact.key().equals(old))return false;",j)

    def test_only_known_plain_planter_drops(self):
        result,files=patch()
        self.assertEqual(result.returncode,0,result.stderr)
        j=files["java"]
        self.assertIn("for(NetworkPlanterBlock.Plant plant:NetworkPlanterBlock.Plant.values())",j)
        self.assertIn("all.add(Items.STICK)",j)
        self.assertIn("all.add(Items.APPLE)",j)
        self.assertIn("!items().contains(item)",j)
        self.assertNotIn("for(ItemKey key:storage.index().keysSnapshot())",j)

    def test_fail_closed_on_second_application(self):
        result,files=patch(repeat=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertNotEqual(files["again"],0)

    def test_fail_closed_on_terminal_source_drift(self):
        result,files=patch(menu=MENU_BASE.replace(
            "ServerLevel openingLevel = this.terminalServerLevel();",
            "ServerLevel level = this.terminalServerLevel();"))
        self.assertNotEqual(result.returncode,0)
        self.assertNotIn("V173_PLANTER_LEGACY_MIGRATION",files["planter"])
        self.assertNotIn("V173_LEGACY_PLANTER_NORMALIZE",files.get("java",""))
if __name__=="__main__":unittest.main()
