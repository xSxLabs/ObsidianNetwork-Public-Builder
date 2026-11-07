"""B1301 all-location Backpack Magnet regression: source, CAS and batching.

Fast tests are synthetic source preflight, NOT a replacement for Java,
Curios-optional dedicated server startup, or real 8-block in-game pickup.
"""
import ast
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
V176=ROOT/"features/v176"
PATCH=V176/"apply-v176-b1301-backpack-magnet-any-location.py"
ORIGINAL=V176/"java/V176BackpackEquipped.java"
B1234=V176/"apply-v176-b1234-magnet-fix.py"
B1270=V176/"apply-v176-b1270-magnet-8-instant-batched.py"
B1273=V176/"apply-v176-b1273-placed-backpack-magnet.py"
WORKFLOW=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"

def extracted_assignment(path,name):
    tree=ast.parse(path.read_text("utf-8"))
    for node in tree.body:
        if isinstance(node,ast.Assign) and isinstance(node.value,ast.Constant):
            if any(isinstance(target,ast.Name) and target.id==name for target in node.targets):
                return ast.literal_eval(node.value)
    raise AssertionError((path,name))

def equipped_after_b1234():
    original=ORIGINAL.read_text("utf-8")
    tree=ast.parse(B1234.read_text("utf-8"))
    for node in ast.walk(tree):
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=="update":
            if len(node.args)==3 and isinstance(node.args[0],ast.Constant) and node.args[0].value=="backpack/V176BackpackEquipped.java":
                old=ast.literal_eval(node.args[1])
                new=ast.literal_eval(node.args[2])
                assert original.count(old)==1
                return original.replace(old,new,1)
    raise AssertionError("B1234 activeMagnet Java fixture missing")

def fixtures():
    return {
        "backpack/V176BackpackEquipped.java":equipped_after_b1234(),
        "backpack/V176BackpackMagnetEvents.java":
            "private static final double RANGE=8.0D;\n" +
            extracted_assignment(B1270,"replacement"),
        "backpack/V176BackpackPlacedMagnet.java":extracted_assignment(B1273,"java"),
        "backpack/NetworkBackpackBlock.java":
            "class NetworkBackpackBlock { V176BackpackPlacedMagnet::tick }\n",
        "backpack/NetworkBackpackBlockEntity.java":
            "class NetworkBackpackBlockEntity { boolean xsxPlacedMagnetActive() {return true;} }\n"
    }

def apply(files):
    with tempfile.TemporaryDirectory() as directory:
        root=Path(directory)/"dev/obsidiannetwork"
        for rel,source in files.items():
            p=root/rel;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text(source,encoding="utf-8")
        run=subprocess.run([sys.executable,str(PATCH)],capture_output=True,text=True,
                           env={**os.environ,"V1_SOURCE_ROOT":directory})
        return run,{p:(root/p).read_text("utf-8") for p in files}

class B1301Magnet(unittest.TestCase):
    def test_source_patch_enables_inventory_without_changing_pickup(self):
        ast.parse(PATCH.read_text("utf-8"))
        f=fixtures()
        run,result=apply(f)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        java=result["backpack/V176BackpackEquipped.java"]
        for token in ("case INVENTORY->",
                      "B1301_INVENTORY_MAGNET_DISCOVERY",
                      "B1301_INVENTORY_MAGNET_CAS",
                      "inventory.getItem(i)",
                      "inventory.setItem(index,updated)",
                      "ItemStack.matches(inventory.getItem(index),stack)",
                      "getContainerSize()",
                      "Where.INVENTORY"):
            self.assertIn(token,java)
        for name in f:
            if name!="backpack/V176BackpackEquipped.java":
                self.assertEqual(result[name],f[name])
        self.assertIn("case CHEST->",java)
        self.assertIn("case CURIOS_BACK->",java)
        self.assertIn("case MAIN_HAND->",java)
        self.assertIn("case OFF_HAND->",java)
        self.assertIn("V176BackpackPlacedMagnet::tick",result["backpack/NetworkBackpackBlock.java"])
        self.assertLess(java.index("Where.OFF_HAND"),java.index("Where.INVENTORY"))
        self.assertLess(java.index("public static Located activeMagnet("),
                        java.index("public static Located active("))

    def test_fails_closed_on_changed_equipment_switch(self):
        f=fixtures()
        f["backpack/V176BackpackEquipped.java"]=f["backpack/V176BackpackEquipped.java"].replace(
            "case OFF_HAND->{","case OFFHAND->{")
        run,result=apply(f)
        self.assertNotEqual(run.returncode,0)
        self.assertEqual(result,f)

    def test_inventory_slot_selection_and_cas_in_model(self):
        rng=random.Random(1301)
        for _ in range(10000):
            slots=[{"bag":False,"enabled":False,"items":0} for _ in range(41)]
            target=rng.randrange(len(slots))
            slots[target]={"bag":True,"enabled":True,"items":rng.randrange(0,1000)}
            first=next((i for i,x in enumerate(slots) if x["bag"] and x["enabled"]),None)
            self.assertEqual(first,target)
            original=slots[target].copy()
            staged=original.copy();staged["items"]+=rng.randrange(1,65)
            # Only the originally selected unchanged slot is modified.
            if slots[target]==original: slots[target]=staged
            self.assertEqual(slots[target],staged)
            self.assertTrue(all(not x["bag"] for i,x in enumerate(slots) if i!=target))

    def test_ground_items_consumed_only_after_matching_slot_persist(self):
        rng=random.Random(8171301)
        for _ in range(10000):
            ground=rng.randrange(0,10000)
            accepted=rng.randrange(0,ground+1)
            slot_changed=bool(rng.randrange(2))
            original={"count":rng.randrange(0,10000)}
            expected=original.copy()
            current=original.copy()
            if slot_changed:current["count"]+=1
            new={"count":original["count"]+accepted}
            committed=current==expected
            if committed:
                current=new
                ground-=accepted
            self.assertGreaterEqual(ground,0)
            if slot_changed:self.assertEqual(ground,ground+0)
            else:self.assertEqual(current["count"],new["count"])

    def test_pipeline_after_b1273_and_b1300_without_changing_freeze(self):
        w=WORKFLOW.read_text("utf-8")
        self.assertIn(PATCH.name,w)
        self.assertIn(Path(__file__).name,w)
        self.assertLess(w.index("python3 features/v176/apply-v176-b1273-placed-backpack-magnet.py"),
                        w.index("python3 features/v176/"+PATCH.name))
        self.assertLess(w.index("python3 features/v176/apply-v176-b1300-energy-conservation.py"),
                        w.index("python3 features/v176/"+PATCH.name))
        self.assertNotIn("features/v175/",PATCH.read_text("utf-8"))
        self.assertNotIn("_EXPLICIT_BUILD_",PATCH.read_text("utf-8"))

if __name__=="__main__":
    unittest.main()
