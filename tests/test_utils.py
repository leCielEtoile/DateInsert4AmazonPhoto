import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import extract_date_and_time_from_filename

class TestExtractDateAndTime(unittest.TestCase):
    def test_valid_filename(self):
        filename = "VRChat_2024-03-25_14-05-00.png"
        expected_date = "2024-03-25"
        expected_time = "午後2時5分"
        self.assertEqual(extract_date_and_time_from_filename(filename), (expected_date, expected_time))

    def test_midnight(self):
        filename = "VRChat_2024-03-25_00-30-00.png"
        expected_time = "午前0時30分"
        self.assertEqual(extract_date_and_time_from_filename(filename)[1], expected_time)

    def test_invalid_filename(self):
        filename = "Screenshot_2024-03-25.png"
        self.assertEqual(extract_date_and_time_from_filename(filename), (None, None))

if __name__ == "__main__":
    unittest.main()
