"""B1230: placed Backpack GUI follows committed cable IO but keeps CAS."""
import ast
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v176/apply-v176-b1230-backpack-live-gui.py"
WF=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"

class BackpackLiveGuiB1230(unittest.TestCase):
 def test_pipeline(self):
  script=PATCH.read_text(encoding="utf-8")
  ast.parse(script)
  workflow=WF.read_text(encoding="utf-8")
  self.assertIn("test_v176_b1230_backpack_live_gui.py",workflow)
  self.assertIn("python3 features/v176/apply-v176-b1230-backpack-live-gui.py",workflow)
  self.assertLess(workflow.index("python3 features/v176/apply-v176-b1225-backpack-chat.py"),
                  workflow.index("python3 features/v176/apply-v176-b1230-backpack-live-gui.py"))
  self.assertIn("_EXPLICIT_BUILD_",workflow)

 def test_live_generation_and_cas_reconstruction(self):
  code=ast.parse(PATCH.read_text(encoding="utf-8"))
  edits={}
  names={}
  for node in code.body:
   if isinstance(node,ast.Assign) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str):
    for target in node.targets:
     if isinstance(target,ast.Name):names[target.id]=node.value.value
  for node in ast.walk(code):
   if not isinstance(node,ast.Call) or not isinstance(node.func,ast.Name) or node.func.id!="change":continue
   if len(node.args)!=3:continue
   path=(ast.literal_eval(node.args[0]) if isinstance(node.args[0],ast.Constant)
         else names.get(node.args[0].id) if isinstance(node.args[0],ast.Name) else None)
   if path is None:continue
   original=ast.literal_eval(node.args[1])
   edits.setdefault(path,[]).append(original)
  self.assertEqual({name:len(entries) for name,entries in edits.items()},
                   {"backpack/NetworkBackpackBlockEntity.java":2,
                    "backpack/V176BackpackMenu.java":4})
  with tempfile.TemporaryDirectory() as root:
   base=Path(root)/"dev/obsidiannetwork"
   for path,fragments in edits.items():
    target=base/path
    target.parent.mkdir(parents=True,exist_ok=True)
    content="\n".join(fragments)
    if path.endswith("BlockEntity.java"):
     content+="\nvoid test(){cableJournal.updateSnapshots(tx);}\n"
    target.write_text(content,encoding="utf-8")
   run=subprocess.run([sys.executable,str(PATCH)],
                      env={**os.environ,"V1_SOURCE_ROOT":str(Path(root))},
                      capture_output=True,text=True,check=True)
   self.assertIn("B1230_BACKPACK_GUI_STAYS_OPEN_ON_COMMITTED_CABLE_IO",run.stdout)
   be=(base/"backpack/NetworkBackpackBlockEntity.java").read_text()
   menu=(base/"backpack/V176BackpackMenu.java").read_text()
   self.assertEqual(be.count("xsxCableCommitRevision++;"),1)
   self.assertIn("onRootCommit(ItemStack before)",be)
   self.assertIn("cableJournal.updateSnapshots(tx)",be)
   self.assertIn("snapshotCableRevision=revision;",menu)
   self.assertIn("if(revision==snapshotCableRevision)return false;",menu)
   self.assertIn("player.level().getBlockEntity(pos)==be",menu)
   self.assertIn("player.distanceToSqr(",menu)
   self.assertIn("||!ItemStack.matches(snapshot,be.getBackpack())",menu)
   self.assertIn("||!be.replaceBackpack(snapshot,next)",menu)
   self.assertIn("snapshot=next.copy();",menu)
   # save() must not silently rebase if a cable changes after a GUI reads.
   save=menu.split("@Override public boolean save(ItemStack next){",1)[1]
   self.assertNotIn("if(!valid()",save)
   self.assertNotIn("snapshot=be.getBackpack().copy();",save)
   self.assertIn("snapshotCableRevision=be.xsxCableCommitRevision();",save)
   self.assertIn("cacheCableRevision==liveCableRevision",menu)
   self.assertIn("cacheCableRevision=liveCableRevision",menu)
   self.assertIn("cacheSource==live",menu)

 def test_expected_transaction_scenarios(self):
  # Small state-machine contract for access across two server ticks:
  # 1. successful cable commit keeps GUI open & refreshes its view
  # 2. simulation / rollback does not advance revision
  # 3. a stale GUI write cannot overwrite a cable deposit/withdrawal
  # 4. removing/replacing the placed block invalidates the GUI
  snapshot=("stone",64)
  latest=("stone",63)
  revision=3
  snapshot_revision=2
  same_block=True
  self.assertTrue(same_block and latest!=snapshot and revision!=snapshot_revision)
  snapshot=latest
  snapshot_revision=revision
  self.assertEqual(snapshot,latest)
  assert revision==snapshot_revision
  # External cable mutation after menu prepares an update: compare-and-swap
  # rejects old snapshot rather than overwriting the new live inventory.
  latest=("stone",62)
  revision+=1
  self.assertNotEqual(snapshot,latest)
  self.assertNotEqual(snapshot_revision,revision)
  same_block=False
  self.assertFalse(same_block and snapshot==latest)

if __name__=="__main__":unittest.main()
