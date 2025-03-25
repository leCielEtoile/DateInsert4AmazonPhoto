import unittest
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules import download_latest_geckodriver

class TestGeckoDriver(unittest.TestCase):
    @patch("modules.geckodriver.requests.get")
    def test_download_skipped_if_exists(self, mock_get):
        """
        geckodriver.exe が既に存在している場合、ダウンロード処理をスキップすることを確認
        """
        test_dir = "test_dir"
        os.makedirs(test_dir, exist_ok=True)

        fake_path = os.path.join(test_dir, "geckodriver.exe")
        with open(fake_path, "w") as f:
            f.write("dummy")

        result_path = download_latest_geckodriver(test_dir)

        self.assertEqual(os.path.normpath(result_path), os.path.normpath(fake_path))

        os.remove(fake_path)
        os.rmdir(test_dir)

if __name__ == "__main__":
    unittest.main()
