"""Guard against accidentally moving the module slots into the main terminal."""
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
MENU=(ROOT/"features/v176/apply-v176-backpack-menu-810.py").read_text("utf-8")
PANEL=(ROOT/"features/v176/apply-v176-backpack-sidepanel-811.py").read_text("utf-8")

class B811SidePanel(unittest.TestCase):
    def test_modules_outside_main_176_pixel_gui(self):
        self.assertIn("i<4?195:-100,i<4?20+i*24:-100",MENU)
        self.assertNotIn("i<4?8+i*18:-100",MENU)
        self.assertIn("private static final int SIDE_X=183",PANEL)
        self.assertIn("private static final int SIDE_W=88",PANEL)

    def test_exactly_four_slot_names_and_screen_registration(self):
        for name in ("MAGNET","CELL 1","CELL 2","CELL 3"):
            self.assertIn(name,PANEL)
        self.assertIn("xsxV176BackpackScreen",PANEL)
        self.assertIn("new dev.obsidiannetwork.client.V176BackpackScreen",PANEL)

if __name__=="__main__":
    unittest.main()
