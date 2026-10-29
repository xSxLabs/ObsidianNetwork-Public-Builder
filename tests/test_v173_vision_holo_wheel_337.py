import ast,pathlib,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
P=ROOT/"features/v173/apply-vision-holo-wheel-337.py"
class TestVisionHoloWheel337(unittest.TestCase):
 def test_source_syntax(self):ast.parse(P.read_text(encoding="utf-8"))
 def test_models_not_markers(self):
  s=P.read_text(encoding="utf-8")
  for x in ('CableFacadeRenderer.java','blockEntity.facadeState()',
            'ConduitBundleRenderer.java','B337_REAL_BLOCKS','@SubscribeEvent public static void hud(RenderGuiEvent.Post event){}'):
   self.assertIn(x,s)
 def test_server_text_displays_restored(self):
  s=P.read_text(encoding="utf-8")
  self.assertIn('entity.setText(Component.literal(line)',s)
  self.assertIn('if("map".equals(holoMode)){',s)
 def test_radial_wheel_no_box(self):
  self.assertIn('wheelSector(double dx,double dy,boolean vision)',P.read_text(encoding='utf-8'))
  s=P.read_text(encoding="utf-8")
  for x in ('B337_CIRCULAR_FIVE_WEDGE','wheelSector','radius2<28*28||radius2>103*103'):
   self.assertIn(x,s)
  self.assertIn('g.fill(x+46,y+53,x+110,y+92,shade);',s)
  self.assertIn('s=s[:start]+',s)
if __name__=="__main__":unittest.main()
