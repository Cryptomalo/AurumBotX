import os
import json
import hashlib
import shutil
import subprocess
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import requests # Moved to top
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("/home/ubuntu/AurumBotX/logs/updater.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class UpdateManager:
    """Manages automatic updates for AurumBotX."""

    def __init__(self, config_path: str = None):
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.config_path = Path(config_path) if config_path else self.base_dir / "config" / "updater_config.json"
        self.config = self._load_config()
        self.current_version = self.config.get("current_version", "1.0.0")
        self.update_server_url = self.config.get("update_server_url")
        self.update_channel = self.config.get("update_channel", "stable")
        self.backup_dir = self.base_dir / "_backup_aurumbotx"
        self.temp_download_dir = self.base_dir / "_temp_update"

        if not self.update_server_url:
            logger.error("Update server URL is not configured.")
            raise ValueError("Update server URL must be set in updater_config.json")

    def _load_config(self) -> Dict[str, Any]:
        """Loads the updater configuration from a JSON file."""
        if self.config_path.is_file():
            with open(self.config_path, "r") as f:
                return json.load(f)
        else:
            logger.warning(
                f"Config file not found at {self.config_path}. Creating default."
            )
            default_config = {
                "current_version": "1.0.0",
                "update_server_url": "https://updates.aurumbotx.com",  # Placeholder
                "update_channel": "stable",  # stable, beta, alpha
                "auto_update_enabled": True,
                "check_interval_hours": 24,
                "last_check": None,
            }
            os.makedirs(self.config_path.parent, exist_ok=True)
            with open(self.config_path, "w") as f:
                json.dump(default_config, f, indent=4)
            return default_config

    def _save_config(self):
        """Saves the current configuration to the JSON file."""
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=4)

    def _get_remote_manifest(self) -> Optional[Dict[str, Any]]:
        """Fetches the latest update manifest from the server."""
        try:
            manifest_url = f"{self.update_server_url}/{self.update_channel}/manifest.json"
            logger.info(f"Fetching manifest from: {manifest_url}")
            response = requests.get(manifest_url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch update manifest: {e}")
            return None

    def _download_update(self, update_info: Dict[str, Any]) -> Optional[Path]:
        """Downloads the update package."""
        try:
            update_url = f"{self.update_server_url}/{self.update_channel}/{update_info['filename']}"
            logger.info(f"Downloading update from: {update_url}")

            self.temp_download_dir.mkdir(parents=True, exist_ok=True)
            download_path = self.temp_download_dir / update_info["filename"]

            with requests.get(update_url, stream=True, timeout=300) as r:
                r.raise_for_status()
                with open(download_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

            # Verify checksum
            if self._calculate_sha256(download_path) != update_info["sha256"]:
                logger.error("Downloaded file checksum mismatch. Aborting update.")
                shutil.rmtree(self.temp_download_dir)
                return None

            logger.info(f"Update downloaded successfully to {download_path}")
            return download_path
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download update: {e}")
            if self.temp_download_dir.exists():
                shutil.rmtree(self.temp_download_dir)
            return None

    def _calculate_sha256(self, file_path: Path) -> str:
        """Calculates the SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _create_backup(self):
        """Creates a backup of the current installation."""
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)  # Clear previous backup
        shutil.copytree(self.base_dir, self.backup_dir, ignore=shutil.ignore_patterns("_backup_aurumbotx", "_temp_update", "logs"))
        logger.info(f"Backup created at {self.backup_dir}")

    def _apply_update(self, update_package_path: Path) -> bool:
        """Applies the downloaded update."""
        try:
            logger.info("Applying update...")
            self._create_backup()

            # Extract the update package
            shutil.unpack_archive(update_package_path, self.temp_download_dir, "zip")

            # Assuming the zip contains the new version in a subfolder, e.g., 'AurumBotX-vX.Y.Z'
            # Find the actual content directory within the extracted folder
            update_content_dir = None
            for item in self.temp_download_dir.iterdir():
                if item.is_dir() and item.name.startswith("AurumBotX-"):
                    update_content_dir = item
                    break
            
            if not update_content_dir:
                logger.error("Could not find update content directory within the extracted package.")
                self._rollback()
                return False

            # Copy new files over old ones
            for src in update_content_dir.glob("**/*"):
                if src.is_file():
                    relative_path = src.relative_to(update_content_dir)
                    dest = self.base_dir / relative_path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest)
                elif src.is_dir():
                    relative_path = src.relative_to(update_content_dir)
                    dest = self.base_dir / relative_path
                    dest.mkdir(parents=True, exist_ok=True)

            logger.info("Update applied successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to apply update: {e}")
            self._rollback()
            return False
        finally:
            if self.temp_download_dir.exists():
                shutil.rmtree(self.temp_download_dir)

    def _rollback(self):
        """Rolls back to the previous version from backup."""
        if self.backup_dir.exists():
            logger.warning("Rolling back to previous version...")
            for item in self.base_dir.iterdir():
                if item.name not in [self.backup_dir.name, self.temp_download_dir.name, "logs"]:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
            shutil.copytree(self.backup_dir, self.base_dir, dirs_exist_ok=True)
            shutil.rmtree(self.backup_dir)
            logger.info("Rollback completed successfully.")
        else:
            logger.error("No backup found for rollback.")

    def _restart_application(self):
        """Restarts the main AurumBotX application."""
        logger.info("Restarting AurumBotX application...")
        # This would depend on how the main application is started.
        # For a simple Python script, you might re-execute it.
        # For a more complex system (e.g., systemd service), you'd use systemctl.
        # Example for simple Python script:
        python_executable = sys.executable
        main_script = self.base_dir / "start_trading.py" # Assuming this is your main entry point
        if main_script.exists():
            subprocess.Popen([python_executable, main_script])
            os._exit(0) # Exit current process
        else:
            logger.warning("Could not find main application script to restart.")

    def check_for_updates(self, force: bool = False) -> bool:
        """Checks for available updates and initiates the update process if found."""
        if not self.config.get("auto_update_enabled") and not force:
            logger.info("Auto-update is disabled. Skipping check.")
            return False

        last_check_str = self.config.get("last_check")
        if last_check_str:
            last_check_time = datetime.fromisoformat(last_check_str)
            if (datetime.now() - last_check_time) < timedelta(hours=self.config.get("check_interval_hours", 24)) and not force:
                logger.info("Update check interval not yet passed. Skipping.")
                return False

        logger.info("Checking for updates...")
        self.config["last_check"] = datetime.now().isoformat()
        self._save_config()

        manifest = self._get_remote_manifest()
        if not manifest:
            logger.warning("Could not retrieve update manifest.")
            return False

        latest_version = manifest.get("latest_version")
        update_info = manifest.get("updates", {}).get(latest_version)

        if not latest_version or not update_info:
            logger.warning("No latest version or update info found in manifest.")
            return False

        if latest_version > self.current_version:
            logger.info(f"New version {latest_version} available. Current: {self.current_version}")
            download_path = self._download_update(update_info)
            if download_path:
                if self._apply_update(download_path):
                    self.config["current_version"] = latest_version
                    self._save_config()
                    logger.info(f"Successfully updated to version {latest_version}")
                    # self._restart_application() # Consider how to restart the main app safely
                    return True
                else:
                    logger.error("Update failed, rollback initiated.")
            return False
        else:
            logger.info(f"AurumBotX is already up to date (version {self.current_version}).")
            return False

    def set_update_channel(self, channel: str):
        """Sets the update channel (stable, beta, alpha)."""
        if channel in ["stable", "beta", "alpha"]:
            self.update_channel = channel
            self.config["update_channel"] = channel
            self._save_config()
            logger.info(f"Update channel set to: {channel}")
        else:
            logger.warning(f"Invalid update channel: {channel}. Must be stable, beta, or alpha.")

    def enable_auto_update(self, enable: bool):
        """Enables or disables automatic updates."""
        self.config["auto_update_enabled"] = enable
        self._save_config()
        logger.info(f"Auto-update {'enabled' if enable else 'disabled'}.")

    def get_status(self) -> Dict[str, Any]:
        """Returns the current status of the update manager."""
        return {
            "current_version": self.current_version,
            "update_channel": self.update_channel,
            "auto_update_enabled": self.config.get("auto_update_enabled"),
            "last_check": self.config.get("last_check"),
            "update_server_url": self.update_server_url,
        }


if __name__ == "__main__":
    # Example usage:
    # To run this, you'd typically have a web server serving manifest.json and update zips
    # For testing, you might mock requests or run a local simple HTTP server
    
    # Ensure requests is installed: pip install requests
    
    # Create a dummy config file if it doesn't exist
    config_dir = Path(__file__).resolve().parent.parent.parent / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    dummy_config_path = config_dir / "updater_config.json"
    if not dummy_config_path.exists():
        with open(dummy_config_path, "w") as f:
            json.dump({
                "current_version": "1.0.0",
                "update_server_url": "http://localhost:8000", # Point to a local server for testing
                "update_channel": "stable",
                "auto_update_enabled": True,
                "check_interval_hours": 1,
                "last_check": None,
            }, f, indent=4)
    
    # Create a dummy update server directory for testing
    # In a real scenario, this would be a remote HTTP server
    update_server_root = Path("/tmp/aurumbotx_updates")
    update_server_root.mkdir(parents=True, exist_ok=True)
    (update_server_root / "stable").mkdir(exist_ok=True)
    
    # Create a dummy manifest for the stable channel
    dummy_manifest = {
        "latest_version": "1.0.1",
        "updates": {
            "1.0.1": {
                "filename": "AurumBotX-1.0.1.zip",
                "sha256": "a77a94205561a06700c8f14959a4c5145781a712217c2448373b5735232a9000" # Dummy hash
            }
        }
    }
    with open(update_server_root / "stable" / "manifest.json", "w") as f:
        json.dump(dummy_manifest, f, indent=4)
        
    # Create a dummy update zip file
    # This would contain the actual files for the new version
    dummy_update_content_dir = Path("/tmp/new_version_content")
    dummy_update_content_dir.mkdir(exist_ok=True)
    (dummy_update_content_dir / "new_feature.txt").write_text("This is a new feature in 1.0.1")
    shutil.make_archive(update_server_root / "stable" / "AurumBotX-1.0.1", "zip", root_dir=dummy_update_content_dir)
    
    # Recalculate SHA256 for the dummy zip
    zip_path = update_server_root / "stable" / "AurumBotX-1.0.1.zip"
    if zip_path.exists():
        dummy_manifest["updates"]["1.0.1"]["sha256"] = UpdateManager(str(dummy_config_path))._calculate_sha256(zip_path)
        with open(update_server_root / "stable" / "manifest.json", "w") as f:
            json.dump(dummy_manifest, f, indent=4)
            
    logger.info(f"Dummy update server setup at {update_server_root}")
    logger.info("You can run a simple HTTP server in that directory: python3 -m http.server 8000")
    
    # Initialize and run the update manager
    updater = UpdateManager(str(dummy_config_path))
    updater.check_for_updates(force=True)
    
    print("\nUpdater Status:")
    print(json.dumps(updater.get_status(), indent=4))

    # Clean up dummy files
    # shutil.rmtree(update_server_root)
    # shutil.rmtree(dummy_update_content_dir)
    # dummy_config_path.unlink()
