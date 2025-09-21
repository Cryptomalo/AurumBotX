#!/usr/bin/env python3
"""
AurumBotX Auto-Updater System
Automatic online updates for AurumBotX trading system

Author: AurumBotX Team
Date: 13 Settembre 2025
Version: 2.0
"""

import os
import sys
import json
import time
import requests
import zipfile
import shutil
import subprocess
import threading
from pathlib import Path
from datetime import datetime, timedelta
import hashlib
import tempfile

class AurumBotXUpdater:
    def __init__(self):
        self.current_dir = Path(__file__).parent.parent.parent
        self.version_file = self.current_dir / "VERSION"
        self.config_file = self.current_dir / "config" / "updater_config.json"
        self.backup_dir = self.current_dir / "backups"
        self.temp_dir = Path(tempfile.gettempdir()) / "aurumbotx_updates"
        
        # Update server configuration
        self.update_server = "https://updates.aurumbotx.ai"
        self.github_repo = "https://api.github.com/repos/aurumbotx/aurumbotx"
        self.fallback_server = "https://backup-updates.aurumbotx.ai"
        
        # Current version
        self.current_version = self.get_current_version()
        
        # Update configuration
        self.config = self.load_config()
        
        print(f"🔄 AurumBotX Auto-Updater v2.0")
        print(f"📦 Current Version: {self.current_version}")
        print(f"🌐 Update Server: {self.update_server}")
    
    def get_current_version(self):
        """Get current version"""
        if self.version_file.exists():
            try:
                with open(self.version_file, 'r') as f:
                    return f.read().strip()
            except:
                pass
        return "2.0.0"
    
    def load_config(self):
        """Load updater configuration"""
        default_config = {
            "auto_check": True,
            "check_interval_hours": 6,
            "auto_download": True,
            "auto_install": False,
            "backup_before_update": True,
            "max_backups": 5,
            "update_channel": "stable",
            "last_check": None,
            "notifications": True,
            "rollback_enabled": True
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except:
                pass
        
        # Create config directory and file
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.save_config(default_config)
        return default_config
    
    def save_config(self, config=None):
        """Save updater configuration"""
        if config is None:
            config = self.config
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save config: {e}")
    
    def check_for_updates(self):
        """Check for available updates"""
        print("🔍 Checking for updates...")
        
        try:
            # Update last check time
            self.config["last_check"] = datetime.now().isoformat()
            self.save_config()
            
            # Check multiple sources
            update_info = None
            
            # Try primary update server
            try:
                update_info = self.check_update_server()
                print("✅ Connected to primary update server")
            except:
                print("⚠️ Primary server unavailable, trying GitHub...")
                
                # Try GitHub releases
                try:
                    update_info = self.check_github_releases()
                    print("✅ Connected to GitHub releases")
                except:
                    print("⚠️ GitHub unavailable, trying fallback...")
                    
                    # Try fallback server
                    try:
                        update_info = self.check_fallback_server()
                        print("✅ Connected to fallback server")
                    except:
                        print("❌ All update servers unavailable")
                        return None
            
            if update_info:
                latest_version = update_info.get("version")
                if self.is_newer_version(latest_version, self.current_version):
                    print(f"🎉 New version available: {latest_version}")
                    return update_info
                else:
                    print(f"✅ Already up to date: {self.current_version}")
                    return None
            
        except Exception as e:
            print(f"❌ Update check failed: {e}")
            return None
    
    def check_update_server(self):
        """Check primary update server"""
        url = f"{self.update_server}/api/v1/check-update"
        params = {
            "current_version": self.current_version,
            "channel": self.config["update_channel"],
            "platform": sys.platform
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        return response.json()
    
    def check_github_releases(self):
        """Check GitHub releases"""
        url = f"{self.github_repo}/releases/latest"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        release_data = response.json()
        
        # Find appropriate asset
        download_url = None
        for asset in release_data.get("assets", []):
            if "AurumBotX" in asset["name"] and asset["name"].endswith(".zip"):
                download_url = asset["browser_download_url"]
                break
        
        if not download_url:
            # Fallback to source code
            download_url = release_data["zipball_url"]
        
        return {
            "version": release_data["tag_name"].lstrip("v"),
            "download_url": download_url,
            "changelog": release_data.get("body", ""),
            "size": sum(asset.get("size", 0) for asset in release_data.get("assets", [])),
            "published_at": release_data["published_at"]
        }
    
    def check_fallback_server(self):
        """Check fallback update server"""
        url = f"{self.fallback_server}/latest.json"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        return response.json()
    
    def is_newer_version(self, latest, current):
        """Compare version numbers"""
        try:
            latest_parts = [int(x) for x in latest.split('.')]
            current_parts = [int(x) for x in current.split('.')]
            
            # Pad shorter version with zeros
            max_len = max(len(latest_parts), len(current_parts))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))
            
            return latest_parts > current_parts
        except:
            return latest != current
    
    def download_update(self, update_info):
        """Download update package"""
        print(f"⬇️ Downloading update {update_info['version']}...")
        
        try:
            # Create temp directory
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Download file
            download_url = update_info["download_url"]
            filename = f"aurumbotx-{update_info['version']}.zip"
            download_path = self.temp_dir / filename
            
            # Download with progress
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\r📥 Progress: {progress:.1f}%", end="", flush=True)
            
            print(f"\n✅ Download completed: {download_path}")
            
            # Verify download
            if self.verify_download(download_path, update_info):
                return download_path
            else:
                print("❌ Download verification failed")
                return None
                
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return None
    
    def verify_download(self, file_path, update_info):
        """Verify downloaded file"""
        try:
            # Check file size
            file_size = file_path.stat().st_size
            expected_size = update_info.get("size")
            
            if expected_size and abs(file_size - expected_size) > 1024:  # 1KB tolerance
                print(f"⚠️ Size mismatch: {file_size} vs {expected_size}")
                return False
            
            # Check if it's a valid zip
            try:
                with zipfile.ZipFile(file_path, 'r') as zf:
                    zf.testzip()
                print("✅ ZIP file integrity verified")
                return True
            except zipfile.BadZipFile:
                print("❌ Invalid ZIP file")
                return False
                
        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return False
    
    def create_backup(self):
        """Create backup of current installation"""
        if not self.config["backup_before_update"]:
            return True
        
        print("💾 Creating backup...")
        
        try:
            # Create backup directory
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"aurumbotx_backup_{self.current_version}_{timestamp}.zip"
            backup_path = self.backup_dir / backup_name
            
            # Create backup zip
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(self.current_dir):
                    # Skip backup and temp directories
                    root_path = Path(root)
                    if any(skip in root_path.parts for skip in ['backups', 'temp', '__pycache__', '.git']):
                        continue
                    
                    for file in files:
                        file_path = Path(root) / file
                        if file_path.suffix not in ['.pyc', '.pyo', '.log']:
                            arcname = file_path.relative_to(self.current_dir)
                            zf.write(file_path, arcname)
            
            print(f"✅ Backup created: {backup_path}")
            
            # Clean old backups
            self.cleanup_old_backups()
            
            return True
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False
    
    def cleanup_old_backups(self):
        """Remove old backup files"""
        try:
            if not self.backup_dir.exists():
                return
            
            # Get all backup files
            backups = list(self.backup_dir.glob("aurumbotx_backup_*.zip"))
            backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Keep only max_backups
            max_backups = self.config["max_backups"]
            if len(backups) > max_backups:
                for backup in backups[max_backups:]:
                    backup.unlink()
                    print(f"🗑️ Removed old backup: {backup.name}")
                    
        except Exception as e:
            print(f"⚠️ Backup cleanup failed: {e}")
    
    def install_update(self, update_path, update_info):
        """Install downloaded update"""
        print(f"🔧 Installing update {update_info['version']}...")
        
        try:
            # Create backup first
            if not self.create_backup():
                print("❌ Backup failed, aborting update")
                return False
            
            # Extract update
            extract_dir = self.temp_dir / "extract"
            extract_dir.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(update_path, 'r') as zf:
                zf.extractall(extract_dir)
            
            print("📦 Update extracted")
            
            # Find source directory in extracted files
            source_dirs = [d for d in extract_dir.iterdir() if d.is_dir()]
            if len(source_dirs) == 1:
                source_dir = source_dirs[0]
            else:
                source_dir = extract_dir
            
            # Copy files (excluding user data)
            self.copy_update_files(source_dir)
            
            # Update version file
            new_version_file = self.current_dir / "VERSION"
            with open(new_version_file, 'w') as f:
                f.write(update_info['version'])
            
            print(f"✅ Update installed successfully!")
            print(f"📦 Version: {self.current_version} → {update_info['version']}")
            
            # Cleanup temp files
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            
            return True
            
        except Exception as e:
            print(f"❌ Installation failed: {e}")
            return False
    
    def copy_update_files(self, source_dir):
        """Copy update files while preserving user data"""
        print("📋 Copying update files...")
        
        # Directories to preserve (user data)
        preserve_dirs = {'config', 'data', 'logs', 'backups'}
        preserve_files = {'.env', '.env.mainnet', 'user_settings.json'}
        
        for item in source_dir.rglob('*'):
            if item.is_file():
                # Calculate relative path
                rel_path = item.relative_to(source_dir)
                target_path = self.current_dir / rel_path
                
                # Skip preserved files/directories
                if any(part in preserve_dirs for part in rel_path.parts):
                    if target_path.exists():
                        continue  # Don't overwrite user data
                
                if rel_path.name in preserve_files:
                    if target_path.exists():
                        continue  # Don't overwrite user settings
                
                # Create target directory
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                shutil.copy2(item, target_path)
        
        print("✅ Files copied successfully")
    
    def rollback_update(self, backup_name=None):
        """Rollback to previous version"""
        print("🔄 Rolling back update...")
        
        try:
            if not self.backup_dir.exists():
                print("❌ No backups available")
                return False
            
            # Find backup to restore
            if backup_name:
                backup_path = self.backup_dir / backup_name
            else:
                # Use most recent backup
                backups = list(self.backup_dir.glob("aurumbotx_backup_*.zip"))
                if not backups:
                    print("❌ No backups found")
                    return False
                
                backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                backup_path = backups[0]
            
            if not backup_path.exists():
                print(f"❌ Backup not found: {backup_path}")
                return False
            
            print(f"📦 Restoring from: {backup_path.name}")
            
            # Extract backup
            extract_dir = self.temp_dir / "rollback"
            extract_dir.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(backup_path, 'r') as zf:
                zf.extractall(extract_dir)
            
            # Copy files back
            for item in extract_dir.rglob('*'):
                if item.is_file():
                    rel_path = item.relative_to(extract_dir)
                    target_path = self.current_dir / rel_path
                    
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, target_path)
            
            print("✅ Rollback completed successfully")
            
            # Cleanup
            shutil.rmtree(extract_dir, ignore_errors=True)
            
            return True
            
        except Exception as e:
            print(f"❌ Rollback failed: {e}")
            return False
    
    def auto_update_loop(self):
        """Automatic update checking loop"""
        print("🔄 Starting auto-update service...")
        
        while True:
            try:
                if self.config["auto_check"]:
                    # Check if it's time for update check
                    last_check = self.config.get("last_check")
                    if last_check:
                        last_check_time = datetime.fromisoformat(last_check)
                        next_check = last_check_time + timedelta(hours=self.config["check_interval_hours"])
                        
                        if datetime.now() < next_check:
                            time.sleep(300)  # Check every 5 minutes
                            continue
                    
                    # Check for updates
                    update_info = self.check_for_updates()
                    
                    if update_info:
                        print(f"🎉 New version available: {update_info['version']}")
                        
                        if self.config["auto_download"]:
                            download_path = self.download_update(update_info)
                            
                            if download_path and self.config["auto_install"]:
                                if self.install_update(download_path, update_info):
                                    print("🎉 Auto-update completed!")
                                    # Restart application
                                    self.restart_application()
                                    break
                            elif download_path:
                                print("📥 Update downloaded, waiting for manual installation")
                        else:
                            print("📢 Update available, auto-download disabled")
                
                # Sleep before next check
                time.sleep(300)  # 5 minutes
                
            except KeyboardInterrupt:
                print("\n👋 Auto-update service stopped")
                break
            except Exception as e:
                print(f"⚠️ Auto-update error: {e}")
                time.sleep(300)
    
    def restart_application(self):
        """Restart the application after update"""
        print("🔄 Restarting application...")
        
        try:
            # Find main application file
            main_files = [
                "aurumbotx_gui.py",
                "start_mainnet_demo.py",
                "aurumbotx_app.py"
            ]
            
            for main_file in main_files:
                main_path = self.current_dir / main_file
                if main_path.exists():
                    # Start new process
                    subprocess.Popen([sys.executable, str(main_path)])
                    break
            
            # Exit current process
            sys.exit(0)
            
        except Exception as e:
            print(f"⚠️ Restart failed: {e}")
    
    def get_update_status(self):
        """Get current update status"""
        return {
            "current_version": self.current_version,
            "last_check": self.config.get("last_check"),
            "auto_check_enabled": self.config["auto_check"],
            "check_interval_hours": self.config["check_interval_hours"],
            "auto_download": self.config["auto_download"],
            "auto_install": self.config["auto_install"],
            "update_channel": self.config["update_channel"],
            "backups_available": len(list(self.backup_dir.glob("*.zip"))) if self.backup_dir.exists() else 0
        }

def main():
    """Main updater function"""
    updater = AurumBotXUpdater()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "check":
            update_info = updater.check_for_updates()
            if update_info:
                print(f"🎉 Update available: {update_info['version']}")
            else:
                print("✅ No updates available")
        
        elif command == "download":
            update_info = updater.check_for_updates()
            if update_info:
                updater.download_update(update_info)
        
        elif command == "install":
            # Install latest downloaded update
            update_files = list(updater.temp_dir.glob("aurumbotx-*.zip"))
            if update_files:
                latest_update = max(update_files, key=lambda x: x.stat().st_mtime)
                # Extract version from filename
                version = latest_update.stem.split('-')[1]
                update_info = {"version": version}
                updater.install_update(latest_update, update_info)
            else:
                print("❌ No downloaded updates found")
        
        elif command == "rollback":
            updater.rollback_update()
        
        elif command == "status":
            status = updater.get_update_status()
            print(json.dumps(status, indent=2))
        
        elif command == "auto":
            updater.auto_update_loop()
        
        else:
            print("Usage: python auto_updater.py [check|download|install|rollback|status|auto]")
    
    else:
        # Interactive mode
        print("\n🔄 AurumBotX Auto-Updater")
        print("1. Check for updates")
        print("2. Download updates")
        print("3. Install updates")
        print("4. Rollback update")
        print("5. Update status")
        print("6. Start auto-update service")
        
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == "1":
            updater.check_for_updates()
        elif choice == "2":
            update_info = updater.check_for_updates()
            if update_info:
                updater.download_update(update_info)
        elif choice == "3":
            update_files = list(updater.temp_dir.glob("aurumbotx-*.zip"))
            if update_files:
                latest_update = max(update_files, key=lambda x: x.stat().st_mtime)
                version = latest_update.stem.split('-')[1]
                update_info = {"version": version}
                updater.install_update(latest_update, update_info)
        elif choice == "4":
            updater.rollback_update()
        elif choice == "5":
            status = updater.get_update_status()
            print(json.dumps(status, indent=2))
        elif choice == "6":
            updater.auto_update_loop()

if __name__ == "__main__":
    main()

