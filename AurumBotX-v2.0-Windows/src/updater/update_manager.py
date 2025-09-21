#!/usr/bin/env python3
"""
AurumBotX Update Manager
Integrated update management for GUI application

Author: AurumBotX Team
Date: 13 Settembre 2025
Version: 2.0
"""

import os
import sys
import json
import threading
import time
from pathlib import Path
from datetime import datetime
import requests

# Add parent directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent.parent))

from src.updater.auto_updater import AurumBotXUpdater

class UpdateManager:
    def __init__(self, gui_callback=None):
        self.updater = AurumBotXUpdater()
        self.gui_callback = gui_callback
        self.update_thread = None
        self.checking = False
        self.downloading = False
        self.installing = False
        
        # Update notifications
        self.notifications = []
        
        print("🔄 Update Manager initialized")
    
    def set_gui_callback(self, callback):
        """Set GUI callback for notifications"""
        self.gui_callback = callback
    
    def notify_gui(self, message, type="info"):
        """Send notification to GUI"""
        notification = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "type": type
        }
        
        self.notifications.append(notification)
        
        if self.gui_callback:
            try:
                self.gui_callback(notification)
            except Exception as e:
                print(f"⚠️ GUI callback failed: {e}")
        
        print(f"📢 {message}")
    
    def check_updates_async(self):
        """Check for updates asynchronously"""
        if self.checking:
            return False
        
        def check_thread():
            self.checking = True
            try:
                self.notify_gui("🔍 Checking for updates...", "info")
                
                update_info = self.updater.check_for_updates()
                
                if update_info:
                    version = update_info.get("version")
                    self.notify_gui(f"🎉 New version available: {version}", "success")
                    
                    # Auto-download if enabled
                    if self.updater.config.get("auto_download", True):
                        self.download_update_async(update_info)
                else:
                    self.notify_gui("✅ You're running the latest version", "success")
                    
            except Exception as e:
                self.notify_gui(f"❌ Update check failed: {e}", "error")
            finally:
                self.checking = False
        
        self.update_thread = threading.Thread(target=check_thread, daemon=True)
        self.update_thread.start()
        return True
    
    def download_update_async(self, update_info):
        """Download update asynchronously"""
        if self.downloading:
            return False
        
        def download_thread():
            self.downloading = True
            try:
                version = update_info.get("version")
                self.notify_gui(f"⬇️ Downloading update {version}...", "info")
                
                download_path = self.updater.download_update(update_info)
                
                if download_path:
                    self.notify_gui(f"✅ Update {version} downloaded successfully", "success")
                    
                    # Auto-install if enabled
                    if self.updater.config.get("auto_install", False):
                        self.install_update_async(download_path, update_info)
                    else:
                        self.notify_gui("📦 Update ready for installation", "info")
                else:
                    self.notify_gui("❌ Download failed", "error")
                    
            except Exception as e:
                self.notify_gui(f"❌ Download failed: {e}", "error")
            finally:
                self.downloading = False
        
        threading.Thread(target=download_thread, daemon=True).start()
        return True
    
    def install_update_async(self, download_path, update_info):
        """Install update asynchronously"""
        if self.installing:
            return False
        
        def install_thread():
            self.installing = True
            try:
                version = update_info.get("version")
                self.notify_gui(f"🔧 Installing update {version}...", "info")
                
                success = self.updater.install_update(download_path, update_info)
                
                if success:
                    self.notify_gui(f"🎉 Update {version} installed successfully!", "success")
                    self.notify_gui("🔄 Restart required to complete update", "warning")
                else:
                    self.notify_gui("❌ Installation failed", "error")
                    
            except Exception as e:
                self.notify_gui(f"❌ Installation failed: {e}", "error")
            finally:
                self.installing = False
        
        threading.Thread(target=install_thread, daemon=True).start()
        return True
    
    def rollback_async(self):
        """Rollback update asynchronously"""
        def rollback_thread():
            try:
                self.notify_gui("🔄 Rolling back to previous version...", "info")
                
                success = self.updater.rollback_update()
                
                if success:
                    self.notify_gui("✅ Rollback completed successfully", "success")
                    self.notify_gui("🔄 Restart required to complete rollback", "warning")
                else:
                    self.notify_gui("❌ Rollback failed", "error")
                    
            except Exception as e:
                self.notify_gui(f"❌ Rollback failed: {e}", "error")
        
        threading.Thread(target=rollback_thread, daemon=True).start()
    
    def get_status(self):
        """Get update status"""
        status = self.updater.get_update_status()
        status.update({
            "checking": self.checking,
            "downloading": self.downloading,
            "installing": self.installing,
            "notifications_count": len(self.notifications)
        })
        return status
    
    def get_notifications(self, limit=10):
        """Get recent notifications"""
        return self.notifications[-limit:] if limit else self.notifications
    
    def clear_notifications(self):
        """Clear all notifications"""
        self.notifications.clear()
    
    def update_config(self, config_updates):
        """Update configuration"""
        try:
            for key, value in config_updates.items():
                if key in self.updater.config:
                    self.updater.config[key] = value
            
            self.updater.save_config()
            self.notify_gui("⚙️ Update settings saved", "success")
            return True
            
        except Exception as e:
            self.notify_gui(f"❌ Failed to save settings: {e}", "error")
            return False
    
    def start_auto_update_service(self):
        """Start automatic update service"""
        if self.updater.config.get("auto_check", True):
            def auto_service():
                while True:
                    try:
                        # Check every 6 hours by default
                        interval = self.updater.config.get("check_interval_hours", 6) * 3600
                        time.sleep(interval)
                        
                        if not self.checking:
                            self.check_updates_async()
                            
                    except Exception as e:
                        print(f"⚠️ Auto-update service error: {e}")
                        time.sleep(300)  # Wait 5 minutes on error
            
            service_thread = threading.Thread(target=auto_service, daemon=True)
            service_thread.start()
            
            self.notify_gui("🔄 Auto-update service started", "info")
    
    def force_update_check(self):
        """Force immediate update check"""
        return self.check_updates_async()
    
    def get_available_updates(self):
        """Get list of available updates"""
        try:
            update_info = self.updater.check_for_updates()
            return [update_info] if update_info else []
        except:
            return []
    
    def get_update_history(self):
        """Get update history from backups"""
        try:
            if not self.updater.backup_dir.exists():
                return []
            
            backups = list(self.updater.backup_dir.glob("aurumbotx_backup_*.zip"))
            history = []
            
            for backup in backups:
                # Parse backup filename
                parts = backup.stem.split('_')
                if len(parts) >= 4:
                    version = parts[2]
                    timestamp = parts[3] + '_' + parts[4]
                    
                    history.append({
                        "version": version,
                        "timestamp": timestamp,
                        "backup_file": backup.name,
                        "size": backup.stat().st_size
                    })
            
            # Sort by timestamp (newest first)
            history.sort(key=lambda x: x["timestamp"], reverse=True)
            return history
            
        except Exception as e:
            print(f"⚠️ Failed to get update history: {e}")
            return []

# Global update manager instance
update_manager = None

def get_update_manager(gui_callback=None):
    """Get global update manager instance"""
    global update_manager
    
    if update_manager is None:
        update_manager = UpdateManager(gui_callback)
    elif gui_callback:
        update_manager.set_gui_callback(gui_callback)
    
    return update_manager

def main():
    """Test update manager"""
    manager = UpdateManager()
    
    print("🔄 Testing Update Manager...")
    
    # Test status
    status = manager.get_status()
    print(f"📊 Status: {json.dumps(status, indent=2)}")
    
    # Test update check
    manager.check_updates_async()
    
    # Wait for completion
    time.sleep(5)
    
    # Show notifications
    notifications = manager.get_notifications()
    print(f"📢 Notifications: {len(notifications)}")
    for notif in notifications:
        print(f"  {notif['timestamp']}: {notif['message']}")

if __name__ == "__main__":
    main()

