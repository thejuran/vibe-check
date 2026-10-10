import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                os.pardir, "src"))

from clamp import clamp, describe_range, width  # noqa: E402


class TestClamp(unittest.TestCase):
    def test_inside_range_is_unchanged(self):
        self.assertEqual(clamp(3, 0, 5), 3)

    def test_below_range_returns_lo(self):
        self.assertEqual(clamp(-4, 0, 5), 0)

    def test_above_range_returns_hi(self):
        self.assertEqual(clamp(10, 0, 5), 5)

    def test_upper_bound_itself_is_kept(self):
        self.assertEqual(clamp(5, 0, 5), 5)

    def test_empty_range_raises(self):
        with self.assertRaises(ValueError):
            clamp(1, 5, 0)


class TestDescribeRange(unittest.TestCase):
    def test_width(self):
        self.assertEqual(width(0, 5), 6)
        self.assertEqual(width(5, 0), 0)

    def test_labels(self):
        self.assertEqual(describe_range(2, 2), "exactly 2")
        self.assertEqual(describe_range(0, 5), "from 0 to 5 (6 values)")


if __name__ == "__main__":
    unittest.main()
