"""B891 preflight contract: every user-reported issue has a fail-closed code path."""
from pathlib import Path
import ast, unittest
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
    'setTooltipForNextFrame(font,lines,mx,my)',
    'super.renderSlotContents(g,stack,slot,"");'):
   self.assertIn(token,text)
  self.assertIn('Component.literal("<"),b->command',text)
 def test_order_and_explicit_build(self):
  w=(R/".github/workflows/networkstorage-v1.7-clean.yml").read_text()
  a="python3 features/v176/apply-v176-b879-vanilla-block-icons-card-backpack-gui.py"
  b="python3 features/v176/apply-v176-b891-arm-backpack-ingame.py"
  self.assertLess(w.index(a),w.index(b))
  self.assertEqual(w.count("B891_EXPLICIT_BUILD_20261102"),4)
  self.assertIn("xsxlabs-network-storage-v1.7.6-b891-ingame-test",w)
if __name__=="__main__":unittest.main()
