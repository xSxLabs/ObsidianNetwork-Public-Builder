#!/usr/bin/env python3
"""B1804 v13 regression contracts for real JAR model, map and wheel."""
import ast,json,os,struct,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
P=R/"features/v178/apply-v178-b1804-v13.py"
W=(R/".github/workflows/networkstorage-v1.7-clean.yml").read_text()

class V13MapBuilderWheel(unittest.TestCase):
 def test_order_and_v13_output(self):
  ast.parse(P.read_text())
  a="python3 features/v178/apply-v178-b1802-v12.py"
  b="python3 features/v178/apply-v178-b1804-v13.py"
  self.assertIn(a,W);self.assertIn(b,W)
  self.assertLess(W.index(a),W.index(b))
  self.assertIn("xSxLabs-Network-Storage-1.7.8-v17.jar",W)
  self.assertIn("xsxlabs-network-storage-1.7.8-v17",W)
  self.assertIn("contains(github.event.head_commit.message, '_EXPLICIT_BUILD_')",W)

 def test_no_forced_world_loads_or_frame_sampling(self):
  s=P.read_text()
  for token in ("refreshSurface(world,cx,cz);",
                "b1802NearCursor++%25","b1802FarCursor++%625",
                "if(!world.hasChunk(cx,cz))return;",
                "java.util.Arrays.equals(before,after)",
                "V178MiniRaster.tick(world);"):
   self.assertIn(token,s)
  self.assertNotIn("forceChunk(",s)
  self.assertNotIn("world.getChunk(",s)
  self.assertNotIn("getBlockState(",s)

 def test_small_face_and_wheel_show(self):
  s=P.read_text()
  for token in ("B1804_SMALL_POINTER","x-2,y-2,4",
                "for(int t=3;t<=6;t++","int wing=t==3?1:0",
                'if(!available())return wheel;', "FLY LOCKED",
                "V178FlyModuleClient.available()"):
   self.assertIn(token,s)
  self.assertIn("PowerArmorRuntime.full(p)",(R/"features/v178/apply-v178-b1687-fly-wheel.py").read_text())

 def test_generated_java_models_if_reconstructed(self):
  root=os.getenv("V1_SOURCE_ROOT")
  res=os.getenv("V1_RESOURCE_ROOT")
  if not root or not res:self.skipTest("CI reconstruction only")
  j=Path(root)/"dev/obsidiannetwork"
  a=Path(res)/"assets/obsidiannetwork"
  marker=(j/"client/V178MapMarkers.java").read_text()
  fly=(j/"client/V178FlyModuleClient.java").read_text()
  wheel=(j/"client/NetworkActionWheelClient.java").read_text()
  t=(j/"client/V178TerrainMap.java").read_text()
  for token in ("x-2,y-2,4","B1804_SMALL_POINTER"):
   self.assertIn(token,marker)
  self.assertNotIn("x-3,y-3,6",marker)
  self.assertNotIn("if(!available())return wheel;",fly)
  self.assertIn("FLY LOCKED",wheel)
  self.assertIn("refreshSurface(world,cx,cz);",t)
  model=json.loads((a/"models/block/mining_builder.json").read_text())
  self.assertEqual(len(model["elements"]),1)
  self.assertEqual(sum(len(el["faces"]) for el in model["elements"]),6)
  for el in model["elements"]:
   self.assertEqual(set(el["faces"]),{"north","south","east","west","up","down"})
   for face in el["faces"].values():
    self.assertIn(face["texture"][1:],model["textures"])
  for key,loc in model["textures"].items():
   png=(a/"textures"/(loc.split(":",1)[1]+".png")).read_bytes()
   self.assertEqual(png[:8],b"\x89PNG\r\n\x1a\n")
   self.assertEqual(struct.unpack(">II",png[16:24]),
    (32,32) if key=="front" else (16,16))
  states=json.loads((a/"blockstates/mining_builder.json").read_text())
  self.assertEqual(len(states["variants"]),4)

if __name__=="__main__":unittest.main()
