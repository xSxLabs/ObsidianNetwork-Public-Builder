import ast,math,pathlib,unittest
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
  for x in ('B340_EXACT_CIRCLE','wheelSector',
            'int maxX=(int)Math.floor(Math.sqrt(103D*103D-yy*yy))',
            'g.fill(x+start,y+yy,x+stop,y+yy+1'):
   self.assertIn(x,s)
  self.assertIn('g.fill(x+46,y+53,x+110,y+92,shade);',s)
  self.assertIn('s=s[:start]+',s)
 def test_real_scanline_stays_inside_outer_ring(self):
  # A 2x2 square at the border used to poke out of the circular wheel.
  for y in range(-103,104):
   max_x=math.isqrt(103*103-y*y)
   for x in range(-max_x,max_x+1):
    self.assertLessEqual(x*x+y*y,103*103)
  script=P.read_text(encoding="utf-8")
  self.assertNotIn("g.fill(x+xx,y+yy,x+xx+2,y+yy+2,color);",script)
  self.assertIn("while(start<=maxX)",script)
  self.assertIn("while(stop<=maxX)",script)
 def test_authoritative_hologram_with_client_fallback(self):
  script=P.read_text(encoding="utf-8")
  for marker in ("B340_HOLO_SINGLE_OWNER","entity.entityTags()",
                 '"xsx-holo-"+mapTerminal.asLong()',
                 "if(!authoritative)textProjection("):
   self.assertIn(marker,script)
  self.assertIn('if("map".equals(holoMode)){',script)
if __name__=="__main__":unittest.main()
