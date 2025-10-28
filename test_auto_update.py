import unittest
import os
import json
import shutil
from unittest.mock import patch, MagicMock
from pathlib import Path
from datetime import datetime, timedelta
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.updater.update_manager import UpdateManager

class TestUpdateManager(unittest.TestCase):

    def setUp(self):
        """Set up a temporary testing environment."""
        self.test_dir = Path("/tmp/test_aurumbotx_update")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir(parents=True, exist_ok=True)

        # --- Create a dummy project structure to be updated ---
        self.config_dir = self.test_dir / "config"
        self.config_dir.mkdir()
        self.logs_dir = self.test_dir / "logs"
        self.logs_dir.mkdir()
        (self.test_dir / "old_file.txt").write_text("This is an old file.")

        # --- Create a dummy updater config ---
        self.config_path = self.config_dir / "updater_config.json"
        self.default_config = {
            "current_version": "1.0.0",
            "update_server_url": "http://mock-server.com",
            "update_channel": "stable",
            "auto_update_enabled": True,
            "check_interval_hours": 1,
            "last_check": None,
        }
        with open(self.config_path, "w") as f:
            json.dump(self.default_config, f, indent=4)

        # --- Create a dummy update package (zip file) ---
        self.dummy_update_content_dir = self.test_dir / "new_version_source"
        self.dummy_update_content_dir.mkdir()
        # This is the structure the updater expects inside the zip
        update_root_in_zip = self.dummy_update_content_dir / "AurumBotX-1.0.1"
        update_root_in_zip.mkdir()
        (update_root_in_zip / "new_feature.txt").write_text("This is the new feature!")
        (update_root_in_zip / "old_file.txt").write_text("This is the updated old file.")

        self.zip_path = self.test_dir / "AurumBotX-1.0.1.zip"
        shutil.make_archive(str(self.zip_path).replace(".zip", ""), "zip", str(self.dummy_update_content_dir))

        # --- Initialize the updater for testing ---
        self.updater = UpdateManager(str(self.config_path))
        # IMPORTANT: Redirect paths to the temporary test directory
        self.updater.base_dir = self.test_dir
        self.updater.backup_dir = self.test_dir / "_backup_aurumbotx"
        self.updater.temp_download_dir = self.test_dir / "_temp_update"

    def tearDown(self):
        """Clean up the testing environment."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    @patch("src.updater.update_manager.UpdateManager._get_remote_manifest")
    def test_check_for_updates_no_new_version(self, mock_get_manifest):
        """Test that no update occurs if the version is current."""
        mock_get_manifest.return_value = {"latest_version": "1.0.0"}
        
        result = self.updater.check_for_updates()
        
        self.assertFalse(result)
        self.assertEqual(self.updater.current_version, "1.0.0")

    @patch("src.updater.update_manager.UpdateManager._download_update")
    @patch("src.updater.update_manager.UpdateManager._get_remote_manifest")
    def test_check_for_updates_new_version_available(self, mock_get_manifest, mock_download_update):
        """Test the full update process when a new version is found."""
        # --- Mock external calls ---
        manifest = {
            "latest_version": "1.0.1",
            "updates": {
                "1.0.1": {
                    "filename": "AurumBotX-1.0.1.zip",
                    "sha256": self.updater._calculate_sha256(self.zip_path)
                }
            }
        }
        mock_get_manifest.return_value = manifest
        mock_download_update.return_value = self.zip_path # Simulate successful download

        # --- Run the update check ---
        result = self.updater.check_for_updates()

        # --- Assertions ---
        self.assertTrue(result)
        mock_get_manifest.assert_called_once()
        mock_download_update.assert_called_once()

        # Check that config file is updated
        # Reload the updater to get the new version from the config file
        reloaded_updater = UpdateManager(str(self.config_path))
        reloaded_updater.base_dir = self.test_dir
        self.assertEqual(reloaded_updater.get_status()["current_version"], "1.0.1")

        # Check that files were correctly updated
        self.assertTrue((self.test_dir / "new_feature.txt").exists())
        self.assertEqual((self.test_dir / "old_file.txt").read_text(), "This is the updated old file.")

    def test_set_update_channel(self):
        """Test changing the update channel."""
        self.updater.set_update_channel("beta")
        self.assertEqual(self.updater.get_status()["update_channel"], "beta")
        # Verify it was saved to the config file
        with open(self.config_path, "r") as f:
            config_data = json.load(f)
        self.assertEqual(config_data["update_channel"], "beta")

    def test_enable_auto_update(self):
        """Test enabling and disabling auto-updates."""
        self.updater.enable_auto_update(False)
        self.assertFalse(self.updater.get_status()["auto_update_enabled"])
        
        self.updater.enable_auto_update(True)
        self.assertTrue(self.updater.get_status()["auto_update_enabled"])

if __name__ == "__main__":
    unittest.main()
