#!/usr/bin/env python3
"""B1792 v11 FPS: prove visually safe opaque culling and facade CPU short circuits."""
import ast,json,os,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"features/v178/apply-v178-b1792-render-fps.py"
WF=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
class V11FpsOptimization(unittest.TestCase):
 def test_script_and_version_order(self):
  s=SCRIPT.read_text()
  ast.parse(s)
  a="python3 features/v178/apply-v178-b1780-v11.py"
  b="python3 features/v178/apply-v178-b1792-render-fps.py"
  self.assertIn(a,WF)
  self.assertIn(b,WF)
  self.assertLess(WF.index(a),WF.index(b))
  self.assertIn("xSxLabs-Network-Storage-1.7.8-v11.jar",WF)
  self.assertIn("xsxlabs-network-storage-1.7.8-v11",WF)
 def test_no_opaque_assumption_on_glass_or_dynamic_models(self):
  s=SCRIPT.read_text()
  for token in ("tRNS","kind in (4,6)","get(\"rotation\"",'"rotation" in el',
                "if not pngs or None in pngs or not all(opaque(p) for p in pngs)",
                "face not in DIR","abs(at-boundary)<1e-5"):
   self.assertIn(token,s,token)
  self.assertNotIn("getChunk(",s)
  self.assertNotIn("forceChunk(",s)
 def test_bounded_facade_cache_and_vision_compat(self):
  s=SCRIPT.read_text()
  for token in ("B1792_SKIP_HIDDEN_BUNDLE_RENDER_WORK",
                "B1792_FACADE_LIGHT_CACHE",
                "B1792_LIGHTS=new java.util.WeakHashMap",
                "xsxNow-cached.tick<5L","cached.level==",
                "new B1792Light(","getBrightness(",
                "B1792_DIRECTIONS","B1792_LAYERS"):
   self.assertIn(token,s,token)
 def test_generated_model_and_renderer_contract(self):
  java_root=os.getenv("V1_SOURCE_ROOT")
  assets_root=os.getenv("V1_RESOURCE_ROOT")
  if not java_root or not assets_root:self.skipTest("requires reconstructed CI sources")
  j=Path(java_root)/"dev/obsidiannetwork"
  r=Path(assets_root)/"assets/obsidiannetwork"
  conduit=(j/"client/render/ConduitBundleRenderer.java").read_text()
  facade=(j/"client/render/CableFacadeRenderer.java").read_text()
  self.assertIn("B1792_SKIP_HIDDEN_BUNDLE_RENDER_WORK",conduit)
  self.assertIn("B1792_FACADE_LIGHT_CACHE",facade)
  self.assertIn("WeakHashMap",facade)
  model=lambda name:json.loads((r/"models/block"/(name+".json")).read_text())
  wc=model("wireless_charger")
  self.assertEqual(len(wc["elements"]),116)
  wc_faces=sum(len(el.get("faces",{})) for el in wc["elements"])
  self.assertLessEqual(wc_faces,620)
  storage=model("storage_drive_8")
  self.assertEqual(len(storage["elements"]),56)
  self.assertLess(sum(len(el.get("faces",{})) for el in storage["elements"]),305)
  miner=model("mining_builder")
  self.assertEqual(len(miner["elements"]),26)
  self.assertLess(sum(len(el.get("faces",{})) for el in miner["elements"]),120)
  # Transparent powerbank/reactor models remain defined; no texture rewriting.
  for tex in ("reactor_glass_formed.png","powerbank_glass_formed.png"):
   self.assertTrue((r/"textures/block"/tex).is_file())
if __name__=="__main__":unittest.main()
