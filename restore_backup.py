from utils.backup_manager import BackupManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    backup_mgr = BackupManager()
    
    # Get list of available backups
    backups = backup_mgr.list_backups()
    
    if not backups:
        logger.error("No backups found")
        return
    
    # Get most recent backup
    latest_backup = backups[0]  # backups are sorted in reverse order
    
    try:
        # Restore the trading configuration
        config = backup_mgr.load_trading_config(latest_backup['timestamp'], "solanabot_backup")
        logger.info(f"Successfully restored backup from {latest_backup['timestamp']}")
        logger.info(f"Restored configuration: {config}")
        return config
    except Exception as e:
        logger.error(f"Failed to restore backup: {str(e)}")
        return None

if __name__ == "__main__":
    main()
