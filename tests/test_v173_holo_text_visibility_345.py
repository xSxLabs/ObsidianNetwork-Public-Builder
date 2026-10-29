import ast
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
P = ROOT / "features/v173/apply-holo-text-visibility-345.py"


class TestHologramVisibility345(unittest.TestCase):
    def test_python_syntax(self):
        ast.parse(P.read_text(encoding="utf-8"))

    def test_render_visibility_and_access_transformer(self):
        s = P.read_text(encoding="utf-8")
        for marker in (
            'V173_B345_HOLO_VISIBLE',
            'entity.setFlags((byte)2)',
            'entity.setWidth(',
            'entity.setHeight(',
            'entity.setViewRange(4F)',
            'Display$TextDisplay setFlags(B)V',
            'Display setWidth(F)V',
            'Display setHeight(F)V',
            'Display setViewRange(F)V',
            'source.count(anchor) == 1',
        ):
            self.assertIn(marker, s)

    def test_visual_only_scope(self):
        s = P.read_text(encoding="utf-8")
        self.assertNotIn("level.setBlock(", s)
        self.assertNotIn("setBlockAndUpdate(", s)
        self.assertNotIn("storageCell", s)
        self.assertNotIn("network.insert", s)


if __name__ == "__main__":
    unittest.main()
