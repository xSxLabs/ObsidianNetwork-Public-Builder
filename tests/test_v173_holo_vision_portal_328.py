import ast, pathlib, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
P=ROOT/"features/v173/apply-holo-vision-portals-328.py"
class Test328(unittest.TestCase):
 def test_python_syntax(self):
  ast.parse(P.read_text(encoding="utf-8"))
 def test_native_hologram(self):
  s=P.read_text(encoding="utf-8")
  for v in ("V173_HOLO_RENDER_328","submitText(","Font.DisplayMode.SEE_THROUGH","device.mode()==","textProjection(","mapSamples=sampleMap"):
   self.assertIn(v,s)
 def test_no_extra_vision(self):
  s=P.read_text(encoding="utf-8")
  for v in ("V173_VISION_FACADE_ONLY_328",'id.endsWith("_cable")',"facade.facadeState().isAir()","inverse.transform(local)","toggleFromWheel()","NetworkVisionClient.installed()"):
   self.assertIn(v,s)
  vision=s.split('vision.write_text(r',1)[1].split("'''",2)[1] if False else s[s.index('vision.write_text('):s.index('# Old K-key')]
  self.assertNotIn("NETWORK_PLANTER",vision)
  self.assertNotIn("NETWORK_PRINTER",vision)
  self.assertNotIn("addParticle",vision)
 def test_importer_exporter_visibility(self):
  s=P.read_text(encoding="utf-8")
  self.assertIn('boolean input=id.equals("importer")',s)
  self.assertIn('boolean output=id.equals("exporter")',s)
  self.assertIn('if(cable&&(!(mc.level.getBlockEntity(p) instanceof',s)
  self.assertNotIn('if(!(mc.level.getBlockEntity(p) instanceof',s)
 def test_portal_1x2(self):
  s=P.read_text(encoding="utf-8")
  for v in ("V173_PORTALGUN_1X2_328","Blocks.LIGHT_BLUE_STAINED_GLASS","Blocks.ORANGE_STAINED_GLASS","return box(0,0,6,16,32,10);","+1.85"):
   self.assertIn(v,s)
if __name__=="__main__":unittest.main()
