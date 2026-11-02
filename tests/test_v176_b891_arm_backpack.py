"""B891 preflight contract: every user-reported issue has a fail-closed code path."""
from pathlib import Path
import ast, unittest, re
R=Path(__file__).resolve().parents[1]
class B891ArmBackpack(unittest.TestCase):
 def test_all_fixes_staged(self):
  text=(R/"features/v176/apply-v176-b891-arm-backpack-ingame.py").read_text()
  ast.parse(text)
  for token in (
    'addBox(-0.62F,5.0F,-3.15F,1.24F,8.5F,1.25F)',
    'pose.translate(0.58F,-0.30F,-0.53F)',
    'this.rightArm.xRot=-1.43F;',
    'rightArm.xRot=-1.43F;',
    'sleeve.xRot=arm.xRot;',
    'if(onSearch&&button==1)',
    'if(getFocused()==searchBox)setFocused(null)',
    'mouseScrolled(double mx,double my,double scrollX,double scrollY)',
    'int position=page*9+slot-4;',
    'String.format(java.util.Locale.GERMANY,"%,d",amount)',
    'g.nextStratum();',
    'setComponentTooltipForNextFrame(font,lines,mx,my)',
    'g.pose().popMatrix();'):
   self.assertIn(token,text)
  self.assertIn('B898_ARROW_PARTIAL_REMOVAL',text)
 def test_order_and_explicit_build(self):
  w=(R/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
  a="python3 features/v176/apply-v176-b879-vanilla-block-icons-card-backpack-gui.py"
  b="python3 features/v176/apply-v176-b891-arm-backpack-ingame.py"
  self.assertLess(w.index(a),w.index(b))
  marker=re.search(r"run-name:.*?'(B[0-9]+_EXPLICIT_BUILD_20261102)'",w)
  self.assertIsNotNone(marker)
  self.assertEqual(w.count(marker.group(1)),4)
  version=marker.group(1).split("_")[0].lower()
  self.assertIn("xsxlabs-network-storage-v1.7.6-"+version+"-ingame-test",w)
if __name__=="__main__":unittest.main()
