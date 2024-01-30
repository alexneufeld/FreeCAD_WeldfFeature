from freecad import app as FreeCAD
import Part
from freecad.weldfeature import geom_utils
import unittest


class TestRoundVector(unittest.TestCase):
    def test_zero(self):
        vec = FreeCAD.Vector()
        self.assertEqual(vec, geom_utils.round_vector(vec))

    def test_rounding(self):
        vec = FreeCAD.Vector(2.123451, 123.004, 0.0)
        other_vec = FreeCAD.Vector(2.12345, 123.004, 0.0)
        self.assertEqual(other_vec, geom_utils.round_vector(vec, ndigits=5))


class TestShouldFlipEdge(unittest.TestCase):
    def test_fails_on_unconnected_edges(self):
        e1 = Part.makeLine(FreeCAD.Vector(0.0, 1.0, 2.0), FreeCAD.Vector(0.0, 2.0, 2.0))
        e2 = Part.makeLine(FreeCAD.Vector(1.0, 1.0, 2.0), FreeCAD.Vector(1.0, 2.0, 2.0))
        with self.assertRaises(RuntimeError):
            geom_utils.should_flip_edges(e1, e2)

    def test_flips_second_reversed_edge(self):
        v1 = FreeCAD.Vector(0.0, 1.0, 2.0)
        v2 = FreeCAD.Vector(1.0, 1.0, 2.0)
        v3 = FreeCAD.Vector(1.0, 1.0, 3.0)
        e1 = Part.makeLine(v1, v2)
        e2 = Part.makeLine(v3, v2)
        self.assertEqual(geom_utils.should_flip_edges(e1, e2), (False, True))

    def doesnt_flip_correct_edges(self):
        v1 = FreeCAD.Vector(0.0, 1.0, 2.0)
        v2 = FreeCAD.Vector(1.0, 1.0, 2.0)
        v3 = FreeCAD.Vector(1.0, 1.0, 3.0)
        e1 = Part.makeLine(v1, v2)
        e2 = Part.makeLine(v2, v3)
        self.assertEqual(geom_utils.should_flip_edges(e1, e2), (False, False))

    def works_with_fuzzy_coincidence(self):
        v1 = FreeCAD.Vector(0.0, 1.0, 2.0)
        v2 = FreeCAD.Vector(1.0, 1.0, 2.0)
        almost_v2 = FreeCAD.Vector(1.0, 1.000001, 2.0)
        v3 = FreeCAD.Vector(1.0, 1.0, 3.0)
        e1 = Part.makeLine(v1, v2)
        e2 = Part.makeLine(v3, almost_v2)
        self.assertEqual(geom_utils.should_flip_edges(e1, e2), (False, True))


if __name__ == "__main__":
    unittest.main()
