import unittest
import os
import json
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules import load_config

class TestConfig(unittest.TestCase):
    def setUp(self):
        self.test_file = "test_config.json"
        with open(self.test_file, "w", encoding="utf-8") as f:
            json.dump({"key": "value"}, f)

    def tearDown(self):
        os.remove(self.test_file)

    def test_load_config_success(self):
        config = load_config(self.test_file)
        self.assertEqual(config["key"], "value")
