"""
BackupManager module for handling trading configuration backups
"""
import json
import os
import logging
import shutil
from datetime import datetime
from pathlib import Path
import threading
import time

logger = logging.getLogger(__name__)

class BackupManager:
    def __init__(self, backup_interval=3600):  # Default 1 hour
        self.backup_dir = Path("backup")
        self.backup_interval = backup_interval
        self.backup_thread = None
        self.should_stop = False
        self._setup_backup_directory()

    def _setup_backup_directory(self):
        """Initialize backup directory structure"""
        self.backup_dir.mkdir(exist_ok=True)

    def _create_backup_folder(self):
        """Create a new timestamped backup folder"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / timestamp
        backup_path.mkdir(exist_ok=True)
        return backup_path

    def save_trading_config(self, config, strategy_name):
        """Save trading configuration to a backup file with JSONB compatibility"""
        try:
            backup_path = self._create_backup_folder()

            # Ensure config is JSON serializable
            config = self._prepare_config_for_backup(config)

            # Save configuration
            config_file = backup_path / f"{strategy_name}_config.json"
            with open(config_file, "w") as f:
                json.dump(config, f, indent=4, default=str)

            # Create backup log
            self._create_backup_log(backup_path, strategy_name, config)

            logger.info(f"Trading configuration backup created at {backup_path}")
            return str(backup_path)
        except Exception as e:
            logger.error(f"Error creating backup: {str(e)}")
            raise

    def _prepare_config_for_backup(self, config):
        """Prepare configuration for backup ensuring JSONB compatibility"""
        if isinstance(config, dict):
            return {
                k: self._prepare_config_for_backup(v)
                for k, v in config.items()
            }
        elif isinstance(config, (list, tuple)):
            return [self._prepare_config_for_backup(item) for item in config]
        elif isinstance(config, (int, float, str, bool)) or config is None:
            return config
        else:
            return str(config)

    def _create_backup_log(self, backup_path, strategy_name, config):
        """Create a detailed log of the backup"""
        log_file = backup_path / "BACKUP_LOG.md"
        timestamp = datetime.now().strftime("%d %B %Y %H:%M:%S")

        log_content = f"""# Backup Log - {timestamp}

## Strategy: {strategy_name}
- Timestamp: {timestamp}
- Configuration Version: {config.get('version', '1.0')}

## Configuration Details
- Risk Per Trade: {config.get('risk_per_trade', 'N/A')}
- Initial Balance: {config.get('initial_balance', 'N/A')}
- Trading Pair: {config.get('trading_pair', 'N/A')}

## Backup Status
- Location: {backup_path}
- Files:
  - {strategy_name}_config.json

## Notes
- Automatic backup created by Trading Bot Backup Manager
- JSONB compatible format
- Database indexes updated
"""

        with open(log_file, "w") as f:
            f.write(log_content)

    def list_backups(self):
        """List all available backups"""
        backups = []
        for backup_dir in sorted(self.backup_dir.iterdir(), reverse=True):
            if backup_dir.is_dir():
                log_file = backup_dir / "BACKUP_LOG.md"
                if log_file.exists():
                    backups.append({
                        'timestamp': backup_dir.name,
                        'path': str(backup_dir),
                        'log_file': str(log_file)
                    })
        return backups
        
    def load_trading_config(self, backup_timestamp, strategy_name):
        """Load trading configuration from a backup"""
        try:
            backup_path = self.backup_dir / backup_timestamp
            config_file = backup_path / f"{strategy_name}_config.json"
            
            if not config_file.exists():
                raise FileNotFoundError(f"Backup configuration not found: {config_file}")
                
            with open(config_file, "r") as f:
                config = json.load(f)
                
            logger.info(f"Trading configuration loaded from {backup_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading backup: {str(e)}")
            raise
            
    def start_auto_backup(self, config, strategy_name):
        """Start automatic backup thread"""
        if self.backup_thread and self.backup_thread.is_alive():
            logger.warning("Backup thread already running")
            return
            
        self.should_stop = False
        self.backup_thread = threading.Thread(
            target=self._auto_backup_worker,
            args=(config, strategy_name),
            daemon=True
        )
        self.backup_thread.start()
        logger.info("Automatic backup started")
        
    def stop_auto_backup(self):
        """Stop automatic backup thread"""
        self.should_stop = True
        if self.backup_thread:
            self.backup_thread.join()
        logger.info("Automatic backup stopped")
        
    def _auto_backup_worker(self, config, strategy_name):
        """Worker function for automatic backup"""
        while not self.should_stop:
            try:
                self.save_trading_config(config, strategy_name)
                time.sleep(self.backup_interval)
            except Exception as e:
                logger.error(f"Auto-backup error: {str(e)}")
                time.sleep(60)  # Wait a minute before retrying
                
    def cleanup_old_backups(self, max_backups=10):
        """Remove old backups keeping only the specified number of recent ones"""
        try:
            backups = self.list_backups()
            if len(backups) > max_backups:
                for backup in backups[max_backups:]:
                    shutil.rmtree(backup['path'])
                logger.info(f"Cleaned up old backups, keeping {max_backups} most recent")
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {str(e)}")