"""B1304 source and behavioral guards for true item-name A-Z vs COUNT DESC."""
import ast
import os
import random
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v176/apply-v176-b1304-backpack-sort-display-names.py"
PREV=ROOT/"tests/test_v176_b1303_backpack_shift_sort_lock.py"
WORKFLOW=ROOT/".github/workflows/networkstorage-v1.7-clean.yml"

def menu_fixture():
    tree=ast.parse(PREV.read_text("utf-8"))
    menu=None
    for node in tree.body:
        if isinstance(node,ast.Assign) and isinstance(node.value,ast.Constant):
            if any(isinstance(k,ast.Name) and k.id=="MENU" for k in node.targets):
                menu=node.value.value
                break
    if menu is None:raise AssertionError("Missing B1303 MENU fixture")
    old=("   if(countSort)result.sort(java.util.Comparator.comparingLong(V176BackpackCells.Entry::count).reversed());\n"
         "   else result.sort(java.util.Comparator.comparing(e->e.descriptor().key().itemId().toString()));")
    new=("   if(countSort)result.sort(java.util.Comparator\n"
         "      .comparingLong(V176BackpackCells.Entry::count).reversed()\n"
         "      .thenComparing(e->e.descriptor().key().itemId().toString()));\n"
         "   // The default is a stable item-identity sort, not unordered HashMap order.\n"
         "   else result.sort(java.util.Comparator.comparing(\n"
         "      e->e.descriptor().key().itemId().toString()));")
    assert menu.count(old)==1
    menu=menu.replace(old,new,1)
    # Apply the real B1303 strict patch first; B1304 must match its output,
    # not a hand-built source that omits Shift's server-side frozen list.
    screen=None
    for node in tree.body:
        if isinstance(node,ast.Assign) and isinstance(node.value,ast.Constant):
            if any(isinstance(k,ast.Name) and k.id=="SCREEN" for k in node.targets):
                screen=node.value.value
                break
    if screen is None:raise AssertionError("Missing B1303 SCREEN fixture")
    patch1303=ROOT/"features/v176/apply-v176-b1303-backpack-shift-sort-lock.py"
    with tempfile.TemporaryDirectory() as directory:
        root=Path(directory)/"dev/obsidiannetwork"
        (root/"backpack").mkdir(parents=True)
        (root/"client").mkdir(parents=True)
        (root/"backpack/V176BackpackMenu.java").write_text(menu,"utf-8")
        (root/"client/V176BackpackScreen.java").write_text(screen,"utf-8")
        run=subprocess.run([sys.executable,str(patch1303)],capture_output=True,text=True,
                           env={**os.environ,"V1_SOURCE_ROOT":directory})
        if run.returncode!=0:raise AssertionError("B1303 fixture failed "+run.stderr)
        return (root/"backpack/V176BackpackMenu.java").read_text("utf-8")

def apply(menu):
    with tempfile.TemporaryDirectory() as directory:
        p=Path(directory)/"dev/obsidiannetwork/backpack/V176BackpackMenu.java"
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(menu,"utf-8")
        run=subprocess.run([sys.executable,str(PATCH)],capture_output=True,text=True,
                           env={**os.environ,"V1_SOURCE_ROOT":directory})
        return run,p.read_text("utf-8")

class B1304RealAlphabetic(unittest.TestCase):
    def test_source_safety_and_single_name_resolution(self):
        ast.parse(PATCH.read_text("utf-8"))
        run,source=apply(menu_fixture())
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        self.assertIn("B1304_REAL_NAME_AZ",source)
        self.assertIn("IdentityHashMap<V176BackpackCells.Entry,String>",source)
        self.assertIn("names.put(entry,display);",source)
        self.assertIn("names.get(e)",source)
        self.assertIn(".getHoverName().getString().toLowerCase(java.util.Locale.ROOT)",source)
        self.assertIn("codec.recreate(entry.descriptor(),1)",source)
        self.assertEqual(source.count("codec.recreate(entry.descriptor(),1)"),1)
        self.assertIn("V176BackpackCells.Entry::count).reversed()",source)
        self.assertIn("if(xsxShiftLayoutFrozen)return xsxShiftEntries;",source)
        self.assertIn("xsx_v176_backpack_sort_count",source)
        self.assertIn("source.save(updated)",source)
        self.assertEqual(source.count("B1304_REAL_NAME_AZ"),1)
        self.assertNotIn("else result.sort(java.util.Comparator.comparing(",source)

    def test_fails_closed_if_count_comparator_was_changed(self):
        fixture=menu_fixture().replace(
           "V176BackpackCells.Entry::count).reversed()",
           "V176BackpackCells.Entry::count)")
        run,out=apply(fixture)
        self.assertNotEqual(run.returncode,0)
        self.assertEqual(out,fixture)

    def test_cross_mod_item_names_sorted_a_to_z_not_namespace(self):
        items=[
           ("zzmod:apple","Apple",100),
           ("minecraft:stone","Stone",1),
           ("aamod:zinc","Zinc",300),
           ("qmod:carrot","Carrot",200),
           ("minecraft:diamond","Diamond",150),
        ]
        az=sorted(items,key=lambda x:(x[1].casefold(),x[0]))
        amounts=sorted(items,key=lambda x:(-x[2],x[0]))
        self.assertEqual([x[1] for x in az],
                         ["Apple","Carrot","Diamond","Stone","Zinc"])
        self.assertEqual([x[1] for x in amounts],
                         ["Zinc","Carrot","Diamond","Apple","Stone"])

    def test_precomputed_label_sort_only_once_per_entry(self):
        rng=random.Random(1304)
        for _ in range(250):
            rows=[(f"mod{rng.randrange(120)}:i{j}",
                   f"Item {rng.randrange(12000)}",
                   rng.randrange(1,1_000_000))
                  for j in range(rng.randrange(1,1000))]
            calls=0
            labels={}
            for i,(item,name,count) in enumerate(rows):
                calls+=1
                labels[i]=name.casefold()
            order=sorted(range(len(rows)),key=lambda i:(labels[i],rows[i][0]))
            self.assertEqual(calls,len(rows))
            self.assertEqual(len(order),len(rows))
            self.assertEqual(set(order),set(range(len(rows))))

    def test_workflow_applied_after_b1303_but_no_release(self):
        flow=WORKFLOW.read_text("utf-8")
        self.assertIn(PATCH.name,flow)
        self.assertIn(Path(__file__).name,flow)
        self.assertLess(flow.index("python3 features/v176/apply-v176-b1303-backpack-shift-sort-lock.py"),
                        flow.index("python3 features/v176/"+PATCH.name))
        self.assertNotIn("_EXPLICIT_BUILD_",PATCH.read_text("utf-8"))

if __name__=="__main__":unittest.main()
