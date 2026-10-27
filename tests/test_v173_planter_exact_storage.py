#!/usr/bin/env python3
"""Fail-closed regression for v1.7.3 planter exact storage identity."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=ROOT/"features/v173/apply-planter-exact-item-identity.py"
BASE=ROOT/"features/v172/apply-network-planter-146.py"
JAVA="dev/obsidiannetwork/blockentity/NetworkPlanterBlockEntity.java"

def baseline():
    src=BASE.read_text(encoding="utf-8")
    marker='java("blockentity/NetworkPlanterBlockEntity.java",r'+"'''"
    assert src.count(marker)==1,"Planter source scaffold changed"
    return src.split(marker,1)[1].split("'''",1)[0]

def patch(source):
    with tempfile.TemporaryDirectory() as tmp:
        target=Path(tmp)/JAVA
        target.parent.mkdir(parents=True)
        target.write_text(source,encoding="utf-8")
        done=subprocess.run([sys.executable,str(PATCH)],env=dict(os.environ,V1_SOURCE_ROOT=tmp),
                            capture_output=True,text=True,timeout=20)
        return done,target.read_text(encoding="utf-8")

class ExactPlanterIdentity(unittest.TestCase):
    def test_expected_source_still_uses_legacy_key(self):
        source=baseline()
        self.assertEqual(source.count("ItemKey key=ItemKey.simple("),1)
        self.assertEqual(source.count("runtime.storage().insert(key,stack.getCount())"),1)

    def test_terminal_key_and_exact_payload_are_used(self):
        source=baseline()
        result,after=patch(source)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn("V173_PLANTER_EXACT_ITEM_KEY_PASS",result.stdout)
        self.assertIn("new dev.obsidiannetwork.platform.MinecraftItemStackCodec(world.registryAccess())",after)
        self.assertIn("codec.describe(stack.copyWithCount(1))",after)
        self.assertIn("descriptor.key(),descriptor.canonicalPayload(),stack.getCount()",after)
        self.assertNotIn("ItemKey key=ItemKey.simple(",after)
        self.assertNotIn("runtime.storage().insert(key,stack.getCount())",after)

    def test_no_loss_and_no_duplicate_unaccepted_items(self):
        _,after=patch(baseline())
        self.assertIn("if(accepted>0){",after)
        self.assertIn("stack.shrink((int)Math.min(accepted,stack.getCount()))",after)
        self.assertIn("if(stack.isEmpty())output[i]=ItemStack.EMPTY;",after)
        for preserved in (
            "Map<Item,Integer> batch=be.harvest(world);",
            "if(stored()==0)return;",
            "if(runtime==null||!runtime.powered())continue;",
            "if(!dest.canPlaceItem(slot,stack))continue;",
            'out.store("outputs",ItemStack.OPTIONAL_CODEC.listOf(),Arrays.asList(output));'
        ):
            self.assertIn(preserved,after)

    def test_patch_is_fail_closed_and_atomic_on_source_drift(self):
        source=baseline().replace(
            "runtime.storage().insert(key,stack.getCount())",
            "runtime.storage().insert(key,1L)")
        result,after=patch(source)
        self.assertNotEqual(result.returncode,0)
        self.assertEqual(after,source)

    def test_not_repeatable(self):
        result,after=patch(baseline())
        self.assertEqual(result.returncode,0,result.stderr)
        repeated,unchanged=patch(after)
        self.assertNotEqual(repeated.returncode,0)
        self.assertEqual(unchanged,after)

if __name__=="__main__":
    unittest.main()
