#!/usr/bin/env python3
"""Build 58: inspect actual generated model and texture bytes (no private source)."""
import ast
import struct
import unittest
import zlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"features/v17/apply-power-armor-geckolib.py"

def pure_generators():
    tree=ast.parse(SCRIPT.read_text(encoding="utf-8"))
    nodes=[]
    for n in tree.body:
        if isinstance(n,ast.FunctionDef) and n.name in ("bone","chunk","png"):
            nodes.append(n)
        if isinstance(n,ast.Assign) and any(
            isinstance(t,ast.Name) and t.id=="bones" for t in n.targets):
            nodes.append(n)
    assert len(nodes)==4
    scope={"struct":struct,"zlib":zlib}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(SCRIPT),"exec"),scope)
    return scope

class Gecko58(unittest.TestCase):
    def test_hinged_parts_and_no_duplicate_cuboids(self):
        bones=pure_generators()["bones"]
        self.assertEqual(len(bones),13)
        by_name={b["name"]:b for b in bones}
        self.assertEqual(len(by_name),13)
        for name,parent in (("visor","helmet"),("reactor","spine"),
                            ("left_shoulder","left_arm"),("right_shoulder","right_arm")):
            self.assertEqual(by_name[name]["parent"],parent)
        cubes=[cube for bone in bones for cube in bone.get("cubes",[])]
        self.assertEqual(len(cubes),len({
            tuple(c["origin"]+c["size"]) for c in cubes}))
        for cube in cubes:
            self.assertTrue(all(v>0 for v in cube["size"]))
            self.assertTrue(all(0<=u<128 for u in cube["uv"]))
        self.assertLess(by_name["visor"]["cubes"][0]["origin"][2],-4.5)
        self.assertLess(by_name["reactor"]["cubes"][0]["origin"][2],-3.4)

    def test_generated_pngs_are_rgba_and_unique(self):
        png=pure_generators()["png"]
        mk1,mk2=png("mk1"),png("mk2")
        self.assertNotEqual(mk1,mk2)
        for raw in (mk1,mk2):
            self.assertTrue(raw.startswith(b"\x89PNG\r\n\x1a\n"))
            pos=8
            data=b""
            while pos<len(raw):
                n=struct.unpack(">I",raw[pos:pos+4])[0]
                kind=raw[pos+4:pos+8]
                payload=raw[pos+8:pos+8+n]
                crc=struct.unpack(">I",raw[pos+8+n:pos+12+n])[0]
                self.assertEqual(zlib.crc32(kind+payload)&0xffffffff,crc)
                pos+=12+n
                if kind==b"IHDR":
                    self.assertEqual(struct.unpack(">IIBBBBB",payload)[:4],(128,128,8,6))
                if kind==b"IDAT":data+=payload
                if kind==b"IEND":break
            pixels=zlib.decompress(data)
            self.assertEqual(len(pixels),128*(128*4+1))
            def pixel(x,y):
                offset=y*(128*4+1)+1+x*4
                return tuple(pixels[offset:offset+4])
            self.assertTrue(all(pixels[y*513]==0 for y in range(128)))
            self.assertEqual(pixel(70,3)[3],255)
            self.assertGreater(pixel(70,3)[2],150)
            self.assertNotEqual(pixel(70,3),pixel(20,20))
            self.assertNotEqual(pixel(10,10),pixel(10,11))

    def test_no_inventory_changes_in_gecko_render_patch(self):
        src=SCRIPT.read_text(encoding="utf-8")
        self.assertIn("The four actual ItemStacks never enter",src)
        self.assertIn("stand.setInvisible(false)",src)
        self.assertIn("noSave()",src)
        self.assertIn('"animation.power_armor.open"',src)
        self.assertIn('"animation.power_armor.close"',src)

if __name__=="__main__":
    unittest.main()
